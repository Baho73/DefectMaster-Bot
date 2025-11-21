"""
Local photo storage service for DefectMaster Bot
"""
import os
import uuid
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PhotoStorageService:
    """Service for storing photos locally on server"""

    def __init__(self, storage_path: str, base_url: str):
        """
        Initialize photo storage service

        Args:
            storage_path: Path to directory for storing photos
            base_url: Base URL for accessing photos (e.g., https://teamplan.ru/photos)
        """
        self.storage_path = Path(storage_path)
        self.base_url = base_url.rstrip('/')

        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Photo storage initialized at {self.storage_path}")

    def save_photo(self, photo_bytes: bytes, user_id: int) -> Optional[str]:
        """
        Save photo to local storage with UUID filename

        Args:
            photo_bytes: Photo binary data
            user_id: User ID (for logging purposes)

        Returns:
            URL to access the photo, or None if failed
        """
        try:
            # Generate unique filename using UUID (impossible to guess)
            photo_uuid = uuid.uuid4().hex
            filename = f"{photo_uuid}.jpg"
            file_path = self.storage_path / filename

            # Save photo to disk
            with open(file_path, 'wb') as f:
                f.write(photo_bytes)

            # Generate public URL
            photo_url = f"{self.base_url}/{filename}"

            logger.info(f"Photo saved for user {user_id}. UUID: {photo_uuid}, Size: {len(photo_bytes)} bytes")

            return photo_url

        except Exception as e:
            logger.error(f"Failed to save photo for user {user_id}: {e}", exc_info=True)
            return None

    def delete_photo(self, photo_url: str) -> bool:
        """
        Delete photo from storage

        Args:
            photo_url: URL of the photo to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            # Extract filename from URL
            filename = photo_url.split('/')[-1]
            file_path = self.storage_path / filename

            if file_path.exists():
                file_path.unlink()
                logger.info(f"Photo deleted: {filename}")
                return True
            else:
                logger.warning(f"Photo not found: {filename}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete photo {photo_url}: {e}", exc_info=True)
            return False

    def get_storage_size(self) -> int:
        """
        Get total size of stored photos in bytes

        Returns:
            Total size in bytes
        """
        try:
            total_size = sum(f.stat().st_size for f in self.storage_path.glob('*.jpg'))
            return total_size
        except Exception as e:
            logger.error(f"Failed to calculate storage size: {e}", exc_info=True)
            return 0

    def get_photo_count(self) -> int:
        """
        Get total number of stored photos

        Returns:
            Number of photos
        """
        try:
            return len(list(self.storage_path.glob('*.jpg')))
        except Exception as e:
            logger.error(f"Failed to count photos: {e}", exc_info=True)
            return 0


# Global photo storage service instance
# Will be initialized in config with proper paths
photo_storage_service = None
