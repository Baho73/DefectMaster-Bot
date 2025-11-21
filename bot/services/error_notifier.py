"""
Error notification service for DefectMaster Bot
Sends error reports to admin chat
"""
import logging
import traceback
from datetime import datetime
from typing import Optional
from aiogram import Bot

import config

logger = logging.getLogger(__name__)

# Global bot instance (set in main.py)
_bot: Optional[Bot] = None


def set_bot(bot: Bot):
    """Set bot instance for error notifications"""
    global _bot
    _bot = bot


async def notify_admins_error(
    error: Exception,
    context: str = "",
    user_id: Optional[int] = None,
    username: Optional[str] = None
):
    """
    Send error notification to all admins

    Args:
        error: The exception that occurred
        context: Description of what was happening when error occurred
        user_id: Optional user ID related to the error
        username: Optional username related to the error
    """
    global _bot

    if not _bot:
        logger.warning("Bot not set for error notifier, skipping notification")
        return

    if not config.ADMIN_IDS:
        logger.warning("No admin IDs configured, skipping error notification")
        return

    try:
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        error_type = type(error).__name__
        error_msg = str(error)

        # Get short traceback (last 3 frames)
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        tb_short = ''.join(tb_lines[-5:]) if len(tb_lines) > 5 else ''.join(tb_lines)

        # Truncate if too long
        if len(tb_short) > 1500:
            tb_short = tb_short[:1500] + "..."

        # Build message
        user_info = ""
        if user_id:
            user_info = f"\n👤 User: {user_id}"
            if username:
                user_info += f" (@{username})"

        message = (
            f"🚨 <b>Ошибка в боте</b>\n\n"
            f"📅 {timestamp}\n"
            f"❌ <b>{error_type}</b>: {error_msg[:200]}{user_info}\n"
            f"📍 {context}\n\n"
            f"<pre>{tb_short}</pre>"
        )

        # Send to all admins
        for admin_id in config.ADMIN_IDS:
            try:
                await _bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to send error notification to admin {admin_id}: {e}")

        logger.info(f"Error notification sent to {len(config.ADMIN_IDS)} admins")

    except Exception as e:
        logger.error(f"Failed to send error notification: {e}")


async def notify_admins_message(message: str, title: str = "Уведомление"):
    """
    Send a simple message to all admins

    Args:
        message: Message text
        title: Message title
    """
    global _bot

    if not _bot or not config.ADMIN_IDS:
        return

    try:
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

        text = (
            f"ℹ️ <b>{title}</b>\n\n"
            f"📅 {timestamp}\n\n"
            f"{message}"
        )

        for admin_id in config.ADMIN_IDS:
            try:
                await _bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to send notification to admin {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
