from datetime import datetime, timedelta, timezone
from threading import Lock
import unittest
from unittest.mock import patch
from backend.scrape_lock import CourseScrapeLease, ScrapeOwnershipLost
from backend.workflow_helpers import scrape_course_data_core


class MemoryLeases:
    """Atomic fake for lifecycle tests; SQL integration is a separate test suite."""
    def __init__(self):
        self.expiry = None
        self.mutex = Lock()

    def claim(self, code, ttl):
        with self.mutex:
            if self.expiry and self.expiry > datetime.now(timezone.utc):
                return None
            self.expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl)
            return self.expiry

    def renew(self, code, expiry, ttl):
        with self.mutex:
            if expiry != self.expiry:
                return None
            self.expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl)
            return self.expiry

    def release(self, code, expiry):
        with self.mutex:
            if self.expiry == expiry:
                self.expiry = None
                return True
            return False


class ScrapeLockTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryLeases()
        for name in ('claim', 'renew', 'release'):
            mock = patch('backend.scrape_lock.db_utils.' + name + '_scrape_lock', side_effect=getattr(self.store, name))
            mock.start()
            self.addCleanup(mock.stop)

    def test_duplicate_request_does_not_run_core_and_lock_is_released(self):
        with CourseScrapeLease('AS.180.101'):
            with patch('backend.workflow_helpers._scrape_course_data_owned') as core:
                result = scrape_course_data_core('AS.180.101')
                self.assertTrue(result['in_progress'])
                core.assert_not_called()
        self.assertIsNone(self.store.expiry)

    def test_renewal_retains_exact_database_expiry_and_releases_new_claim(self):
        with CourseScrapeLease('AS.180.101') as lease:
            first = lease.expires_at
            lease.renew()
            self.assertNotEqual(first, lease.expires_at)
            self.assertEqual(lease.expires_at, self.store.expiry)
        self.assertIsNone(self.store.expiry)

    def test_lost_owner_cannot_publish_or_clear_reclaimed_lock(self):
        with CourseScrapeLease('AS.180.101') as lease:
            reclaimed = datetime.now(timezone.utc) + timedelta(seconds=600)
            self.store.expiry = reclaimed
            with self.assertRaises(ScrapeOwnershipLost):
                lease.renew()
            with patch('backend.scrape_lock.db_utils.update_course_data_owned') as publish:
                with self.assertRaises(ScrapeOwnershipLost):
                    lease.publish('key', {})
                publish.assert_not_called()
        self.assertEqual(self.store.expiry, reclaimed)

    def test_database_rejecting_publish_marks_ownership_lost(self):
        with CourseScrapeLease('AS.180.101') as lease:
            with patch('backend.scrape_lock.db_utils.update_course_data_owned', return_value=False):
                with self.assertRaises(ScrapeOwnershipLost):
                    lease.publish('key', {})
            self.assertFalse(lease.acquired)

    def test_failure_releases_lease(self):
        with self.assertRaises(RuntimeError):
            with CourseScrapeLease('AS.180.101'):
                raise RuntimeError('network failed')
        self.assertIsNone(self.store.expiry)


if __name__ == '__main__':
    unittest.main()
