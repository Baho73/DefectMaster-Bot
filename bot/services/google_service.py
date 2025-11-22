"""
Google Sheets and Drive service for DefectMaster Bot
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import config
from bot.database.models import db

logger = logging.getLogger(__name__)


class GoogleService:
    """Service for working with Google Sheets and Drive"""

    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self):
        self.credentials = service_account.Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=self.SCOPES
        )
        self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
        self.drive_service = build('drive', 'v3', credentials=self.credentials)

    def create_user_spreadsheet(self, username: str) -> Dict[str, str]:
        """
        Create a new spreadsheet for user

        Args:
            username: Telegram username

        Returns:
            Dict with spreadsheet_id and url
        """
        logger.info(f"Creating spreadsheet for user: {username}")
        spreadsheet_title = f"{config.SPREADSHEET_TEMPLATE_NAME}_{username}"

        # Create spreadsheet in Shared Drive or folder
        file_metadata = {
            'name': spreadsheet_title,
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }

        # Use Shared Drive if configured, otherwise use folder
        if config.GOOGLE_SHARED_DRIVE_ID:
            file_metadata['parents'] = [config.GOOGLE_SHARED_DRIVE_ID]
            file_metadata['driveId'] = config.GOOGLE_SHARED_DRIVE_ID
        elif config.GOOGLE_SHEETS_FOLDER_ID:
            file_metadata['parents'] = [config.GOOGLE_SHEETS_FOLDER_ID]

        # Create spreadsheet via Drive API with Shared Drive support
        file = self.drive_service.files().create(
            body=file_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()

        spreadsheet_id = file['id']

        # Rename default sheet to "Отчеты"
        self._rename_default_sheet(spreadsheet_id)

        # Format header row
        self._format_header(spreadsheet_id)

        # Insert headers
        self._insert_headers(spreadsheet_id)

        # Set permissions (anyone with link can view)
        self._set_permissions(spreadsheet_id)

        # Get spreadsheet URL
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

        logger.info(f"Spreadsheet created successfully for {username}: {spreadsheet_id}")
        return {
            'spreadsheet_id': spreadsheet_id,
            'url': spreadsheet_url
        }

    def _rename_default_sheet(self, spreadsheet_id: str):
        """Rename default sheet (Sheet1) to 'Отчеты'"""
        # Get spreadsheet info to find the default sheet ID
        spreadsheet = self.sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        # Get the first sheet ID
        sheet_id = spreadsheet['sheets'][0]['properties']['sheetId']

        # Rename the sheet
        requests = [{
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'title': 'Отчеты'
                },
                'fields': 'title'
            }
        }]

        body = {
            'requests': requests
        }

        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()

    def _insert_headers(self, spreadsheet_id: str):
        """Insert header row to spreadsheet"""
        values = [config.SHEET_HEADERS]

        body = {
            'values': values
        }

        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Отчеты!A1',
            valueInputOption='RAW',
            body=body
        ).execute()

    def _format_header(self, spreadsheet_id: str):
        """Format header row (bold, background color) and set default formatting for all cells"""
        requests = [
            # Format header row (row 1)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.9,
                                'green': 0.9,
                                'blue': 0.9
                            },
                            'textFormat': {
                                'bold': True,
                                'fontSize': 10
                            },
                            'wrapStrategy': 'WRAP'
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat,wrapStrategy)'
                }
            },
            # Format all data cells (row 2+) - no bold, font size 10, word wrap
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 1,
                        'endRowIndex': 1000  # Format first 1000 rows
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': False,
                                'fontSize': 10
                            },
                            'wrapStrategy': 'WRAP'
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,wrapStrategy)'
                }
            },
            {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': len(config.SHEET_HEADERS)
                    }
                }
            }
        ]

        body = {
            'requests': requests
        }

        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()

    def _set_permissions(self, spreadsheet_id: str):
        """Set spreadsheet permissions to 'anyone with link can view'"""
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }

        self.drive_service.permissions().create(
            fileId=spreadsheet_id,
            body=permission,
            supportsAllDrives=True
        ).execute()

    def upload_photo_to_drive(self, photo_bytes: bytes, filename: str) -> str:
        """
        Upload photo to Google Drive and get shareable link

        Args:
            photo_bytes: Photo binary data
            filename: Filename for the photo

        Returns:
            Direct link to the photo
        """
        file_metadata = {
            'name': filename,
            'mimeType': 'image/jpeg'
        }

        # Use Shared Drive if configured, otherwise use folder
        if config.GOOGLE_SHARED_DRIVE_ID:
            file_metadata['parents'] = [config.GOOGLE_SHARED_DRIVE_ID]
            file_metadata['driveId'] = config.GOOGLE_SHARED_DRIVE_ID
        elif config.GOOGLE_DRIVE_FOLDER_ID:
            file_metadata['parents'] = [config.GOOGLE_DRIVE_FOLDER_ID]

        media = MediaIoBaseUpload(
            io.BytesIO(photo_bytes),
            mimetype='image/jpeg',
            resumable=True
        )

        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()

        file_id = file['id']

        # Set permissions
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }

        self.drive_service.permissions().create(
            fileId=file_id,
            body=permission,
            supportsAllDrives=True
        ).execute()

        # Return direct link
        return f"https://drive.google.com/uc?id={file_id}"

    async def add_defect_row(self, spreadsheet_id: str, analysis: Dict[str, Any],
                            context: str, photo_url: str, user_id: int,
                            photo_id: str):
        """
        Add defect analysis results to spreadsheet and database

        Args:
            spreadsheet_id: Google Spreadsheet ID
            analysis: AI analysis results
            context: Object context
            photo_url: URL to photo on Google Drive
            user_id: Telegram user ID
            photo_id: Telegram photo ID
        """
        items = analysis.get('items', [])
        expert_summary = analysis.get('expert_summary', '')
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M')

        # Generate analysis UUID for this photo analysis
        analysis_uuid = uuid.uuid4().hex
        logger.info(f"Generated analysis UUID: {analysis_uuid}")

        # Save analysis to database
        await db.save_analysis(
            analysis_uuid=analysis_uuid,
            user_id=user_id,
            photo_id=photo_id,
            photo_url=photo_url,
            context=context or 'Не указан',
            defects_found=len(items),
            is_relevant=True  # If we got here, photo was relevant
        )

        # Prepare rows (one for each defect)
        rows = []
        for defect_index, item in enumerate(items, start=1):
            # Generate unique UUID for each defect
            defect_uuid = uuid.uuid4().hex

            criticality_text = {
                "Критический": "🔥 Критический",
                "Значительный": "⚠️ Значительный",
                "Малозначительный": "ℹ️ Малозначительный"
            }.get(item.get('criticality', ''), item.get('criticality', ''))

            row = [
                defect_uuid,  # UUID дефекта (первая колонка)
                timestamp,
                context or 'Не указан',
                item.get('defect', ''),
                item.get('location', ''),
                criticality_text,
                item.get('cause', ''),
                item.get('norm', ''),
                item.get('recommendation', ''),
                expert_summary,
                f'=HYPERLINK("{photo_url}", "Фото")'
            ]
            rows.append(row)

            logger.info(f"Generated UUID for defect {defect_index}: {defect_uuid}")

            # Save defect to database
            await db.save_defect(
                defect_uuid=defect_uuid,
                analysis_uuid=analysis_uuid,
                user_id=user_id,
                defect_index=defect_index,
                defect_name=item.get('defect', ''),
                location=item.get('location', ''),
                criticality=item.get('criticality', ''),
                cause=item.get('cause', ''),
                norm_violation=item.get('norm', ''),
                recommendation=item.get('recommendation', '')
            )

        # If no defects, add one summary row
        if not rows:
            no_defect_uuid = uuid.uuid4().hex
            rows.append([
                no_defect_uuid,  # UUID даже для "нет дефектов"
                timestamp,
                context or 'Не указан',
                'Дефекты не обнаружены',
                '',
                '',
                '',
                '',
                '',
                expert_summary,
                f'=HYPERLINK("{photo_url}", "Фото")'
            ])

            # Save "no defects" row to database as well
            await db.save_defect(
                defect_uuid=no_defect_uuid,
                analysis_uuid=analysis_uuid,
                user_id=user_id,
                defect_index=0,
                defect_name='Дефекты не обнаружены',
                location='',
                criticality='',
                cause='',
                norm_violation='',
                recommendation=''
            )

        body = {
            'values': rows
        }

        self.sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Отчеты!A2',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()

    def get_spreadsheet_url(self, spreadsheet_id: str) -> str:
        """Get spreadsheet URL by ID"""
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


# Global Google service instance
google_service = GoogleService()
