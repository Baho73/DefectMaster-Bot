"""
Migration script to add UUID column to existing spreadsheets
Run this once to update all user spreadsheets with UUID column
"""
import asyncio
import uuid
import logging
from bot.database.models import db
from bot.services.google_service import google_service
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_spreadsheet(spreadsheet_id: str, username: str):
    """Add UUID column to existing spreadsheet and populate UUIDs for existing rows"""
    try:
        logger.info(f"Migrating spreadsheet for user: {username} ({spreadsheet_id})")

        # Step 1: Insert new column A (UUID дефекта)
        requests = [{
            'insertDimension': {
                'range': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 1
                }
            }
        }]

        google_service.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

        logger.info(f"  ✓ Inserted UUID column for {username}")

        # Step 2: Update header in A1
        google_service.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Отчеты!A1',
            valueInputOption='RAW',
            body={'values': [['UUID дефекта']]}
        ).execute()

        logger.info(f"  ✓ Updated header for {username}")

        # Step 3: Get existing data (all rows except header)
        result = google_service.sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Отчеты!A2:K'  # Now we have 11 columns (A-K)
        ).execute()

        existing_rows = result.get('values', [])

        if not existing_rows:
            logger.info(f"  ℹ No existing data for {username}, skipping UUID generation")
            return

        # Step 4: Generate UUIDs for existing rows
        updates = []
        for row_index, row in enumerate(existing_rows, start=2):
            # Generate UUID for this defect
            defect_uuid = uuid.uuid4().hex

            # Update column A (UUID)
            updates.append({
                'range': f'Отчеты!A{row_index}',
                'values': [[defect_uuid]]
            })

        # Batch update UUIDs
        if updates:
            google_service.sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    'valueInputOption': 'RAW',
                    'data': updates
                }
            ).execute()

            logger.info(f"  ✓ Generated {len(updates)} UUIDs for {username}")

        logger.info(f"✓ Successfully migrated spreadsheet for {username}")

    except Exception as e:
        logger.error(f"✗ Error migrating spreadsheet for {username}: {e}", exc_info=True)


async def main():
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("Starting UUID migration for all user spreadsheets")
    logger.info("=" * 60)

    # Initialize database
    await db.init_db()

    # Get all users with spreadsheets
    async with db.get_connection() as conn:
        cursor = await conn.execute(
            "SELECT user_id, username, spreadsheet_id FROM users WHERE spreadsheet_id IS NOT NULL"
        )
        users = await cursor.fetchall()

    logger.info(f"Found {len(users)} users with spreadsheets")

    # Migrate each spreadsheet
    for user_id, username, spreadsheet_id in users:
        await migrate_spreadsheet(spreadsheet_id, username or f"user_{user_id}")

        # Small delay to avoid rate limits
        await asyncio.sleep(0.5)

    logger.info("=" * 60)
    logger.info(f"Migration complete! Migrated {len(users)} spreadsheets")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
