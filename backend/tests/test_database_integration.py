"""Optional real PostgreSQL checks, restricted to an explicitly named local test DB.

TEST_DATABASE_URL must use localhost/127.0.0.1 and a course_eval_test_* database.
No DATABASE_URL value or production database is used by this test module.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import urlparse
import uuid
import psycopg2
from backend import db_utils

TEST_URL = os.getenv('TEST_DATABASE_URL')


@unittest.skipUnless(TEST_URL, 'No disposable local PostgreSQL configured (TEST_DATABASE_URL).')
class DatabaseIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        target = urlparse(TEST_URL)
        if target.hostname not in ('localhost', '127.0.0.1', '::1') or not target.path.lstrip('/').startswith('course_eval_test_'):
            raise RuntimeError('Refusing to run integration tests outside an explicitly named local course_eval_test_* database.')
        cls.schema = 'overnight_' + uuid.uuid4().hex
        with psycopg2.connect(TEST_URL) as conn, conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA {cls.schema}')

        @contextmanager
        def connection():
            conn = psycopg2.connect(TEST_URL, options=f'-c search_path={cls.schema}')
            try:
                with conn:
                    yield conn
            finally:
                conn.close()
        cls.connection = staticmethod(connection)
        root = Path(__file__).resolve().parents[2]
        with connection() as conn, conn.cursor() as cur:
            cur.execute((root / 'db_schema.sql').read_text())
        # Reapply migrations to check safe repeatability as well as fresh setup.
        for _ in range(2):
            for migration in sorted((root / 'migrations').glob('*.sql')):
                with connection() as conn, conn.cursor() as cur:
                    cur.execute(migration.read_text())
        cls.patch = patch('backend.db_utils.get_db_connection', side_effect=connection)
        cls.patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        with psycopg2.connect(TEST_URL) as conn, conn.cursor() as cur:
            cur.execute(f'DROP SCHEMA {cls.schema} CASCADE')

    def test_concurrent_claim_reclaim_and_stale_writer(self):
        code = 'AS.180.101'
        with ThreadPoolExecutor(max_workers=8) as workers:
            claims = list(workers.map(lambda _: db_utils.claim_scrape_lock(code, 120), range(8)))
        claimed = [claim for claim in claims if claim is not None]
        self.assertEqual(len(claimed), 1)
        old = claimed[0]
        renewed = db_utils.renew_scrape_lock(code, old, 120)
        self.assertIsNotNone(renewed)
        self.assertFalse(db_utils.release_scrape_lock(code, old))
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute('UPDATE course_metadata SET scrape_lock_expires_at=%s WHERE course_code=%s', (datetime.now(timezone.utc) - timedelta(seconds=1), code))
        new = db_utils.claim_scrape_lock(code, 120)
        self.assertIsNotNone(new)
        self.assertIsNone(db_utils.renew_scrape_lock(code, renewed, 120))
        self.assertFalse(db_utils.update_course_data_owned('stale', code, {}, renewed))
        self.assertFalse(db_utils.update_course_metadata_owned(code, {}, renewed))
        self.assertFalse(db_utils.release_scrape_lock(code, renewed))
        self.assertTrue(db_utils.update_course_data_owned('AS.180.101.01.SP25', code, {'instructor_name': 'Jane Smith & J. Smith'}, new))
        self.assertTrue(db_utils.release_scrape_lock(code, new))

    def test_heartbeat_does_not_change_last_updated(self):
        code = 'AS.180.102'
        claim = db_utils.claim_scrape_lock(code, 120)
        before = db_utils.get_course_metadata(code)['updated_at']
        claim = db_utils.renew_scrape_lock(code, claim, 120)
        self.assertEqual(before, db_utils.get_course_metadata(code)['updated_at'])
        db_utils.release_scrape_lock(code, claim)

    def test_sql_instructor_membership_is_exact(self):
        code = 'AS.180.103'
        claim = db_utils.claim_scrape_lock(code, 120)
        db_utils.update_course_data_owned('AS.180.103.01.SP25', code, {'instructor_name': 'Smith, Jane; Dana Lee'}, claim)
        db_utils.release_scrape_lock(code, claim)
        self.assertEqual(len(db_utils.get_professor_records('Smith, Jane')), 1)
        self.assertEqual(len(db_utils.get_professor_records('Jane')), 0)
        self.assertEqual(db_utils.find_professors_by_name_db('Dana')['results'], [{'type': 'professor', 'name': 'Dana Lee'}])
