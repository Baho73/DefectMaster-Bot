"""
Payment handlers for DefectMaster Bot (Telegram Stars)
"""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery
from aiogram.filters import Command
from bot.database.models import db
from bot.services.stars_payment_service import stars_payment_service

router = Router()


@router.callback_query(F.data.startswith("buy_"))
async def handle_buy_callback(callback: CallbackQuery, bot: Bot):
    """Handle buy package callback - send invoice"""
    package_key = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Get invoice parameters
    invoice_params = stars_payment_service.get_invoice_params(package_key, user_id)

    if not invoice_params:
        await callback.answer("❌ Неверный пакет")
        return

    # Send invoice
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        **invoice_params
    )

    await callback.answer()


@router.pre_checkout_query()
async def handle_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Handle pre-checkout query - confirm payment"""
    # Parse payload
    parsed = stars_payment_service.parse_invoice_payload(
        pre_checkout_query.invoice_payload
    )

    if not parsed:
        await pre_checkout_query.answer(
            ok=False,
            error_message="Ошибка обработки платежа"
        )
        return

    # Verify user
    if parsed['user_id'] != pre_checkout_query.from_user.id:
        await pre_checkout_query.answer(
            ok=False,
            error_message="Неверный пользователь"
        )
        return

    # All checks passed
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message):
    """Handle successful payment - update balance"""
    # Parse payload
    parsed = stars_payment_service.parse_invoice_payload(
        message.successful_payment.invoice_payload
    )

    if not parsed:
        await message.answer("⚠️ Ошибка обработки платежа")
        return

    user_id = parsed['user_id']
    package_key = parsed['package_key']

    # Get package info
    package = stars_payment_service.get_package(package_key)
    if not package:
        await message.answer("⚠️ Пакет не найден")
        return

    # Update balance
    await db.update_balance(user_id, package['credits'])

    # Log payment
    await db.create_payment(
        order_id=message.successful_payment.telegram_payment_charge_id,
        user_id=user_id,
        amount=package['stars'],
        credits=package['credits']
    )
    await db.update_payment_status(
        message.successful_payment.telegram_payment_charge_id,
        'completed'
    )

    # Get new balance
    user = await db.get_user(user_id)
    new_balance = user['balance'] if user else package['credits']

    # Send confirmation
    await message.answer(
        f"✅ **Платеж успешен!**\n\n"
        f"Начислено: {package['credits']} фото\n"
        f"💳 Ваш баланс: {new_balance} фото\n\n"
        f"Спасибо за покупку! Отправляйте фото для анализа.",
        parse_mode="Markdown"
    )
