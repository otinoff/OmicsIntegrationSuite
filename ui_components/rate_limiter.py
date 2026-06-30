"""
Rate Limiter for OmicsIntegrationSuite
Модуль ограничения частоты запросов для защиты от DoS

Implements session-based rate limiting for file uploads and processing
"""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List


class SessionRateLimiter:
    """
    Session-based rate limiter

    Tracks:
    - File uploads per time window
    - Processing jobs per user

    Features:
    - Time-window based limits (e.g., 10 uploads/minute)
    - Concurrent processing limits (e.g., 5 active jobs)
    - Automatic cleanup of old records
    """

    def __init__(self, upload_limit=10, upload_window_seconds=60, max_concurrent_jobs=5):
        """
        Initialize rate limiter

        Args:
            upload_limit (int): Max uploads per time window
            upload_window_seconds (int): Time window in seconds
            max_concurrent_jobs (int): Max concurrent processing jobs
        """
        self.upload_limit = upload_limit
        self.upload_window = timedelta(seconds=upload_window_seconds)
        self.max_concurrent_jobs = max_concurrent_jobs

        # Track upload timestamps by session
        self.upload_history: Dict[str, List[datetime]] = defaultdict(list)

        # Track active processing jobs by session
        self.active_jobs: Dict[str, int] = defaultdict(int)

    def check_upload_allowed(self, session_id: str) -> tuple:
        """
        Check if upload is allowed for session

        Args:
            session_id (str): Session identifier

        Returns:
            tuple: (is_allowed, error_message, uploads_remaining)
        """
        # Clean old uploads outside time window
        self._cleanup_old_uploads(session_id)

        # Check current upload count
        current_uploads = len(self.upload_history[session_id])

        if current_uploads >= self.upload_limit:
            wait_time = self._time_until_next_slot(session_id)
            return False, f"Upload limit exceeded. Wait {wait_time:.0f} seconds.", 0

        remaining = self.upload_limit - current_uploads
        return True, "", remaining

    def record_upload(self, session_id: str):
        """
        Record an upload for session

        Args:
            session_id (str): Session identifier
        """
        self.upload_history[session_id].append(datetime.now())

    def check_processing_allowed(self, session_id: str) -> tuple:
        """
        Check if processing job can be started

        Args:
            session_id (str): Session identifier

        Returns:
            tuple: (is_allowed, error_message, slots_remaining)
        """
        current_jobs = self.active_jobs[session_id]

        if current_jobs >= self.max_concurrent_jobs:
            return False, f"Max concurrent jobs ({self.max_concurrent_jobs}) reached. Wait for completion.", 0

        remaining = self.max_concurrent_jobs - current_jobs
        return True, "", remaining

    def start_processing(self, session_id: str):
        """
        Start a processing job for session

        Args:
            session_id (str): Session identifier
        """
        self.active_jobs[session_id] += 1

    def finish_processing(self, session_id: str):
        """
        Finish a processing job for session

        Args:
            session_id (str): Session identifier
        """
        if self.active_jobs[session_id] > 0:
            self.active_jobs[session_id] -= 1

    def get_stats(self, session_id: str) -> dict:
        """
        Get current rate limit stats for session

        Args:
            session_id (str): Session identifier

        Returns:
            dict: Statistics
        """
        self._cleanup_old_uploads(session_id)

        return {
            'uploads_in_window': len(self.upload_history[session_id]),
            'upload_limit': self.upload_limit,
            'active_jobs': self.active_jobs[session_id],
            'max_jobs': self.max_concurrent_jobs,
            'window_seconds': self.upload_window.total_seconds(),
        }

    def reset_session(self, session_id: str):
        """
        Reset limits for session (for testing)

        Args:
            session_id (str): Session identifier
        """
        if session_id in self.upload_history:
            del self.upload_history[session_id]
        if session_id in self.active_jobs:
            del self.active_jobs[session_id]

    def _cleanup_old_uploads(self, session_id: str):
        """Remove uploads older than time window"""
        cutoff_time = datetime.now() - self.upload_window
        self.upload_history[session_id] = [
            timestamp for timestamp in self.upload_history[session_id]
            if timestamp > cutoff_time
        ]

    def _time_until_next_slot(self, session_id: str) -> float:
        """Calculate seconds until next upload slot available"""
        if not self.upload_history[session_id]:
            return 0.0

        oldest_upload = min(self.upload_history[session_id])
        next_slot_time = oldest_upload + self.upload_window
        wait_time = (next_slot_time - datetime.now()).total_seconds()

        return max(0.0, wait_time)
