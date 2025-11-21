"""
Admin Analytics Service - Google Sheets dashboard for admin
Модуль для создания и обновления админской аналитической таблицы
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
from typing import Dict, Any, List, Optional
import config
import logging

logger = logging.getLogger(__name__)


class AdminAnalyticsService:
    """Service for admin analytics in Google Sheets"""

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

    def create_admin_dashboard(self) -> Dict[str, str]:
        """
        Create admin analytics dashboard in Google Sheets

        Returns:
            Dict with spreadsheet_id and url
        """
        spreadsheet_title = "СтройКонтроль_Админ_Аналитика"

        # Create spreadsheet
        file_metadata = {
            'name': spreadsheet_title,
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }

        # Use Shared Drive if configured
        if config.GOOGLE_SHARED_DRIVE_ID:
            file_metadata['parents'] = [config.GOOGLE_SHARED_DRIVE_ID]
            file_metadata['driveId'] = config.GOOGLE_SHARED_DRIVE_ID

        # Create via Drive API
        file = self.drive_service.files().create(
            body=file_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()

        spreadsheet_id = file['id']

        # Create sheets structure
        self._create_sheets_structure(spreadsheet_id)

        # Set permissions (only admin can edit, anyone with link can view)
        self._set_permissions(spreadsheet_id)

        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

        logger.info(f"Admin dashboard created: {spreadsheet_url}")

        return {
            'spreadsheet_id': spreadsheet_id,
            'url': spreadsheet_url
        }

    def _create_sheets_structure(self, spreadsheet_id: str):
        """Create sheets structure with multiple tabs"""

        # Get current sheets
        spreadsheet = self.sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        default_sheet_id = spreadsheet['sheets'][0]['properties']['sheetId']

        requests = [
            # Rename first sheet to "Дашборд"
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': default_sheet_id,
                        'title': 'Дашборд'
                    },
                    'fields': 'title'
                }
            },
            # Add "Пользователи" sheet
            {
                'addSheet': {
                    'properties': {
                        'title': 'Пользователи',
                        'gridProperties': {
                            'frozenRowCount': 1
                        }
                    }
                }
            },
            # Add "Платежи" sheet
            {
                'addSheet': {
                    'properties': {
                        'title': 'Платежи',
                        'gridProperties': {
                            'frozenRowCount': 1
                        }
                    }
                }
            },
            # Add "Анализы" sheet
            {
                'addSheet': {
                    'properties': {
                        'title': 'Анализы',
                        'gridProperties': {
                            'frozenRowCount': 1
                        }
                    }
                }
            }
        ]

        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

        # Initialize headers for each sheet
        self._init_users_sheet(spreadsheet_id)
        self._init_payments_sheet(spreadsheet_id)
        self._init_analyses_sheet(spreadsheet_id)
        self._init_dashboard_sheet(spreadsheet_id)

        logger.info(f"Admin dashboard structure created for {spreadsheet_id}")

    def _init_users_sheet(self, spreadsheet_id: str):
        """Initialize Users sheet with headers"""
        headers = [
            "User ID",
            "Username",
            "Баланс",
            "Всего заплатил",
            "Всего анализов",
            "Релевантных анализов",
            "Найдено дефектов",
            "Таблица",
            "Пригласил (ID)",
            "Пригласил (Username)",
            "Дата регистрации"
        ]

        self._write_headers(spreadsheet_id, 'Пользователи', headers)

    def _init_payments_sheet(self, spreadsheet_id: str):
        """Initialize Payments sheet with headers"""
        headers = [
            "Дата",
            "User ID",
            "Username",
            "Order ID",
            "Сумма (₽)",
            "Кредиты",
            "Статус"
        ]

        self._write_headers(spreadsheet_id, 'Платежи', headers)

    def _init_analyses_sheet(self, spreadsheet_id: str):
        """Initialize Analyses sheet with headers"""
        headers = [
            "Дата",
            "User ID",
            "Username",
            "Контекст",
            "Дефектов найдено",
            "Релевантно"
        ]

        self._write_headers(spreadsheet_id, 'Анализы', headers)

    def _init_dashboard_sheet(self, spreadsheet_id: str):
        """Initialize Dashboard sheet with statistics"""
        data = [
            ["📊 СтройКонтроль - Админская панель"],
            [""],
            ["Метрика", "Значение"],
            ["👥 Всего пользователей", '=COUNTA(Пользователи!A2:A)'],
            ["💰 Платящих пользователей", '=COUNTIF(Пользователи!D2:D,">0")'],
            ["💳 Общая выручка", '=SUM(Пользователи!D2:D)&" ₽"'],
            ["📸 Всего анализов", '=SUM(Пользователи!E2:E)'],
            ["✅ Релевантных анализов", '=SUM(Пользователи!F2:F)'],
            ["🚨 Найдено дефектов", '=SUM(Пользователи!G2:G)'],
            [""],
            ["📈 Платежи"],
            ["Всего платежей", '=COUNTA(Платежи!A2:A)'],
            ["Успешных платежей", '=COUNTIF(Платежи!G2:G,"completed")'],
            ["Сумма платежей", '=SUMIF(Платежи!G2:G,"completed",Платежи!E2:E)&" ₽"'],
            ["Средний чек", '=AVERAGEIF(Платежи!G2:G,"completed",Платежи!E2:E)&" ₽"'],
            [""],
            ["🔥 Конверсия"],
            ["Конверсия в оплату", '=IF(COUNTA(Пользователи!A2:A)>0,TEXT(COUNTIF(Пользователи!D2:D,">0")/COUNTA(Пользователи!A2:A),"0.0%"),"0%")'],
            [""],
            ["🤖 Система"],
            ["Версия бота", f"v{config.BOT_VERSION}"],
            ["Последнее обновление", datetime.now().strftime('%d.%m.%Y %H:%M')]
        ]

        body = {'values': data}

        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Дашборд!A1',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        # Format dashboard
        self._format_dashboard(spreadsheet_id)

    def _write_headers(self, spreadsheet_id: str, sheet_name: str, headers: List[str]):
        """Write headers to a sheet"""
        body = {'values': [headers]}

        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A1',
            valueInputOption='RAW',
            body=body
        ).execute()

        # Format headers
        self._format_headers(spreadsheet_id, sheet_name, len(headers))

    def _format_headers(self, spreadsheet_id: str, sheet_name: str, num_columns: int):
        """Format header row (bold, background)"""
        # Get sheet ID by name
        spreadsheet = self.sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        sheet_id = None
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == sheet_name:
                sheet_id = sheet['properties']['sheetId']
                break

        if sheet_id is None:
            return

        requests = [{
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.4,
                            'green': 0.49,
                            'blue': 0.92
                        },
                        'textFormat': {
                            'bold': True,
                            'fontSize': 10,
                            'foregroundColor': {
                                'red': 1.0,
                                'green': 1.0,
                                'blue': 1.0
                            }
                        },
                        'wrapStrategy': 'WRAP'
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,wrapStrategy)'
            }
        }]

        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

    def _format_dashboard(self, spreadsheet_id: str):
        """Format dashboard sheet"""
        # Get sheet ID
        spreadsheet = self.sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        sheet_id = None
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == 'Дашборд':
                sheet_id = sheet['properties']['sheetId']
                break

        if sheet_id is None:
            return

        requests = [
            # Format title (row 1)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True,
                                'fontSize': 14
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.textFormat'
                }
            },
            # Merge title cell
            {
                'mergeCells': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 2
                    },
                    'mergeType': 'MERGE_ALL'
                }
            }
        ]

        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

    def _set_permissions(self, spreadsheet_id: str):
        """Set spreadsheet permissions"""
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }

        self.drive_service.permissions().create(
            fileId=spreadsheet_id,
            body=permission,
            supportsAllDrives=True
        ).execute()

    async def sync_users_to_sheet(self, spreadsheet_id: str, db):
        """
        Sync all users from database to Google Sheets

        Args:
            spreadsheet_id: Admin dashboard spreadsheet ID
            db: Database instance
        """
        logger.info("Syncing users to admin dashboard...")

        # Get all users with statistics
        async with db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT
                    u.user_id,
                    u.username,
                    u.balance,
                    COALESCE(SUM(CASE WHEN p.status = 'completed' THEN p.amount ELSE 0 END), 0) as total_paid,
                    COALESCE(COUNT(DISTINCT a.id), 0) as total_analyses,
                    COALESCE(SUM(CASE WHEN a.is_relevant = 1 THEN 1 ELSE 0 END), 0) as relevant_analyses,
                    COALESCE(SUM(CASE WHEN a.is_relevant = 1 THEN a.defects_found ELSE 0 END), 0) as total_defects,
                    u.spreadsheet_id,
                    u.referred_by,
                    ref.username as referrer_username,
                    u.created_at
                FROM users u
                LEFT JOIN payments p ON u.user_id = p.user_id
                LEFT JOIN analysis_history a ON u.user_id = a.user_id
                LEFT JOIN users ref ON u.referred_by = ref.user_id
                GROUP BY u.user_id
                ORDER BY u.created_at DESC
            """)

            users = await cursor.fetchall()

        # Prepare data rows
        rows = []
        for user in users:
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{user[7]}" if user[7] else ""

            row = [
                user[0],  # User ID
                user[1] or f"user_{user[0]}",  # Username
                user[2],  # Balance
                user[3],  # Total paid
                user[4],  # Total analyses
                user[5],  # Relevant analyses
                user[6],  # Total defects
                spreadsheet_url,  # Spreadsheet URL
                user[8] or "",  # Referred by (ID)
                user[9] or "",  # Referrer username
                user[10]   # Created at
            ]
            rows.append(row)

        # Clear existing data (except header)
        self.sheets_service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range='Пользователи!A2:Z'
        ).execute()

        # Write new data
        if rows:
            body = {'values': rows}
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Пользователи!A2',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

        logger.info(f"Synced {len(rows)} users to admin dashboard")

    async def sync_payments_to_sheet(self, spreadsheet_id: str, db):
        """
        Sync payment history to Google Sheets

        Args:
            spreadsheet_id: Admin dashboard spreadsheet ID
            db: Database instance
        """
        logger.info("Syncing payments to admin dashboard...")

        async with db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT
                    p.created_at,
                    p.user_id,
                    u.username,
                    p.order_id,
                    p.amount,
                    p.credits,
                    p.status
                FROM payments p
                LEFT JOIN users u ON p.user_id = u.user_id
                ORDER BY p.created_at DESC
                LIMIT 1000
            """)

            payments = await cursor.fetchall()

        # Prepare data rows
        rows = []
        for payment in payments:
            row = [
                payment[0],  # Created at
                payment[1],  # User ID
                payment[2] or f"user_{payment[1]}",  # Username
                payment[3],  # Order ID
                payment[4],  # Amount
                payment[5],  # Credits
                payment[6]   # Status
            ]
            rows.append(row)

        # Clear existing data
        self.sheets_service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range='Платежи!A2:Z'
        ).execute()

        # Write new data
        if rows:
            body = {'values': rows}
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Платежи!A2',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

        logger.info(f"Synced {len(rows)} payments to admin dashboard")

    async def sync_analyses_to_sheet(self, spreadsheet_id: str, db):
        """
        Sync analysis history to Google Sheets

        Args:
            spreadsheet_id: Admin dashboard spreadsheet ID
            db: Database instance
        """
        logger.info("Syncing analyses to admin dashboard...")

        async with db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT
                    a.created_at,
                    a.user_id,
                    u.username,
                    a.context_object,
                    a.defects_found,
                    a.is_relevant
                FROM analysis_history a
                LEFT JOIN users u ON a.user_id = u.user_id
                ORDER BY a.created_at DESC
                LIMIT 1000
            """)

            analyses = await cursor.fetchall()

        # Prepare data rows
        rows = []
        for analysis in analyses:
            row = [
                analysis[0],  # Created at
                analysis[1],  # User ID
                analysis[2] or f"user_{analysis[1]}",  # Username
                analysis[3] or "Не указан",  # Context
                analysis[4],  # Defects found
                "✅" if analysis[5] else "❌"  # Is relevant
            ]
            rows.append(row)

        # Clear existing data
        self.sheets_service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range='Анализы!A2:Z'
        ).execute()

        # Write new data
        if rows:
            body = {'values': rows}
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Анализы!A2',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

        logger.info(f"Synced {len(rows)} analyses to admin dashboard")


# Global instance
admin_analytics_service = AdminAnalyticsService()
