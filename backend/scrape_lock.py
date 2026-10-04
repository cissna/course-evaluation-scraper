"""Request-scoped renewable database lease, shared by every scraper entry point."""
from threading import Event, RLock, Thread
from . import db_utils


class ScrapeOwnershipLost(RuntimeError):
    pass


class CourseScrapeLease:
    def __init__(self, course_code, ttl_seconds=120, heartbeat_seconds=30):
        self.course_code = course_code
        self.ttl_seconds = ttl_seconds
        self.heartbeat_seconds = heartbeat_seconds
        self.expires_at = None
        self._mutex = RLock()
        self._stop = Event()
        self._thread = None
        self._lost = False

    def __enter__(self):
        self.expires_at = db_utils.claim_scrape_lock(self.course_code, self.ttl_seconds)
        if self.expires_at is not None:
            self._thread = Thread(target=self._heartbeat, daemon=True)
            self._thread.start()
        return self

    @property
    def acquired(self):
        return self.expires_at is not None and not self._lost

    def ensure_owned(self):
        if not self.acquired:
            raise ScrapeOwnershipLost('This request no longer owns the course scrape lock.')

    def renew(self):
        with self._mutex:
            self.ensure_owned()
            expiry = db_utils.renew_scrape_lock(self.course_code, self.expires_at, self.ttl_seconds)
            if expiry is None:
                self._lost = True
                raise ScrapeOwnershipLost('The course scrape lock expired or was reclaimed.')
            # Preserve exactly what PostgreSQL returned, including microseconds.
            self.expires_at = expiry

    def _heartbeat(self):
        while not self._stop.wait(self.heartbeat_seconds):
            try:
                self.renew()
            except Exception:
                # A failed renewal is a loss of ownership, never permission to write.
                self._lost = True
                return

    def update_metadata(self, metadata):
        with self._mutex:
            self.ensure_owned()
            if not db_utils.update_course_metadata_owned(self.course_code, metadata, self.expires_at):
                self._lost = True
                raise ScrapeOwnershipLost('Course metadata was not published because ownership was lost.')

    def publish(self, instance_key, data):
        with self._mutex:
            self.ensure_owned()
            if not db_utils.update_course_data_owned(instance_key, self.course_code, data, self.expires_at):
                self._lost = True
                raise ScrapeOwnershipLost('Evaluation was not published because ownership was lost.')

    def __exit__(self, exc_type, exc, traceback):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        with self._mutex:
            if self.expires_at is not None:
                db_utils.release_scrape_lock(self.course_code, self.expires_at)
