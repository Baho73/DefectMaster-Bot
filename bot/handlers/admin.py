"""
Admin command handlers for DefectMaster Bot
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from bot.database.models import db
from bot.services.admin_analytics_service import admin_analytics_service
from bot.services.backup_service import backup_service
import config
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)
router = Router()

# Store admin dashboard ID (will be saved to .env after creation)
ADMIN_DASHBOARD_ID = os.getenv("ADMIN_DASHBOARD_ID")


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in config.ADMIN_IDS


@router.message(Command("admin_addbalance"))
async def cmd_admin_addbalance(message: Message):
    """Add balance to user (admin only)"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("⛔ Эта команда доступна только администраторам")
        return

    # Parse command: /admin_addbalance <user_id> <amount>
    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer(
                "📝 <b>Использование:</b>\n"
                "<code>/admin_addbalance &lt;user_id&gt; &lt;количество&gt;</code>\n\n"
                "<b>Пример:</b>\n"
                "<code>/admin_addbalance 123456789 10</code>",
                parse_mode="HTML"
            )
            return

        target_user_id = int(parts[1])
        amount = int(parts[2])

        if amount <= 0:
            await message.answer("⚠️ Количество должно быть положительным числом")
            return

        # Check if user exists
        user = await db.get_user(target_user_id)
        if not user:
            await message.answer(f"⚠️ Пользователь с ID {target_user_id} не найден в базе")
            return

        # Update balance
        await db.update_balance(target_user_id, amount)

        # Get updated balance
        updated_user = await db.get_user(target_user_id)
        new_balance = updated_user['balance']

        logger.info(f"Admin {user_id} added {amount} credits to user {target_user_id}. New balance: {new_balance}")

        await message.answer(
            f"✅ <b>Баланс пополнен!</b>\n\n"
            f"👤 User ID: <code>{target_user_id}</code>\n"
            f"➕ Добавлено: {amount} фото\n"
            f"💳 Новый баланс: {new_balance} фото",
            parse_mode="HTML"
        )

    except ValueError:
        await message.answer("⚠️ Неверный формат. User ID и количество должны быть числами")
    except Exception as e:
        logger.error(f"Error in admin_addbalance: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка: {e}")


@router.message(Command("admin_user"))
async def cmd_admin_user(message: Message):
    """Get user info (admin only)"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("⛔ Эта команда доступна только администраторам")
        return

    # Parse command: /admin_user <user_id>
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer(
                "📝 **Использование:**\n"
                "`/admin_user <user_id>`\n\n"
                "**Пример:**\n"
                "`/admin_user 123456789`",
                parse_mode="Markdown"
            )
            return

        target_user_id = int(parts[1])

        # Get user
        user = await db.get_user(target_user_id)
        if not user:
            await message.answer(f"⚠️ Пользователь с ID {target_user_id} не найден в базе")
            return

        # Format user info
        context = user['context_object'] or "Не установлен"
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{user['spreadsheet_id']}" if user['spreadsheet_id'] else "Не создана"

        await message.answer(
            f"👤 <b>Информация о пользователе</b>\n\n"
            f"🆔 User ID: <code>{user['user_id']}</code>\n"
            f"👨‍💼 Username: @{user['username']}\n"
            f"💳 Баланс: {user['balance']} фото\n"
            f"📍 Объект: {context}\n"
            f"📊 Таблица: {spreadsheet_url}\n"
            f"📅 Регистрация: {user['created_at']}",
            parse_mode="HTML"
        )

    except ValueError:
        await message.answer("⚠️ User ID должен быть числом")
    except Exception as e:
        logger.error(f"Error in admin_user: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка: {e}")


@router.message(Command("admin_stats"))
async def cmd_admin_stats(message: Message):
    """Get bot statistics (admin only)"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("⛔ Эта команда доступна только администраторам")
        return

    try:
        # Get statistics from database
        async with db.get_connection() as conn:
            # Total users
            cursor = await conn.execute("SELECT COUNT(*) FROM users")
            total_users = (await cursor.fetchone())[0]

            # Total analyses
            cursor = await conn.execute("SELECT COUNT(*) FROM analysis_history")
            total_analyses = (await cursor.fetchone())[0]

            # Relevant analyses
            cursor = await conn.execute("SELECT COUNT(*) FROM analysis_history WHERE is_relevant = 1")
            relevant_analyses = (await cursor.fetchone())[0]

            # Total defects found
            cursor = await conn.execute("SELECT SUM(defects_found) FROM analysis_history WHERE is_relevant = 1")
            result = await cursor.fetchone()
            total_defects = result[0] if result[0] else 0

            # Users with balance > 0
            cursor = await conn.execute("SELECT COUNT(*) FROM users WHERE balance > 0")
            users_with_balance = (await cursor.fetchone())[0]

            # Total balance
            cursor = await conn.execute("SELECT SUM(balance) FROM users")
            result = await cursor.fetchone()
            total_balance = result[0] if result[0] else 0

        await message.answer(
            f"📊 <b>Статистика бота</b>\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"💰 Пользователей с балансом: {users_with_balance}\n"
            f"💳 Общий баланс: {total_balance} фото\n\n"
            f"📸 Всего анализов: {total_analyses}\n"
            f"✅ Релевантных фото: {relevant_analyses}\n"
            f"🚨 Найдено дефектов: {total_defects}\n\n"
            f"🤖 Версия: v{config.BOT_VERSION}",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error in admin_stats: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка: {e}")


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Show admin commands (admin only)"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("⛔ Эта команда доступна только администраторам")
        return

    await message.answer(
        "🔧 <b>Админские команды:</b>\n\n"
        "<code>/admin_addbalance &lt;user_id&gt; &lt;количество&gt;</code> - Пополнить баланс пользователю\n"
        "<code>/admin_user &lt;user_id&gt;</code> - Информация о пользователе\n"
        "<code>/admin_stats</code> - Статистика бота\n"
        "<code>/admin_dashboard</code> - Создать админскую таблицу\n"
        "<code>/admin_sync</code> - Синхронизировать данные в таблицу\n"
        "<code>/admin_backup</code> - Бэкап базы данных\n"
        "<code>/admin</code> - Список команд",
        parse_mode="HTML"
    )


@router.message(Command("admin_dashboard"))
async def cmd_admin_dashboard(message: Message):
    """Create or show admin analytics dashboard (admin only)"""
    global ADMIN_DASHBOARD_ID
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("⛔ Эта команда доступна только администраторам")
        return

    try:
        if ADMIN_DASHBOARD_ID:
            # Dashboard already exists
            url = f"https://docs.google.com/spreadsheets/d/{ADMIN_DASHBOARD_ID}/edit"
            await message.answer(
                f"📊 <b>Админская таблица уже создана:</b>\n\n"
                f"{url}\n\n"
                f"Используй <code>/admin_sync</code> для обновления данных.",
                parse_mode="HTML"
            )
            return

        await message.answer("⏳ Создаю админскую таблицу...")

        # Create dashboard
        result = admin_analytics_service.create_admin_dashboard()
        ADMIN_DASHBOARD_ID = result['spreadsheet_id']

        await message.answer(
            f"✅ <b>Админская таблица создана!</b>\n\n"
            f"📊 {result['url']}\n\n"
            f"⚠️ <b>Важно!</b> Добавь в .env на сервере:\n"
            f"<code>ADMIN_DASHBOARD_ID={ADMIN_DASHBOARD_ID}</code>\n\n"
            f"Используй <code>/admin_sync</code> для синхронизации данных.",
            parse_mode="HTML"
        )

        logger.info(f"Admin dashboard created: {result['url']}")

    except Exception as e:
        logger.error(f"Error creating admin dashboard: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка при создании таблицы: {e}", parse_mode=None)


@router.message(Command("admin_sync"))
async def cmd_admin_sync(message: Message):
    """Sync data to admin analytics dashboard (admin only)"""
    global ADMIN_DASHBOARD_ID
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("⛔ Эта команда доступна только администраторам")
        return

    if not ADMIN_DASHBOARD_ID:
        await message.answer(
            "⚠️ Админская таблица не создана.\n\n"
            "Используй <code>/admin_dashboard</code> для создания.",
            parse_mode="HTML"
        )
        return

    try:
        await message.answer("⏳ Синхронизирую данные...")

        # Sync all data
        await admin_analytics_service.sync_users_to_sheet(ADMIN_DASHBOARD_ID, db)
        await admin_analytics_service.sync_payments_to_sheet(ADMIN_DASHBOARD_ID, db)
        await admin_analytics_service.sync_analyses_to_sheet(ADMIN_DASHBOARD_ID, db)

        url = f"https://docs.google.com/spreadsheets/d/{ADMIN_DASHBOARD_ID}/edit"

        await message.answer(
            f"✅ <b>Данные синхронизированы!</b>\n\n"
            f"📊 {url}",
            parse_mode="HTML"
        )

        logger.info(f"Admin dashboard synced: {ADMIN_DASHBOARD_ID}")

    except Exception as e:
        logger.error(f"Error syncing admin dashboard: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка при синхронизации: {e}")


@router.message(Command("admin_backup"))
async def cmd_admin_backup(message: Message):
    """Create database backup (admin only)"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("⛔ Эта команда доступна только администраторам")
        return

    try:
        await message.answer("⏳ Создаю бэкап базы данных...")

        # Get database stats
        stats = backup_service.get_db_stats()

        if not stats.get('exists'):
            await message.answer("⚠️ Файл базы данных не найден")
            return

        # Backup to Google Drive
        backup_url = backup_service.backup_to_drive()

        # Send file to admin
        db_path = backup_service.get_db_file_path()
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M')

        caption = (
            f"📦 <b>Бэкап базы данных</b>\n\n"
            f"📅 Дата: {timestamp}\n"
            f"📊 Размер: {stats['size_kb']} KB\n"
            f"🕐 Изменен: {stats['modified']}\n\n"
            f"☁️ Google Drive: <a href='{backup_url}'>Открыть</a>"
        )

        await message.answer_document(
            document=FSInputFile(db_path, filename=f"bot_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"),
            caption=caption,
            parse_mode="HTML"
        )

        logger.info(f"Admin {user_id} created manual backup: {backup_url}")

    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка при создании бэкапа: {e}")


@router.message(Command("admin_delete_user"))
async def cmd_admin_delete_user(message: Message):
    """Delete user from database (admin only)"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("⛔ Эта команда доступна только администраторам")
        return

    # Parse command: /admin_delete_user <user_id>
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer(
                "📝 <b>Использование:</b>\n"
                "<code>/admin_delete_user &lt;user_id&gt;</code>\n\n"
                "<b>Пример:</b>\n"
                "<code>/admin_delete_user 123456789</code>\n\n"
                "⚠️ <b>Внимание:</b> Это полностью удалит пользователя и все его данные из базы!",
                parse_mode="HTML"
            )
            return

        target_user_id = int(parts[1])

        # Check if user exists
        user = await db.get_user(target_user_id)
        if not user:
            await message.answer(f"⚠️ Пользователь с ID {target_user_id} не найден в базе")
            return

        # Show user info before deletion
        username = user.get('username', 'Unknown')
        balance = user.get('balance', 0)
        context = user.get('context_object', 'Не установлен')

        # Delete user
        success = await db.delete_user(target_user_id)

        if success:
            logger.info(f"Admin {user_id} deleted user {target_user_id} (@{username})")
            await message.answer(
                f"✅ <b>Пользователь удалён!</b>\n\n"
                f"👤 User ID: <code>{target_user_id}</code>\n"
                f"👤 Username: @{username}\n"
                f"💳 Баланс был: {balance} фото\n"
                f"📍 Объект был: {context}\n\n"
                f"Все данные пользователя удалены из базы.",
                parse_mode="HTML"
            )
        else:
            await message.answer(f"⚠️ Ошибка при удалении пользователя {target_user_id}")

    except ValueError:
        await message.answer("⚠️ Неверный формат user_id. Используй число.")
    except Exception as e:
        logger.error(f"Error deleting user: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка при удалении пользователя: {e}", parse_mode=None)
