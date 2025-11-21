"""
Photo analysis handlers for DefectMaster Bot
"""
from aiogram import Router, F, Bot
from aiogram.types import Message
from bot.database.models import db
from bot.services.ai_service import ai_service
from bot.services.google_service import google_service
from bot.services.photo_storage_service import PhotoStorageService
from bot.services import error_notifier
from datetime import datetime
import logging
import config

logger = logging.getLogger(__name__)
router = Router()

# Initialize photo storage service
photo_storage = PhotoStorageService(
    storage_path=config.PHOTO_STORAGE_PATH,
    base_url=config.PHOTO_BASE_URL
)


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    """Handle photo messages"""
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"

    logger.info(f"Photo received from user {user_id} (@{username})")

    # Get user
    user = await db.get_user(user_id)
    if not user:
        logger.warning(f"User {user_id} not found in database")
        await message.answer("⚠️ Сначала нажми /start")
        return

    # Check context
    context = user.get('context_object')
    if not context:
        logger.info(f"User {user_id} has no context set")
        await message.answer(
            "⚠️ Сначала установи объект командой /new\n\n"
            "*Например: ЖК Пионер, 5 этаж*",
            parse_mode="Markdown"
        )
        return

    # Check balance
    if user['balance'] <= 0:
        logger.info(f"User {user_id} has insufficient balance: {user['balance']}")
        bot_username = (await bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

        await message.answer(
            f"❌ **Недостаточно кредитов!**\n\n"
            f"Используй /balance для пополнения.\n\n"
            f"💡 Или пригласи коллегу и получи **+{config.REFERRAL_BONUS_INVITER} фото бесплатно:**\n"
            f"`{referral_link}`",
            parse_mode="Markdown"
        )
        return

    logger.info(f"Processing photo for user {user_id}. Context: {context}, Balance: {user['balance']}")

    # Send "analyzing" message
    processing_msg = await message.answer("🔍 Анализирую фото...")

    try:
        # Download photo
        photo = message.photo[-1]  # Get highest resolution
        logger.info(f"Downloading photo {photo.file_id}, size: {photo.file_size} bytes")
        file = await bot.get_file(photo.file_id)
        photo_bytes = await bot.download_file(file.file_path)
        photo_data = photo_bytes.read()
        logger.info(f"Photo downloaded successfully. Size: {len(photo_data)} bytes")

        # Analyze with AI
        logger.info(f"Starting AI analysis for user {user_id}")
        analysis = await ai_service.analyze_photo(photo_data, context)
        logger.info(f"AI analysis completed for user {user_id}")

        # Check if relevant
        if not analysis.get('is_relevant'):
            # Not relevant - don't charge
            logger.info(f"Photo from user {user_id} is not relevant. Joke: {analysis.get('joke', 'N/A')}")
            await processing_msg.edit_text(
                f"😄 {analysis.get('joke', 'Фото не относится к строительству.')}\n\n"
                "Присылай фото строительных работ для анализа.",
                parse_mode="Markdown"
            )

            # Log non-relevant analysis
            await db.log_analysis(
                user_id=user_id,
                photo_id=photo.file_id,
                context=context,
                defects_found=0,
                is_relevant=False
            )
            logger.info(f"Non-relevant photo logged for user {user_id}")
            return

        logger.info(f"Photo is relevant. Defects found: {len(analysis.get('items', []))}")

        # Deduct credit
        await db.update_balance(user_id, -1)
        logger.info(f"Deducted 1 credit from user {user_id}. New balance: {user['balance'] - 1}")

        # Save photo to local storage with UUID hash
        logger.info(f"Saving photo to local storage for user {user_id}")
        photo_url = photo_storage.save_photo(photo_data, user_id)

        if not photo_url:
            logger.error(f"Failed to save photo for user {user_id}")
            await processing_msg.edit_text(
                "⚠️ Ошибка при сохранении фото. Попробуй еще раз.",
                parse_mode="Markdown"
            )
            return

        logger.info(f"Photo saved successfully. URL: {photo_url}")

        # Add to Google Sheets
        if user.get('spreadsheet_id'):
            logger.info(f"Adding defect row to Google Sheets for user {user_id}")
            google_service.add_defect_row(
                spreadsheet_id=user['spreadsheet_id'],
                analysis=analysis,
                context=context,
                photo_url=photo_url
            )
            logger.info(f"Defect row added to Google Sheets successfully")
        else:
            logger.warning(f"User {user_id} has no spreadsheet_id")

        # Log analysis
        await db.log_analysis(
            user_id=user_id,
            photo_id=photo.file_id,
            context=context,
            defects_found=len(analysis.get('items', [])),
            is_relevant=True
        )

        # Check and give referral bonus to inviter (only on first relevant analysis)
        if not await db.is_referral_bonus_given(user_id):
            referrer = await db.get_referrer(user_id)
            if referrer:
                # Give bonus to referrer
                await db.update_balance(referrer['user_id'], config.REFERRAL_BONUS_INVITER)
                await db.mark_referral_bonus_given(user_id)
                logger.info(f"Referral bonus +{config.REFERRAL_BONUS_INVITER} given to {referrer['user_id']} for inviting {user_id}")

                # Notify the referrer
                try:
                    referrer_username = user.get('username') or f"user_{user_id}"
                    await bot.send_message(
                        referrer['user_id'],
                        f"🎉 **Бонус за приглашение!**\n\n"
                        f"Ваш коллега @{referrer_username} сделал первый анализ строительного фото!\n\n"
                        f"💰 **+{config.REFERRAL_BONUS_INVITER} фото** начислено на ваш баланс!",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning(f"Failed to notify referrer {referrer['user_id']}: {e}")

        # Format and send result
        result_message = ai_service.format_telegram_message(analysis, context)

        # Add table link
        if user.get('spreadsheet_id'):
            table_url = google_service.get_spreadsheet_url(user['spreadsheet_id'])
            result_message += f"\n🔗 [Открыть таблицу]({table_url})"

        # Add balance info
        new_balance = user['balance'] - 1
        result_message += f"\n\n💳 Осталось: {new_balance} фото"

        await processing_msg.edit_text(result_message, parse_mode="Markdown")
        logger.info(f"Photo processing completed successfully for user {user_id}")

    except Exception as e:
        error_str = str(e)
        logger.error(f"Error processing photo for user {user_id}: {error_str}", exc_info=True)

        # Notify admins about the error
        await error_notifier.notify_admins_error(
            error=e,
            context="Photo analysis",
            user_id=user_id,
            username=username
        )

        # Check for specific errors
        if "429" in error_str or "exhausted" in error_str.lower() or "quota" in error_str.lower():
            error_message = (
                "⏳ **Лимит AI-запросов исчерпан**\n\n"
                "Сервис временно перегружен. Попробуй через 5-10 минут.\n\n"
                "💡 Твой баланс не изменился."
            )
        elif "503" in error_str or "unavailable" in error_str.lower():
            error_message = (
                "🔧 **AI-сервис временно недоступен**\n\n"
                "Ведутся технические работы. Попробуй через несколько минут."
            )
        else:
            error_message = (
                f"⚠️ Ошибка при анализе: {error_str[:100]}\n\n"
                "Попробуй еще раз или обратись к администратору."
            )

        await processing_msg.edit_text(error_message, parse_mode="Markdown")


@router.message(F.text & ~F.text.startswith('/'))
async def handle_text(message: Message):
    """Handle text messages (context setting)"""
    user_id = message.from_user.id

    # Get user
    user = await db.get_user(user_id)
    if not user:
        await message.answer("⚠️ Сначала нажми /start")
        return

    # Set context
    context_text = message.text.strip()
    await db.set_context(user_id, context_text)

    await message.answer(
        f"✅ Объект установлен: **{context_text}**\n\n"
        "Теперь присылай фото для анализа!\n\n"
        "💡 Все найденные дефекты будут записаны с этим контекстом.",
        parse_mode="Markdown"
    )
