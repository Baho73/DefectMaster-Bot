"""
Common command handlers for DefectMaster Bot
"""
from aiogram import Router, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.models import db
from bot.services.google_service import google_service
from bot.utils.markdown_utils import escape_markdown, escape_html
import config
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    """Handle /start command with optional referral parameter"""
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"

    # Log start event
    await db.log_event(user_id, 'start')

    # Parse referral parameter from deep link
    # Format: /start ref_123456789
    referred_by = None
    if command.args and command.args.startswith("ref_"):
        try:
            referred_by = int(command.args[4:])
            # Don't allow self-referral
            if referred_by == user_id:
                referred_by = None
            # Check if referrer exists
            elif not await db.get_user(referred_by):
                referred_by = None
            else:
                logger.info(f"User {user_id} referred by {referred_by}")
        except ValueError:
            referred_by = None

    # Check if user exists
    user = await db.get_user(user_id)

    if not user:
        # Show version immediately
        await message.answer(f"🤖 DefectMaster Bot v{config.BOT_VERSION}")

        # Create new user with referral
        await db.create_user(user_id, username, referred_by)

        # Calculate starting credits for welcome message
        starting_credits = config.FREE_CREDITS
        if referred_by:
            starting_credits += config.REFERRAL_BONUS_INVITED

        # Create Google Spreadsheet
        try:
            spreadsheet_data = google_service.create_user_spreadsheet(username)
            await db.set_spreadsheet(user_id, spreadsheet_data['spreadsheet_id'])

            # Build welcome text
            if referred_by:
                bonus_text = f"🎁 **Бонус:** {starting_credits} анализов ({config.FREE_CREDITS} стартовых + {config.REFERRAL_BONUS_INVITED} за регистрацию по приглашению)!"
            else:
                bonus_text = f"🎁 **Бонус:** {config.FREE_CREDITS} бесплатных анализов!"

            welcome_text = f"""👋 Добро пожаловать в **DefectMaster Bot**!

Я — твой AI-помощник для строительного надзора. Присылай фото стройки, и я найду дефекты по нормам РФ (СНиП/ГОСТ).

{bonus_text}

📊 **Твоя таблица отчетов:**
[Открыть таблицу]({spreadsheet_data['url']})

📝 Для начала работы введи контекст объекта:
*Например: "ЖК Пионер, 5 этаж" или "Мост через р. Волга, опора №4"*

Команды:
/new - Сменить объект
/balance - Мой баланс
/table - Ссылка на таблицу
/help - Помощь

💬 [Сообщество](https://t.me/+unHOsuhOxmM2M2Ni) — задавай вопросы, предлагай фичи!
🌐 Сайт: https://teamplan.ru"""

            await message.answer(welcome_text, parse_mode="Markdown")

        except Exception as e:
            error_msg = escape_markdown(str(e))
            await message.answer(
                f"⚠️ Ошибка при создании таблицы: {error_msg}\n\nПопробуй позже или обратись к администратору.",
                parse_mode="Markdown"
            )
    else:
        # Show version immediately for existing users too
        await message.answer(f"🤖 DefectMaster Bot v{config.BOT_VERSION}")

        # Existing user - check if they have a spreadsheet
        if not user.get('spreadsheet_id'):
            # User doesn't have a spreadsheet - create one
            try:
                spreadsheet_data = google_service.create_user_spreadsheet(username)
                await db.set_spreadsheet(user_id, spreadsheet_data['spreadsheet_id'])

                await message.answer(
                    f"📊 **Таблица создана!**\n\n"
                    f"[Открыть таблицу]({spreadsheet_data['url']})\n\n"
                    f"Теперь все результаты анализа будут сохраняться в твою таблицу!",
                    parse_mode="Markdown"
                )
            except Exception as e:
                error_msg = escape_markdown(str(e))
                await message.answer(
                    f"⚠️ Ошибка при создании таблицы: {error_msg}\n\nПопробуй позже или обратись к администратору.",
                    parse_mode="Markdown"
                )
                return

        # Show welcome message
        # Use HTML instead of Markdown to avoid parsing issues
        balance = user['balance']
        context_display = escape_html(user['context_object']) if user['context_object'] else "не установлен"

        await message.answer(
            f"""👋 С возвращением!

💳 Баланс: {balance} фото
📍 Объект: {context_display}

Присылай фото для анализа или используй команды:
/new - Сменить объект
/balance - Пополнить баланс
/table - Открыть таблицу
/help - Помощь

💬 <a href="https://t.me/+unHOsuhOxmM2M2Ni">Сообщество</a> — задавай вопросы, предлагай фичи!
🌐 Сайт: https://teamplan.ru""",
            parse_mode="HTML",
            disable_web_page_preview=True
        )


@router.message(Command("new"))
async def cmd_new(message: Message):
    """Handle /new command - set new context"""
    await message.answer(
        "📝 Введи название объекта и место работ:\n\n"
        "*Например:*\n"
        "ЖК Сердце Столицы, -1 этаж\n"
        "Мост через р. Волга, опора №4\n"
        "Коттедж ул. Ленина 15, фундамент",
        parse_mode="Markdown"
    )


@router.message(Command("balance"))
async def cmd_balance(message: Message):
    """Handle /balance command"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)

    if not user:
        await message.answer("⚠️ Сначала нажми /start")
        return

    balance = user['balance']

    # Tinkoff packages - честные цены: 10₽ за фото
    packages = {
        "small": {"credits": 20, "price": 200},
        "medium": {"credits": 50, "price": 500},
        "large": {"credits": 100, "price": 1000}
    }

    # Create payment keyboard
    builder = InlineKeyboardBuilder()
    for key, pack in packages.items():
        builder.button(
            text=f"💳 {pack['credits']} фото - {pack['price']} ₽",
            callback_data=f"buy_{key}"
        )
    # Add referral button
    builder.button(
        text="👥 Пригласить коллегу",
        callback_data="invite_colleague"
    )
    builder.adjust(1)

    await message.answer(
        f"""💰 **Твой баланс:** {balance} фото

💳 **Честные цены: 10₽ за анализ**""",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "invite_colleague")
async def callback_invite_colleague(callback: CallbackQuery):
    """Handle invite colleague button"""
    user_id = callback.from_user.id
    bot_username = (await callback.bot.get_me()).username

    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    await callback.message.answer(
        f"""👥 **Пригласи коллегу и получи бонус!**

🔗 **Твоя реферальная ссылка:**
`{referral_link}`

📋 Как это работает:
1. Отправь ссылку коллеге
2. Он регистрируется и получает **{config.FREE_CREDITS + config.REFERRAL_BONUS_INVITED} фото** вместо {config.FREE_CREDITS}
3. Когда он сделает первый анализ строительного фото — ты получишь **+{config.REFERRAL_BONUS_INVITER} фото** на баланс!

💡 Бонус начисляется только за реальных пользователей, которые отправляют строительные фото.""",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(Command("table"))
async def cmd_table(message: Message):
    """Handle /table command"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)

    if not user:
        await message.answer("⚠️ Сначала нажми /start")
        return

    if not user['spreadsheet_id']:
        await message.answer("⚠️ У тебя еще нет таблицы. Используй /start")
        return

    url = google_service.get_spreadsheet_url(user['spreadsheet_id'])
    await message.answer(
        f"📊 **Твоя таблица отчетов:**\n[Открыть таблицу]({url})",
        parse_mode="Markdown"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """📖 **Как пользоваться ботом:**

1️⃣ Установи контекст командой /new
   *Например: "ЖК Пионер, 5 этаж"*

2️⃣ Присылай фото строительных работ
   Бот найдет дефекты и запишет в таблицу

3️⃣ Если кредиты закончились - /balance

**Команды:**
/start - Перезапуск
/new - Сменить объект
/balance - Баланс и оплата
/table - Моя таблица
/help - Эта справка

**Что анализирует бот:**
✅ Нарушения СНиП/ГОСТ/СП
✅ Критичность дефектов
✅ Рекомендации по устранению
✅ Ссылки на нормативы РФ

**Сообщество:**
💬 [Присоединяйся к обсуждению](https://t.me/+unHOsuhOxmM2M2Ni) — предлагай фичи, задавай вопросы, общайся с другими пользователями!"""

    await message.answer(help_text, parse_mode="Markdown")
