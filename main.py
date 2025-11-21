"""
DefectMaster Bot - Main entry point
Telegram bot for construction defect detection using AI
"""
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

import config
from bot.database.models import db
from bot.handlers import common, photo, tinkoff_payments, admin
from bot.services.admin_analytics_service import admin_analytics_service
from bot.services.backup_service import backup_service
from aiogram.types import FSInputFile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def on_startup():
    """Actions on bot startup"""
    logger.info("Initializing database...")
    await db.init_db()
    logger.info("Database initialized successfully")


async def auto_sync_dashboard():
    """Background task to sync admin dashboard every hour"""
    dashboard_id = os.getenv("ADMIN_DASHBOARD_ID")
    if not dashboard_id:
        logger.info("ADMIN_DASHBOARD_ID not set, auto-sync disabled")
        return

    logger.info("Admin dashboard auto-sync started (every 1 hour)")

    while True:
        await asyncio.sleep(3600)  # Wait 1 hour
        try:
            logger.info("Running scheduled admin dashboard sync...")
            await admin_analytics_service.sync_users_to_sheet(dashboard_id, db)
            await admin_analytics_service.sync_payments_to_sheet(dashboard_id, db)
            await admin_analytics_service.sync_analyses_to_sheet(dashboard_id, db)
            logger.info("Admin dashboard sync completed successfully")
        except Exception as e:
            logger.error(f"Error in auto-sync: {e}", exc_info=True)


async def auto_backup_to_drive():
    """Background task to backup database to Google Drive every hour"""
    logger.info("Database backup to Google Drive started (every 1 hour)")

    while True:
        await asyncio.sleep(3600)  # Wait 1 hour
        try:
            logger.info("Running scheduled database backup to Google Drive...")
            backup_url = backup_service.backup_to_drive()
            backup_service.cleanup_old_backups(keep_count=48)  # Keep 48 hours of backups
            logger.info(f"Database backup completed: {backup_url}")
        except Exception as e:
            logger.error(f"Error in database backup: {e}", exc_info=True)


async def auto_backup_to_admin(bot: Bot):
    """Background task to send database backup to admin chat every 24 hours"""
    if not config.ADMIN_IDS:
        logger.info("ADMIN_IDS not set, daily backup to admin disabled")
        return

    logger.info("Database backup to admin chat started (every 24 hours)")

    while True:
        await asyncio.sleep(86400)  # Wait 24 hours
        try:
            logger.info("Sending daily database backup to admins...")
            db_path = backup_service.get_db_file_path()
            stats = backup_service.get_db_stats()

            if not stats.get('exists'):
                logger.warning("Database file not found for backup")
                continue

            from datetime import datetime
            timestamp = datetime.now().strftime('%d.%m.%Y %H:%M')

            caption = (
                f"📦 **Ежедневный бэкап базы данных**\n\n"
                f"📅 Дата: {timestamp}\n"
                f"📊 Размер: {stats['size_kb']} KB\n"
                f"🕐 Изменен: {stats['modified']}"
            )

            for admin_id in config.ADMIN_IDS:
                try:
                    await bot.send_document(
                        chat_id=admin_id,
                        document=FSInputFile(db_path, filename=f"bot_db_backup_{datetime.now().strftime('%Y%m%d')}.db"),
                        caption=caption,
                        parse_mode="Markdown"
                    )
                    logger.info(f"Backup sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"Failed to send backup to admin {admin_id}: {e}")

        except Exception as e:
            logger.error(f"Error in daily backup to admin: {e}", exc_info=True)


async def main():
    """Main function to start the bot"""
    # Initialize bot
    bot = Bot(
        token=config.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )

    # Initialize dispatcher
    dp = Dispatcher()

    # Register routers
    dp.include_router(common.router)
    dp.include_router(photo.router)
    dp.include_router(tinkoff_payments.router)
    dp.include_router(admin.router)

    # Startup actions
    await on_startup()

    # Set bot commands
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start", description="Перезапуск / Инструкция"),
        BotCommand(command="new", description="Сменить объект (Контекст)"),
        BotCommand(command="balance", description="Кошелек и оплата"),
        BotCommand(command="table", description="Ссылка на мою таблицу"),
        BotCommand(command="help", description="Помощь"),
    ])

    logger.info("Bot started successfully!")
    logger.info("Press Ctrl+C to stop")

    # Start background tasks
    sync_task = asyncio.create_task(auto_sync_dashboard())
    backup_drive_task = asyncio.create_task(auto_backup_to_drive())
    backup_admin_task = asyncio.create_task(auto_backup_to_admin(bot))

    try:
        # Start polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        sync_task.cancel()
        backup_drive_task.cancel()
        backup_admin_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
