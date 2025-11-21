"""
Payment handlers for DefectMaster Bot (Tinkoff Acquiring)
"""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from bot.database.models import db
from bot.services.payment_service import payment_service
import config
import uuid
import logging

logger = logging.getLogger(__name__)
router = Router()

# Package configuration (prices in rubles)
# Честные цены: 10₽ за фото, без психологических трюков
PACKAGES = {
    "small": {
        "credits": 20,
        "price": 200,
        "title": "20 фото",
        "description": "Пакет 20 анализов фотографий"
    },
    "medium": {
        "credits": 50,
        "price": 500,
        "title": "50 фото",
        "description": "Пакет 50 анализов фотографий"
    },
    "large": {
        "credits": 100,
        "price": 1000,
        "title": "100 фото",
        "description": "Пакет 100 анализов фотографий"
    }
}


@router.callback_query(F.data.startswith("buy_"))
async def handle_buy_callback(callback: CallbackQuery, bot: Bot):
    """Handle buy package callback - create payment link"""
    package_key = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Get package
    package = PACKAGES.get(package_key)
    if not package:
        await callback.answer("❌ Неверный пакет")
        return

    # Generate unique order ID
    order_id = f"{user_id}_{uuid.uuid4().hex[:8]}"

    # Convert rubles to kopecks
    amount_kopecks = package['price'] * 100

    # Initialize payment with Tinkoff
    try:
        payment_result = await payment_service.init_payment(
            order_id=order_id,
            amount=amount_kopecks,
            description=f"DefectMaster - {package['title']}",
            user_id=user_id
        )

        if not payment_result:
            await callback.answer("❌ Ошибка создания платежа", show_alert=True)
            logger.error(f"Failed to create Tinkoff payment for user {user_id}")
            return

        payment_url = payment_result.get('PaymentURL')
        payment_id = payment_result.get('PaymentId')

        if not payment_url or not payment_id:
            await callback.answer("❌ Ошибка получения ссылки на оплату", show_alert=True)
            logger.error(f"Missing PaymentURL or PaymentId in response: {payment_result}")
            return

        # Save payment to database
        await db.create_payment(
            order_id=order_id,
            user_id=user_id,
            amount=package['price'],
            credits=package['credits']
        )

        # Create payment button
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
                [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_payment_{payment_id}")]
            ]
        )

        await callback.message.edit_text(
            f"💰 **Оплата пакета**\n\n"
            f"📦 Пакет: {package['title']}\n"
            f"💵 Сумма: {package['price']} ₽\n"
            f"📸 Получите: {package['credits']} анализов\n\n"
            f"Нажмите кнопку ниже для оплаты:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error creating Tinkoff payment: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при создании платежа", show_alert=True)


@router.callback_query(F.data.startswith("check_payment_"))
async def handle_check_payment(callback: CallbackQuery):
    """Handle payment verification request"""
    payment_id = callback.data.split("_", 2)[2]
    user_id = callback.from_user.id

    try:
        # Check payment status with Tinkoff
        status = await payment_service.check_payment_status(payment_id)

        if status == "CONFIRMED":
            # Payment successful - find the payment record
            async with db.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM payments WHERE order_id LIKE ? AND user_id = ? AND status = 'pending'",
                    (f"{user_id}%", user_id)
                )
                payment = await cursor.fetchone()

                if not payment:
                    await callback.answer("⚠️ Платеж не найден", show_alert=True)
                    return

                # Get payment details
                order_id = payment[1]  # order_id
                credits = payment[4]    # credits

                # Update balance
                await db.update_balance(user_id, credits)

                # Update payment status
                await db.update_payment_status(order_id, 'completed')

                # Get new balance
                user = await db.get_user(user_id)
                new_balance = user['balance'] if user else credits

                # Send confirmation
                await callback.message.edit_text(
                    f"✅ **Платеж успешен!**\n\n"
                    f"Начислено: {credits} фото\n"
                    f"💳 Ваш баланс: {new_balance} фото\n\n"
                    f"Спасибо за покупку! Отправляйте фото для анализа.",
                    parse_mode="Markdown"
                )
                await callback.answer("✅ Платеж подтвержден!")

        elif status == "REJECTED" or status == "CANCELED":
            await callback.answer("❌ Платеж отклонен или отменен", show_alert=True)

        else:
            # Payment still pending or in progress
            await callback.answer(
                "⏳ Платеж еще обрабатывается. Попробуйте через несколько секунд.",
                show_alert=True
            )

    except Exception as e:
        logger.error(f"Error checking payment status: {e}", exc_info=True)
        await callback.answer("❌ Ошибка проверки платежа", show_alert=True)
