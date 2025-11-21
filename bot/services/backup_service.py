"""
Backup service for DefectMaster Bot
Handles automatic backups of bot.db to Google Drive and Telegram
"""
import os
import shutil
from datetime import datetime
from typing import Optional
import logging
from googleapiclient.http import MediaFileUpload

import config
from bot.services.google_service import google_service

logger = logging.getLogger(__name__)


class BackupService:
    """Service for database backups"""

    # Folder name for backups in Google Drive
    BACKUP_FOLDER_NAME = "DefectMaster_Backups"

    def __init__(self):
        self.backup_folder_id: Optional[str] = None

    def _get_or_create_backup_folder(self) -> str:
        """Get or create backup folder in Google Drive"""
        if self.backup_folder_id:
            return self.backup_folder_id

        drive_service = google_service.drive_service

        # Search for existing folder
        parent_id = config.GOOGLE_SHARED_DRIVE_ID or config.GOOGLE_DRIVE_FOLDER_ID

        query = f"name='{self.BACKUP_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        files = results.get('files', [])

        if files:
            self.backup_folder_id = files[0]['id']
            logger.info(f"Found existing backup folder: {self.backup_folder_id}")
            return self.backup_folder_id

        # Create new folder
        file_metadata = {
            'name': self.BACKUP_FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if config.GOOGLE_SHARED_DRIVE_ID:
            file_metadata['parents'] = [config.GOOGLE_SHARED_DRIVE_ID]
        elif config.GOOGLE_DRIVE_FOLDER_ID:
            file_metadata['parents'] = [config.GOOGLE_DRIVE_FOLDER_ID]

        folder = drive_service.files().create(
            body=file_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()

        self.backup_folder_id = folder['id']
        logger.info(f"Created backup folder: {self.backup_folder_id}")
        return self.backup_folder_id

    def backup_to_drive(self) -> str:
        """
        Backup bot.db to Google Drive

        Returns:
            URL to the backup file
        """
        db_path = config.DATABASE_PATH

        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")

        # Create timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"bot_db_backup_{timestamp}.db"

        # Get or create backup folder
        folder_id = self._get_or_create_backup_folder()

        # Upload file
        file_metadata = {
            'name': backup_filename,
            'parents': [folder_id]
        }

        media = MediaFileUpload(
            db_path,
            mimetype='application/x-sqlite3',
            resumable=True
        )

        file = google_service.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()

        file_id = file['id']
        file_url = f"https://drive.google.com/file/d/{file_id}/view"

        logger.info(f"Database backed up to Google Drive: {backup_filename}")
        return file_url

    def cleanup_old_backups(self, keep_count: int = 48):
        """
        Remove old backups, keeping only the most recent ones

        Args:
            keep_count: Number of backups to keep (default: 48 = 2 days of hourly backups)
        """
        try:
            folder_id = self._get_or_create_backup_folder()

            # List all backup files in folder
            results = google_service.drive_service.files().list(
                q=f"'{folder_id}' in parents and name contains 'bot_db_backup_' and trashed=false",
                spaces='drive',
                fields='files(id, name, createdTime)',
                orderBy='createdTime desc',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = results.get('files', [])

            # Delete old files (keep only keep_count most recent)
            if len(files) > keep_count:
                files_to_delete = files[keep_count:]
                for file in files_to_delete:
                    google_service.drive_service.files().delete(
                        fileId=file['id'],
                        supportsAllDrives=True
                    ).execute()
                    logger.info(f"Deleted old backup: {file['name']}")

                logger.info(f"Cleanup complete: deleted {len(files_to_delete)} old backups")
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")

    def get_db_file_path(self) -> str:
        """Get the path to database file for sending via Telegram"""
        return config.DATABASE_PATH

    def get_db_stats(self) -> dict:
        """Get database file statistics"""
        db_path = config.DATABASE_PATH

        if not os.path.exists(db_path):
            return {'exists': False}

        stat = os.stat(db_path)
        return {
            'exists': True,
            'size_bytes': stat.st_size,
            'size_kb': round(stat.st_size / 1024, 2),
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y %H:%M:%S')
        }


# Global backup service instance
backup_service = BackupService()
