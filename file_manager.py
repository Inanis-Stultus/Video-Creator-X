import os
import glob
from datetime import datetime, timedelta
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class FileManager:
    _instance = None
    _lock = Lock()

    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.tracked_files = {}
        self.processing_progress = 0
        self.file_expiry = timedelta(hours=24)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(os.path.join(os.getcwd(), 'uploads'))
        return cls._instance

    def track_file(self, filepath):
        """Track a new file with creation timestamp."""
        self.tracked_files[filepath] = {
            'created_at': datetime.now(),
            'expires_at': datetime.now() + self.file_expiry
        }
        logger.debug(f"Tracking new file: {filepath}")

    def is_tracked(self, filepath):
        """Check if a file is being tracked and not expired."""
        if filepath not in self.tracked_files:
            return False
        
        file_info = self.tracked_files[filepath]
        return datetime.now() < file_info['expires_at']

    def cleanup_expired_files(self):
        """Remove expired files and their tracking information."""
        current_time = datetime.now()
        expired_files = []

        for filepath, info in self.tracked_files.items():
            if current_time >= info['expires_at']:
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        logger.debug(f"Removed expired file: {filepath}")
                except Exception as e:
                    logger.error(f"Failed to remove expired file {filepath}: {str(e)}")
                expired_files.append(filepath)

        # Remove expired files from tracking
        for filepath in expired_files:
            del self.tracked_files[filepath]

    def update_progress(self, progress):
        """Update the processing progress."""
        with self._lock:
            self.processing_progress = min(100, max(0, progress))

    def get_processing_progress(self):
        """Get the current processing progress."""
        with self._lock:
            return self.processing_progress
