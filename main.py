import os
import asyncio
import logging
import html
from dataclasses import dataclass

import aiosqlite
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv()
logging.basicConfig(level=logging.INFO)

DB_PATH = "bot.db"


@dataclass(frozen=True)
class LangText:
    greeting_vacancy: str
    greeting_service: str
    help_text: str
    help_text: str
    submitted: str
    vip_offer: str
    vip_details: str
    approved: str
    rejected_prefix: str
    need_info_prefix: str
    choose_type_text: str
    btn_vacancy: str
    btn_service: str
    start_input_text: str
    payment_received: str
    tariffs: str
    btn_add_ad: str
    delete_request_sent: str


KZ_TARIFFS = """💸Тарифтер және қызметтер

💡Хабарландыру қосу — ТЕГІН (айдың соңына дейін)
Бұл қызметке мыналар кіреді:
• Мәліметтерді қабылдау және тексеру
• Хабарландыруды дұрыс форматта рәсімдеу (тақырып, сипаттама, айлық/баға, тэгтер)
• Сайтқа жариялау

🗓Жариялану мерзімі: 30 күн (1 ай)

📆1 айға ұзарту — 650 ₸
Егер хабарландыру өзекті болса, 30 күнге ұзартамыз.
Ұзарту кезінде:
• Күні жаңарады (хабарландыру “жаңа” болып көрінеді)
• Қажет болса, ақпарат жаңартылады (айлық/шарт/байланыс)

🔥VIP мәртебесі (қосымша қызмет)
VIP хабарландыру:
• Тізімнің ең үстінде көрсетіледі
• “TOP” белгісімен ерекшеленеді
• Көбірек қаралым жинауға көмектеседі

💰VIP бағасы:
• 7 күн — 1000 ₸
• 14 күн — 2000 ₸
• 30 күн — 3000 ₸
"""

KZ_GREETING_VACANCY = """📌Хабарландыру үшін жіберетін ақпарат

1️⃣ Түрі: Вакансия

2️⃣ Міндетті түрде көрсетіңіз❗️:
• Компания/бизнес атауы

3️⃣ Негізгі ақпарат:
📃• Сипаттама
💵• Баға
📊• График/шарттар (5/2, ауысым, қашықтан/офлайн т.б.)
⏰• Жұмыс уақыты
📍• Мекенжай
📞• Байланыс нөмірі
📷• Фото/логотип (бар болса)
💌• Әлеуметтік желілеріңіз (Instagram / TikTok / Telegram / сайт сілтемесі)
📚• Талаптар, тәжірибе, жас шектеуі, жолақы/тамақ/тұру, т.б.

❗️Мәліметті бір хабарламаға жинап жіберсеңіз, тезірек рәсімдейміз❗️
Хабарландыруды өшіру үшін /delete командасын жіберіңіз.
Көмек керек болса, @spiritz777 жазуыңызға болады.
"""

KZ_GREETING_SERVICE = """📌Хабарландыру үшін жіберетін ақпарат

1️⃣ Түрі: Анкета / Қызмет

2️⃣ Міндетті түрде көрсетіңіз❗️:
• Аты-жөніңіз

3️⃣ Негізгі ақпарат:
📃• Сипаттама
💵• Баға
📊• График/шарттар (5/2, ауысым, қашықтан/офлайн т.б.)
⏰• Жұмыс уақыты
📍• Мекенжай
📞• Байланыс нөмірі
💌• Әлеуметтік желілеріңіз (қалауыңызша): Instagram / TikTok / Telegram / сайт сілтемесі
📚• Тәжірибе: қанша жыл, қай жерде жұмыс істедіңіз
🎓• Білім: оқу орны / курс / сертификат (болса)
🛠• Дағдылар: негізгі skills, бағдарлама/құралдар (мыс: Excel, Photoshop, т.б.)
🌐• Тілдер: қазақ/орыс/ағылшын деңгейі
📎• Портфолио/резюме: сілтеме немесе файл (болса)

❗️Мәліметті бір хабарламаға жинап жіберсеңіз, тезірек рәсімдейміз❗️
Хабарландыруды өшіру үшін /delete командасын жіберіңіз.
Көмек керек болса, @spiritz777 жазуыңызға болады.
"""

RU_TARIFFS = """💸 Тарифы и услуги

💡 Добавление объявления — БЕСПЛАТНО (до конца месяца)
В услугу входит:
• Приём и проверка информации
• Оформление объявления в нужном формате (заголовок, описание, зарплата/цена, теги)
• Публикация на сайте

🗓 Срок размещения: 30 дней (1 месяц)

📆 Продление на 1 месяц — 650 ₸
Если объявление остаётся актуальным, продлеваем ещё на 30 дней.
При продлении:
• Обновляется дата (объявление выглядит “свежим”)
• При необходимости обновляем информацию (зарплата/условия/контакты)

🔥 VIP-статус (дополнительная услуга)
VIP-объявление:
• Показывается вверху списка
• Отмечено значком “TOP”
• Помогает собрать больше просмотров

💰 Цена VIP:
• 7 дней — 1000 ₸
• 14 дней — 2000 ₸
• 30 дней — 3000 ₸
"""

RU_GREETING_VACANCY = """📌 Информация, которую нужно отправить для объявления

1️⃣ Тип: Вакансия

2️⃣ Обязательно укажите❗️:
• Название компании/бизнеса

3️⃣ Основная информация:
📃• Описание
💵• Зарплата/цена
📊• График/условия (5/2, смены, удалённо/офлайн и т.д.)
⏰• Время работы (например: 09:00–18:00)
📍• Адрес (по желанию)
📞• Контактный номер (WhatsApp/звонки)
📷• Фото/логотип (если есть)
💌• Ваши соцсети (по желанию): Instagram / TikTok / Telegram / ссылка на сайт
📚• Требования, опыт, возрастные ограничения, проезд/питание/проживание и т.д.

❗️Если отправите всё одним сообщением, оформим быстрее❗️
Чтобы удалить объявление, отправьте команду /delete.
Если нужна помощь, можете написать @spiritz777.
"""

RU_GREETING_SERVICE = """📌Информация, которую нужно отправить для объявления

1️⃣ Тип: Услуга / Анкета

2️⃣ Обязательно укажите❗️:
• Ваше имя (ФИО/имя)

3️⃣ Основная информация:
📃• Описание
💵• Зарплата/цена
📊• График/условия (5/2, смены, удалённо/офлайн и т.д.)
⏰• Время работы (например: 09:00–18:00)
📍• Адрес (по желанию)
📞• Контактный номер (WhatsApp/звонки)
📷• Фото/логотип (если есть)
💌• Ваши соцсети (по желанию): Instagram / TikTok / Telegram / ссылка на сайт
🎓• Образование: учебное заведение / курсы / сертификаты (если есть)
🛠• Навыки: основные навыки, программы/инструменты (например: Excel, Photoshop и т.д.)
🌐• Языки: уровень казахского/русского/английского
📎• Портфолио/резюме: ссылка или файл (если есть)

❗️Если отправите всё одним сообщением, оформим быстрее❗️
Чтобы удалить объявление, отправьте команду /delete.
Если нужна помощь, можете написать @spiritz777.
"""

VIP_DETAILS_RU = (
    "🔥 VIP-статус\n"
    "• 7 дней — 1000 ₸\n"
    "• 14 дней — 2000 ₸\n"
    "• 30 дней — 3000 ₸\n\n"
    "Оплата:\n"
    "Kaspi: +7 700 200 9510\n"
    "Карта: 4400 4303 4626 5066\n"
    "Получатель: Жандос О.\n\n"
    "После оплаты отправьте чек/скрин — и мы подключим VIP."
)

VIP_DETAILS_KZ = (
    "🔥 VIP мәртебесі\n"
    "• 7 күн — 1000 ₸\n"
    "• 14 күн — 2000 ₸\n"
    "• 30 күн — 3000 ₸\n\n"
    "Төлем:\n"
    "Kaspi: +7 700 200 9510\n"
    "Карта: 4400 4303 4626 5066\n"
    "Алушы: Жандос О.\n\n"
    "Төлемнен кейін чек/скрин жіберіңіз — VIP қосамыз."
)

TEXTS = {
    "ru": LangText(
        greeting_vacancy=RU_GREETING_VACANCY,
        greeting_service=RU_GREETING_SERVICE,
        help_text="Отправьте заявку сообщением. Мы проверим и ответим.",
        submitted="Заявка отправлена. Ожидайте модерацию.",
        vip_offer="Хотите добавить VIP-статус? (поднимем объявление вверх и отметим TOP)",
        vip_details=VIP_DETAILS_RU,
        approved="Заявка принята. Мы проверим данные и добавим на сайт. Если потребуется уточнение — напишем. Для удаления объявления отправьте команду /delete.",
        rejected_prefix="Заявка отклонена. Причина:",
        need_info_prefix="Нужны уточнения по заявке:",
        choose_type_text="Выберите тип объявления:",
        btn_vacancy="Вакансия",
        btn_service="Услуга",
        start_input_text="Теперь отправьте текст вашей заявки.",
        payment_received="✅Чек получен. Ожидайте подтверждения.",
        tariffs=RU_TARIFFS,
        btn_add_ad="Добавить объявление",
        delete_request_sent="✅ Запрос на удаление отправлен администратору.",
    ),
    "kz": LangText(
        greeting_vacancy=KZ_GREETING_VACANCY,
        greeting_service=KZ_GREETING_SERVICE,
        help_text="Өтінімді хабарлама ретінде жіберіңіз. Тексеріп, жауап береміз.",
        submitted="Өтінім жіберілді. Модерацияны күтіңіз.",
        vip_offer="VIP мәртебесін қосқыңыз келе ме? (хабарландыру жоғарыға шығып, TOP белгісі болады)",
        vip_details=VIP_DETAILS_KZ,
        approved="Өтінім қабылданды. Мәліметтерді тексеріп, сайтқа қосамыз. Қажет болса, нақтылау сұраймыз. Хабарландыруды өшіру үшін /delete командасын жіберіңіз.",
        rejected_prefix="Өтінім қабылданбады. Себебі:",
        need_info_prefix="Өтінім бойынша қосымша ақпарат керек:",
        choose_type_text="Хабарландыру түрін таңдаңыз:",
        btn_vacancy="Вакансия",
        btn_service="Қызмет",
        start_input_text="Енді өтінім мәтінін жіберіңіз.",
        payment_received="✅Чек қабылданды. Растауды күтіңіз.",
        tariffs=KZ_TARIFFS,
        btn_add_ad="Хабарландыру қосу",
        delete_request_sent="✅ Өшіру туралы сұраныс администраторға жіберілді.",
    ),
}


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Қазақша", callback_data="lang:kz")],
            [InlineKeyboardButton(text="Русский", callback_data="lang:ru")],
        ]
    )


def type_keyboard(lang_code: str) -> InlineKeyboardMarkup:
    texts = TEXTS.get(lang_code, TEXTS["ru"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts.btn_vacancy, callback_data="type:vacancy"),
                InlineKeyboardButton(text=texts.btn_service, callback_data="type:service"),
            ]
        ]
    )


def admin_actions_kb(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"a:ok:{ticket_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"a:rej:{ticket_id}"),
            ],
            [
                InlineKeyboardButton(text="📝 Нужны данные", callback_data=f"a:need:{ticket_id}"),
                InlineKeyboardButton(text="🚫 Бан", callback_data=f"a:ban:{ticket_id}"),
            ],
        ]
    )


def vip_offer_kb(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅", callback_data=f"vip:yes:{ticket_id}"),
                InlineKeyboardButton(text="❌", callback_data=f"vip:no:{ticket_id}"),
            ]
        ]
    )


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                lang TEXT NOT NULL
            )
            """
        )
        try:
            await db.execute("ALTER TABLE users ADD COLUMN active_type TEXT")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
        except Exception:
            pass

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lang TEXT NOT NULL,
                status TEXT NOT NULL,
                admin_chat_id INTEGER NOT NULL,
                admin_header_msg_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        try:
            await db.execute("ALTER TABLE tickets ADD COLUMN ticket_type TEXT")
        except Exception:
            pass

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_prompts (
                prompt_msg_id INTEGER PRIMARY KEY,
                admin_chat_id INTEGER NOT NULL,
                ticket_id INTEGER NOT NULL,
                action TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS message_map (
                admin_msg_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL
            )
            """
        )
        await db.commit()


async def set_user_lang(user_id: int, lang: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users(user_id, lang) VALUES(?, ?)
            ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang
            """,
            (user_id, lang),
        )
        await db.commit()


async def set_user_type(user_id: int, ticket_type: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET active_type=? WHERE user_id=?",
            (ticket_type, user_id),
        )
        await db.commit()


        await db.commit()


async def ban_user(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
        await db.commit()


async def is_user_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT is_banned FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return bool(row[0]) if row else False


async def get_user_lang_and_type(user_id: int) -> tuple[str, str | None] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT lang, active_type FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return row if row else None


async def get_user_lang(user_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else None


async def create_ticket(user_id: int, lang: str, admin_chat_id: int, ticket_type: str | None = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO tickets(user_id, lang, status, admin_chat_id, ticket_type) VALUES(?, ?, ?, ?, ?)",
            (user_id, lang, "new", admin_chat_id, ticket_type),
        )
        await db.commit()
        return cur.lastrowid


async def set_ticket_header(ticket_id: int, header_msg_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET admin_header_msg_id=? WHERE id=?",
            (header_msg_id, ticket_id),
        )
        await db.commit()


async def update_ticket_status(ticket_id: int, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tickets SET status=? WHERE id=?", (status, ticket_id))
        await db.commit()


async def get_waiting_ticket(user_id: int) -> tuple[int, int, int] | None:
    # returns (ticket_id, admin_chat_id, admin_header_msg_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, admin_chat_id, admin_header_msg_id FROM tickets WHERE user_id=? AND status='waiting_vip_receipt' ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        row = await cur.fetchone()
        return row if row else None


async def get_ticket(ticket_id: int) -> tuple[int, str, str, int, int | None] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT user_id, lang, status, admin_chat_id, admin_header_msg_id FROM tickets WHERE id=?",
            (ticket_id,),
        )
        row = await cur.fetchone()
        return row if row else None


async def save_admin_prompt(prompt_msg_id: int, admin_chat_id: int, ticket_id: int, action: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO admin_prompts(prompt_msg_id, admin_chat_id, ticket_id, action) VALUES(?, ?, ?, ?)",
            (prompt_msg_id, admin_chat_id, ticket_id, action),
        )
        await db.commit()


async def resolve_admin_prompt(prompt_msg_id: int, admin_chat_id: int) -> tuple[int, str] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT ticket_id, action FROM admin_prompts WHERE prompt_msg_id=? AND admin_chat_id=?",
            (prompt_msg_id, admin_chat_id),
        )
        row = await cur.fetchone()
        return row if row else None


async def delete_admin_prompt(prompt_msg_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admin_prompts WHERE prompt_msg_id=?", (prompt_msg_id,))
        await db.commit()


async def save_message_map(admin_msg_id: int, user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO message_map(admin_msg_id, user_id) VALUES(?, ?)",
            (admin_msg_id, user_id),
        )
        await db.commit()


async def get_user_from_message_map(admin_msg_id: int) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM message_map WHERE admin_msg_id=?", (admin_msg_id,))
        row = await cur.fetchone()
        return row[0] if row else None


def build_admin_header(user: types.User, lang: str, ticket_id: int, ticket_type: str | None = None) -> str:
    # Clickable User Name
    user_link = f'<a href="tg://user?id={user.id}">{html.escape(user.full_name)}</a>'
    username = f"@{user.username}" if user.username else "(no username)"
    type_str = ticket_type.upper() if ticket_type else "UNKNOWN"
    return (
        f"🆕 Заявка #{ticket_id}\n"
        f"Type: {type_str}\n"
        f"User: {user_link}\n"
        f"ID: {user.id}\n"
        f"Lang: {lang}\n"
        f"Username: {username}\n\n"
        f"Действия ниже:"
    )


async def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set in .env")

    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))

    await init_db()

    bot = Bot(token=token)
    dp = Dispatcher()

    @dp.message(Command("chatid"))
    async def cmd_chatid(message: types.Message):
        await message.answer(f"chat_id = {message.chat.id}")

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        if message.chat.type != "private":
            return
        await message.answer("👋Тілді таңдаңыз / Выберите язык :", reply_markup=lang_keyboard())

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        if message.chat.type != "private":
            return
        lang = await get_user_lang(message.from_user.id) or "ru"
        await message.answer(TEXTS[lang].help_text)

    @dp.message(Command("delete"))
    async def cmd_delete(message: types.Message):
        if message.chat.type != "private":
            return
        
        lang = await get_user_lang(message.from_user.id) or "ru"
        
        # Clickable User Name for Admin
        user_link = f'<a href="tg://user?id={message.from_user.id}">{html.escape(message.from_user.full_name)}</a>'
        username = f"@{message.from_user.username}" if message.from_user.username else "(no username)"

        admin_text = (
            f"🗑 <b>Запрос на удаление объявления</b>\n"
            f"User: {user_link}\n"
            f"ID: {message.from_user.id}\n"
            f"Username: {username}\n"
            f"Lang: {lang}\n"
            f"Проверьте историю или последние тикеты."
        )

        if admin_chat_id != 0:
            await bot.send_message(chat_id=admin_chat_id, text=admin_text, parse_mode="HTML")
            await message.answer(TEXTS[lang].delete_request_sent)
        else:
            await message.answer("Admin chat not configured.")

    @dp.callback_query(F.data.startswith("lang:"))
    async def on_lang_choice(callback: types.CallbackQuery):
        lang = callback.data.split(":", 1)[1]
        if lang not in TEXTS:
            await callback.answer("Unknown language", show_alert=True)
            return

        await set_user_lang(callback.from_user.id, lang)
        
        # 1. Show Tariffs (edit the lang message or send new?)
        # Let's simple edit the message to TARIFFS text
        
        finish_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=TEXTS[lang].btn_add_ad, callback_data="start_ad")]
            ]
        )
        await callback.message.edit_text(TEXTS[lang].tariffs, reply_markup=finish_kb)
        await callback.answer()

    @dp.callback_query(F.data == "start_ad")
    async def on_start_ad(callback: types.CallbackQuery):
        lang = await get_user_lang(callback.from_user.id) or "ru"
        
        # Now show the type selection
        await callback.message.answer(TEXTS[lang].choose_type_text, reply_markup=type_keyboard(lang))
        await callback.answer()

    @dp.callback_query(F.data.startswith("type:"))
    async def on_type_choice(callback: types.CallbackQuery):
        ticket_type = callback.data.split(":", 1)[1]
        await set_user_type(callback.from_user.id, ticket_type)
        
        lang = await get_user_lang(callback.from_user.id) or "ru"
        
        
        await callback.answer("OK")
        await callback.message.edit_reply_markup(reply_markup=None)
        
        texts = TEXTS.get(lang, TEXTS["ru"])
        if ticket_type == "vacancy":
            await callback.message.answer(texts.greeting_vacancy)
        else:
            await callback.message.answer(texts.greeting_service)
            
        await callback.message.answer(texts.start_input_text)

    # Пользователь отправляет заявку в личке → создаём тикет и кидаем в админ-чат с кнопками
    @dp.message(F.chat.type == "private")
    async def handle_user_message(message: types.Message):
        nonlocal admin_chat_id

        # не пересылаем команды в поддержку
        if message.text and message.text.startswith("/"):
            return

        if await is_user_banned(message.from_user.id):
            return

        if admin_chat_id == 0:
            await message.answer("Поддержка ещё не настроена (ADMIN_CHAT_ID=0).")
            return

        user_data = await get_user_lang_and_type(message.from_user.id)
        if not user_data:
            lang, active_type = "ru", None
        else:
            lang, active_type = user_data

        # CHECK IF USER IS SENDING VIP RECEIPT
        waiting_ticket = await get_waiting_ticket(message.from_user.id)
        if waiting_ticket:
            ticket_id, t_admin_chat_id, header_msg_id = waiting_ticket
            
            # Forward receipt to admin
            if header_msg_id:
                await bot.send_message(
                    chat_id=t_admin_chat_id,
                    text=f"💸 Чек/Оплата от пользователя (Тикет #{ticket_id}) по VIP:",
                    reply_to_message_id=header_msg_id
                )
            else:
                await bot.send_message(chat_id=t_admin_chat_id, text=f"💸 Чек/Оплата от пользователя (Тикет #{ticket_id}) по VIP:")

            # Copy the actual message (photo/file/text)
            forwarded = await bot.copy_message(
                chat_id=t_admin_chat_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                reply_to_message_id=header_msg_id if header_msg_id else None
            )
            # Save mapping so admin can reply
            await save_message_map(forwarded.message_id, message.from_user.id)

            # Update status back to something else so we don't get stuck?
            # Or keep it waiting if they send multiple photos? 
            # Let's set it to 'new' or 'vip_paid' to stop the loop, or keep it if we expect more.
            # User request implies "loop" is bad. So let's reset to 'vip_paid' or just 'new'.
            await update_ticket_status(ticket_id, "vip_paid")

            await message.answer(TEXTS[lang].payment_received)
            return

        ticket_id = await create_ticket(message.from_user.id, lang, admin_chat_id, active_type)

        header_text = build_admin_header(message.from_user, lang, ticket_id, active_type)
        header_msg = await bot.send_message(
            chat_id=admin_chat_id,
            text=header_text,
            reply_markup=admin_actions_kb(ticket_id),
            parse_mode="HTML"
        )
        await set_ticket_header(ticket_id, header_msg.message_id)
        # Also save header message ID to map, so admin can reply to the header too
        await save_message_map(header_msg.message_id, message.from_user.id)

        forwarded = await bot.copy_message(
            chat_id=admin_chat_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            reply_to_message_id=header_msg.message_id,
        )
        await save_message_map(forwarded.message_id, message.from_user.id)

        # Ответ пользователю: локализовано + VIP оффер
        await message.answer(TEXTS[lang].submitted)
        await message.answer(TEXTS[lang].vip_offer, reply_markup=vip_offer_kb(ticket_id))

    # VIP выбор пользователя
    @dp.callback_query(F.data.startswith("vip:"))
    async def on_vip_choice(callback: types.CallbackQuery):
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("Bad callback", show_alert=True)
            return

        choice = parts[1]  # yes/no
        ticket_id = int(parts[2])

        lang = await get_user_lang(callback.from_user.id) or "ru"

        if choice == "yes":
            await callback.answer("OK")
            # Set status to waiting_vip_receipt so next message is treated as receipt
            await update_ticket_status(ticket_id, "waiting_vip_receipt")
            
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer(TEXTS[lang].vip_details)

            # уведомим админ-чат, что по тикету хотят VIP
            if admin_chat_id != 0:
                t = await get_ticket(ticket_id)
                if t:
                    _, _, _, _, header_msg_id = t
                    note = f"🔥 Пользователь по заявке #{ticket_id} хочет VIP."
                    if header_msg_id:
                        await callback.bot.send_message(
                            chat_id=admin_chat_id,
                            text=note,
                            reply_to_message_id=header_msg_id,
                        )
                    else:
                        await callback.bot.send_message(chat_id=admin_chat_id, text=note)
            return

        if choice == "no":
            await callback.answer("OK")
            await callback.message.edit_reply_markup(reply_markup=None)
            return

        await callback.answer("Неизвестный выбор", show_alert=True)

    # Нажатия админ-кнопок
    @dp.callback_query(F.data.startswith("a:"))
    async def on_admin_action(callback: types.CallbackQuery):
        if admin_chat_id == 0:
            await callback.answer("ADMIN_CHAT_ID=0", show_alert=True)
            return
        if callback.message.chat.id != admin_chat_id:
            await callback.answer("Не тот чат", show_alert=True)
            return

        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("Bad callback", show_alert=True)
            return

        action = parts[1]
        ticket_id = int(parts[2])

        t = await get_ticket(ticket_id)
        if not t:
            await callback.answer("Тикет не найден", show_alert=True)
            return

        user_id, lang, status, t_admin_chat_id, header_msg_id = t
        if t_admin_chat_id != admin_chat_id:
            await callback.answer("Не тот админ-чат", show_alert=True)
            return

        # Принять — без доп. вопросов
        if action == "ok":
            await update_ticket_status(ticket_id, "approved")
            await callback.message.edit_text(
                callback.message.text + "\n\n✅ Статус: ПРИНЯТО",
                reply_markup=None,
                parse_mode="HTML"
            )
            try:
                await bot.send_message(chat_id=user_id, text=TEXTS[lang].approved)
            except Exception:
                await callback.message.answer("⚠️ Пользователь заблокировал бота, сообщение не доставлено.")
            
            await callback.answer("Принято")
            await callback.message.react([types.ReactionTypeEmoji(emoji="👍")])
            return

        # Бан пользователя
        if action == "ban":
            await ban_user(user_id)
            await callback.message.edit_text(
                callback.message.text + "\n\n🚫 Статус: ЗАБАНЕН",
                reply_markup=None,
                parse_mode="HTML"
            )
            await callback.answer("Пользователь забанен")
            await callback.message.react([types.ReactionTypeEmoji(emoji="🔥")])
            return

        # Отклонить / Нужны данные — просим админа написать текст (reply)
        if action in ("rej", "need"):
            await update_ticket_status(ticket_id, "waiting_admin_text")

            prompt_text = (
                f"Ответьте НА ЭТО сообщение текстом для пользователя.\n"
                f"Тикет #{ticket_id}\n"
                f"Действие: {'ОТКЛОНИТЬ' if action == 'rej' else 'НУЖНЫ ДАННЫЕ'}"
            )
            prompt_msg = await bot.send_message(
                chat_id=admin_chat_id,
                text=prompt_text,
                reply_to_message_id=callback.message.message_id,
            )
            await save_admin_prompt(prompt_msg.message_id, admin_chat_id, ticket_id, action)

            await callback.message.edit_text(
                callback.message.text + "\n\n⏳ Статус: ОЖИДАЕТ ТЕКСТ ОТ АДМИНА",
                reply_markup=None,
                parse_mode="HTML"
            )
            await callback.answer("Ок, жду текст")
            await callback.message.react([types.ReactionTypeEmoji(emoji="🙈")])
            return

        await callback.answer("Неизвестное действие", show_alert=True)

    # Админ пишет reply на prompt → бот отправляет юзеру
    @dp.message()
    async def on_admin_reply(message: types.Message):
        if admin_chat_id == 0:
            return
        if message.chat.id != admin_chat_id:
            return
        if not message.reply_to_message:
            return

        # 1. Check if it's a response to an admin prompt (reject/need info)
        resolved = await resolve_admin_prompt(message.reply_to_message.message_id, admin_chat_id)
        if resolved:
            ticket_id, action = resolved
            t = await get_ticket(ticket_id)
            if not t:
                await delete_admin_prompt(message.reply_to_message.message_id)
                return

            user_id, lang, status, _, _ = t

            admin_text = message.text or ""
            if not admin_text.strip():
                await message.reply("Нужен текст (не пустое сообщение).")
                return

            if action == "rej":
                await update_ticket_status(ticket_id, "rejected")
                out = f"{TEXTS[lang].rejected_prefix}\n{admin_text}"
                await bot.send_message(chat_id=user_id, text=out)
                await message.reply(f"✅ Отправлено пользователю. Тикет #{ticket_id}: ОТКЛОНЕНО")
            elif action == "need":
                await update_ticket_status(ticket_id, "need_info")
                out = f"{TEXTS[lang].need_info_prefix}\n{admin_text}"
                await bot.send_message(chat_id=user_id, text=out)
                await message.reply(f"✅ Отправлено пользователю. Тикет #{ticket_id}: НУЖНЫ ДАННЫЕ")
            
            await delete_admin_prompt(message.reply_to_message.message_id)
            return

        # 2. Check if it's a normal reply to a user's forwarded message
        target_user_id = await get_user_from_message_map(message.reply_to_message.message_id)
        if target_user_id:
            try:
                # We copy the admin's message to the user (preserving photo/video/text)
                await message.copy_to(chat_id=target_user_id)
                await message.react([types.ReactionTypeEmoji(emoji="👍")])
            except Exception as e:
                await message.reply(f"❌ Не удалось отправить (юзер заблочил бота?):\n{e}")
            return

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
