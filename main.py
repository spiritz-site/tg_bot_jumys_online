import os
import asyncio
import logging
from dataclasses import dataclass
from contextlib import asynccontextmanager

import aiosqlite
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest

load_dotenv()
logging.basicConfig(level=logging.INFO)

DB_PATH = "bot.db"


# =========================
# Texts / i18n
# =========================
@dataclass(frozen=True)
class LangText:
    greeting: str
    help_text: str
    submitted: str
    submitted_more: str
    vip_offer: str
    vip_details: str
    approved: str
    rejected_prefix: str
    need_info_prefix: str


KZ_GREETING = """💸Тарифтер және қызметтер

💡Хабарландыру қосу — ТЕГІН (айдың соңына дейін)
Бұл қызметке мыналар кіреді:
• Мәліметтерді қабылдау және тексеру
• Хабарландыруды дұрыс форматта рәсімдеу (тақырып, сипаттама, айлық/баға, тэгтер)
• Сайтқа жариялау

🗓Жариялану мерзімі: 30 күн (1 ай)

📆1 айға ұзарту — 1500 ₸
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
• 7 күн — 2000 ₸
• 14 күн — 3000 ₸
• 30 күн — 5000 ₸

📌Хабарландыру үшін жіберетін ақпарат

1️⃣ Түрі: вакансия / анкета / қызмет

2️⃣ Міндетті түрде көрсетіңіз❗️:
• Егер вакансия болса — компания/бизнес атауы
• Егер анкета немесе қызмет болса — аты-жөніңіз (есіміңіз)

3️⃣ Негізгі ақпарат:
📃• Қысқаша сипаттама
💵• Айлық/баға
📊• График/шарттар (5/2, ауысым, қашықтан/офлайн т.б.)
⏰• Жұмыс уақыты (мысалы: 09:00–18:00)
📍• Мекенжай (қалауыңызша)
📞• Байланыс нөмірі (WhatsApp/қоңырау)
📷• Фото/логотип (бар болса)
💌• Әлеуметтік желілеріңіз (қалауыңызша): Instagram / TikTok / Telegram / сайт сілтемесі
📚• Қосымша (қалауыңызша): талаптар, тәжірибе, жас шектеуі, жолақы/тамақ/тұру, т.б.

❗️Мәліметті бір хабарламаға жинап жіберсеңіз, тезірек рәсімдейміз❗️
Көмек керек болса, @spiritz777 жазуыңызға болады.
"""

RU_GREETING = """💸 Тарифы и услуги

💡 Добавление объявления — БЕСПЛАТНО (до конца месяца)
В услугу входит:
• Приём и проверка информации
• Оформление объявления в нужном формате (заголовок, описание, зарплата/цена, теги)
• Публикация на сайте

🗓 Срок размещения: 30 дней (1 месяц)

📆 Продление на 1 месяц — 1500 ₸
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
• 7 дней — 2000 ₸
• 14 дней — 3000 ₸
• 30 дней — 5000 ₸

📌 Информация, которую нужно отправить для объявления

1️⃣ Тип: вакансия / анкета / услуга

2️⃣ Обязательно укажите❗️:
• Если вакансия — название компании/бизнеса
• Если анкета или услуга — ваше имя (ФИО/имя)

3️⃣ Основная информация:
📃• Краткое описание
💵• Зарплата/цена
📊• График/условия (5/2, смены, удалённо/офлайн и т.д.)
⏰• Время работы (например: 09:00–18:00)
📍• Адрес (по желанию)
📞• Контактный номер (WhatsApp/звонки)
📷• Фото/логотип (если есть)
💌• Ваши соцсети (по желанию): Instagram / TikTok / Telegram / ссылка на сайт
📚• Дополнительно (по желанию): требования, опыт, возрастные ограничения, проезд/питание/проживание и т.д.

❗️Если отправите всё одним сообщением, оформим быстрее❗️
Если нужна помощь, можете написать @spiritz777.
"""

# Лучше держать реквизиты в .env (чтобы не светить в GitHub):
# VIP_DETAILS_RU=...
# VIP_DETAILS_KZ=...
VIP_DETAILS_RU = os.getenv(
    "VIP_DETAILS_RU",
    "🔥 VIP-статус\n• 7 дней — 2000 ₸\n• 14 дней — 3000 ₸\n• 30 дней — 5000 ₸\n\nОплата: (заполни VIP_DETAILS_RU в .env)\n"
)
VIP_DETAILS_KZ = os.getenv(
    "VIP_DETAILS_KZ",
    "🔥 VIP мәртебесі\n• 7 күн — 2000 ₸\n• 14 күн — 3000 ₸\n• 30 күн — 5000 ₸\n\nТөлем: (.env ішіне VIP_DETAILS_KZ толтырыңыз)\n"
)

TEXTS = {
    "ru": LangText(
        greeting=RU_GREETING,
        help_text="Отправьте заявку сообщением (можно с фото/логотипом). Мы проверим и ответим.",
        submitted="Заявка отправлена. Ожидайте модерацию.",
        submitted_more="Дополнение к заявке отправлено. Ожидайте модерацию.",
        vip_offer="Хотите добавить VIP-статус? (поднимем объявление вверх и отметим TOP)",
        vip_details=VIP_DETAILS_RU,
        approved="Заявка принята. Мы проверим данные и добавим на сайт. Если потребуется уточнение — напишем.",
        rejected_prefix="Заявка отклонена. Причина:",
        need_info_prefix="Нужны уточнения по заявке:",
    ),
    "kz": LangText(
        greeting=KZ_GREETING,
        help_text="Өтінімді хабарлама ретінде жіберіңіз (фото/логотип болса қосуға болады). Тексеріп, жауап береміз.",
        submitted="Өтінім жіберілді. Модерацияны күтіңіз.",
        submitted_more="Өтінімге қосымша ақпарат жіберілді. Модерацияны күтіңіз.",
        vip_offer="VIP мәртебесін қосқыңыз келе ме? (хабарландыру жоғарыға шығып, TOP белгісі болады)",
        vip_details=VIP_DETAILS_KZ,
        approved="Өтінім қабылданды. Мәліметтерді тексеріп, сайтқа қосамыз. Қажет болса, нақтылау сұраймыз.",
        rejected_prefix="Өтінім қабылданбады. Себебі:",
        need_info_prefix="Өтінім бойынша қосымша ақпарат керек:",
    ),
}


# =========================
# Keyboards
# =========================
def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Қазақша", callback_data="lang:kz")],
            [InlineKeyboardButton(text="Русский", callback_data="lang:ru")],
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
            ],
        ]
    )


def vip_offer_kb(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"vip:yes:{ticket_id}"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"vip:no:{ticket_id}"),
            ]
        ]
    )


# =========================
# DB helpers
# =========================
@asynccontextmanager
async def db_conn():
    db = await aiosqlite.connect(DB_PATH)
    try:
        # Для устойчивости на телефоне
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA busy_timeout=5000;")
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    async with db_conn() as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                lang TEXT NOT NULL
            )
            """
        )
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
        # Антидубликат (chat_id + message_id)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_messages (
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, message_id)
            )
            """
        )

        # Мягкая миграция: добавим колонки, если их ещё нет
        for stmt in (
            "ALTER TABLE tickets ADD COLUMN vip_offered INTEGER DEFAULT 0",
            "ALTER TABLE tickets ADD COLUMN vip_choice TEXT DEFAULT NULL",   # yes/no
        ):
            try:
                await db.execute(stmt)
            except aiosqlite.OperationalError:
                # колонка уже существует
                pass

        await db.commit()


async def mark_message_processed(chat_id: int, message_id: int) -> bool:
    """True = обрабатываем впервые, False = уже было (защита от дублей)."""
    async with db_conn() as db:
        cur = await db.execute(
            "INSERT OR IGNORE INTO processed_messages(chat_id, message_id) VALUES(?, ?)",
            (chat_id, message_id),
        )
        await db.commit()
        return cur.rowcount == 1


async def set_user_lang(user_id: int, lang: str) -> None:
    async with db_conn() as db:
        await db.execute(
            """
            INSERT INTO users(user_id, lang) VALUES(?, ?)
            ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang
            """,
            (user_id, lang),
        )
        await db.commit()


async def get_user_lang(user_id: int) -> str | None:
    async with db_conn() as db:
        cur = await db.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else None


async def create_ticket(user_id: int, lang: str, admin_chat_id: int) -> int:
    async with db_conn() as db:
        cur = await db.execute(
            "INSERT INTO tickets(user_id, lang, status, admin_chat_id) VALUES(?, ?, ?, ?)",
            (user_id, lang, "new", admin_chat_id),
        )
        await db.commit()
        return cur.lastrowid


async def set_ticket_header(ticket_id: int, header_msg_id: int) -> None:
    async with db_conn() as db:
        await db.execute(
            "UPDATE tickets SET admin_header_msg_id=? WHERE id=?",
            (header_msg_id, ticket_id),
        )
        await db.commit()


async def update_ticket_status(ticket_id: int, status: str) -> None:
    async with db_conn() as db:
        await db.execute("UPDATE tickets SET status=? WHERE id=?", (status, ticket_id))
        await db.commit()


async def set_ticket_vip_offered(ticket_id: int) -> None:
    async with db_conn() as db:
        await db.execute("UPDATE tickets SET vip_offered=1 WHERE id=?", (ticket_id,))
        await db.commit()


async def set_ticket_vip_choice(ticket_id: int, choice: str) -> None:
    async with db_conn() as db:
        await db.execute("UPDATE tickets SET vip_choice=? WHERE id=?", (choice, ticket_id))
        await db.commit()


async def get_ticket(ticket_id: int) -> tuple[int, str, str, int, int | None, int, str | None] | None:
    # returns (user_id, lang, status, admin_chat_id, admin_header_msg_id, vip_offered, vip_choice)
    async with db_conn() as db:
        cur = await db.execute(
            """
            SELECT user_id, lang, status, admin_chat_id, admin_header_msg_id,
                   COALESCE(vip_offered, 0), vip_choice
            FROM tickets WHERE id=?
            """,
            (ticket_id,),
        )
        row = await cur.fetchone()
        return row if row else None


async def get_open_ticket_for_user(user_id: int, admin_chat_id: int) -> tuple[int, int | None, str] | None:
    """
    Вернёт (ticket_id, header_msg_id, lang) если есть активный тикет (new / need_info / waiting_admin_text).
    """
    async with db_conn() as db:
        cur = await db.execute(
            """
            SELECT id, admin_header_msg_id, lang
            FROM tickets
            WHERE user_id=? AND admin_chat_id=? AND status IN ('new', 'need_info', 'waiting_admin_text')
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id, admin_chat_id),
        )
        row = await cur.fetchone()
        return row if row else None


async def save_admin_prompt(prompt_msg_id: int, admin_chat_id: int, ticket_id: int, action: str) -> None:
    async with db_conn() as db:
        await db.execute(
            "INSERT OR REPLACE INTO admin_prompts(prompt_msg_id, admin_chat_id, ticket_id, action) VALUES(?, ?, ?, ?)",
            (prompt_msg_id, admin_chat_id, ticket_id, action),
        )
        await db.commit()


async def resolve_admin_prompt(prompt_msg_id: int, admin_chat_id: int) -> tuple[int, str] | None:
    async with db_conn() as db:
        cur = await db.execute(
            "SELECT ticket_id, action FROM admin_prompts WHERE prompt_msg_id=? AND admin_chat_id=?",
            (prompt_msg_id, admin_chat_id),
        )
        row = await cur.fetchone()
        return row if row else None


async def delete_admin_prompt(prompt_msg_id: int) -> None:
    async with db_conn() as db:
        await db.execute("DELETE FROM admin_prompts WHERE prompt_msg_id=?", (prompt_msg_id,))
        await db.commit()


# =========================
# Business helpers
# =========================
def build_admin_header(user: types.User, lang: str, ticket_id: int, vip_choice: str | None = None) -> str:
    username = f"@{user.username}" if user.username else "(no username)"
    vip_line = f"\nVIP: {vip_choice}" if vip_choice else "\nVIP: —"
    return (
        f"🆕 Заявка #{ticket_id}\n"
        f"User: {user.full_name}\n"
        f"ID: {user.id}\n"
        f"Lang: {lang}\n"
        f"Username: {username}"
        f"{vip_line}\n\n"
        f"Действия ниже:"
    )


# =========================
# Main
# =========================
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
        lang = await get_user_lang(message.from_user.id)
        if lang in TEXTS:
            await message.answer(TEXTS[lang].greeting)
        else:
            await message.answer("Тілді таңдаңыз / Выберите язык :", reply_markup=lang_keyboard())

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        if message.chat.type != "private":
            return
        lang = await get_user_lang(message.from_user.id) or "ru"
        await message.answer(TEXTS[lang].help_text)

    @dp.callback_query(F.data.startswith("lang:"))
    async def on_lang_choice(callback: types.CallbackQuery):
        try:
            await callback.answer()
        except TelegramBadRequest:
            pass

        lang = callback.data.split(":", 1)[1]
        if lang not in TEXTS:
            try:
                await callback.answer("Unknown language", show_alert=True)
            except TelegramBadRequest:
                pass
            return

        await set_user_lang(callback.from_user.id, lang)

        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass

        await callback.message.answer(TEXTS[lang].greeting)

    # Пользователь отправляет заявку в личке
    @dp.message(F.chat.type == "private")
    async def handle_user_message(message: types.Message):
        nonlocal admin_chat_id

        # команды не отправляем как заявки
        if message.text and message.text.startswith("/"):
            return

        if admin_chat_id == 0:
            await message.answer("Поддержка ещё не настроена (ADMIN_CHAT_ID=0).")
            return

        # Антидубликат: если Telegram отдал тот же апдейт повторно — игнорируем
        first = await mark_message_processed(message.chat.id, message.message_id)
        if not first:
            return

        lang = await get_user_lang(message.from_user.id) or "ru"

        # Если у пользователя уже есть активный тикет — не создаём новый, просто докидываем сообщение
        open_ticket = await get_open_ticket_for_user(message.from_user.id, admin_chat_id)
        if open_ticket:
            ticket_id, header_msg_id, t_lang = open_ticket
            # докидываем в админ-чат “в ответ” на шапку тикета (если она есть)
            try:
                await bot.copy_message(
                    chat_id=admin_chat_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                    reply_to_message_id=header_msg_id if header_msg_id else None,
                )
            except TelegramBadRequest:
                # если reply_to_message_id не подходит, просто отправим без reply
                await bot.copy_message(
                    chat_id=admin_chat_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                )

            await message.answer(TEXTS[lang].submitted_more)
            return

        # Создаём новый тикет
        ticket_id = await create_ticket(message.from_user.id, lang, admin_chat_id)

        header_text = build_admin_header(message.from_user, lang, ticket_id)
        header_msg = await bot.send_message(
            chat_id=admin_chat_id,
            text=header_text,
            reply_markup=admin_actions_kb(ticket_id),
        )
        await set_ticket_header(ticket_id, header_msg.message_id)

        await bot.copy_message(
            chat_id=admin_chat_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            reply_to_message_id=header_msg.message_id,
        )

        # Пользователь: подтверждение + VIP оффер (один раз на тикет)
        await message.answer(TEXTS[lang].submitted)
        await set_ticket_vip_offered(ticket_id)
        await message.answer(TEXTS[lang].vip_offer, reply_markup=vip_offer_kb(ticket_id))

    # VIP выбор пользователя
    @dp.callback_query(F.data.startswith("vip:"))
    async def on_vip_choice(callback: types.CallbackQuery):
        try:
            await callback.answer()
        except TelegramBadRequest:
            pass

        parts = callback.data.split(":")
        if len(parts) != 3:
            return

        choice = parts[1]  # yes/no
        ticket_id = int(parts[2])

        t = await get_ticket(ticket_id)
        if not t:
            return

        user_id, lang, status, t_admin_chat_id, header_msg_id, vip_offered, vip_choice = t

        # защита: кнопки может нажимать только тот пользователь, чей тикет
        if callback.from_user.id != user_id:
            try:
                await callback.answer("Это не ваша заявка.", show_alert=True)
            except TelegramBadRequest:
                pass
            return

        user_lang = await get_user_lang(callback.from_user.id) or lang or "ru"

        if choice == "yes":
            await set_ticket_vip_choice(ticket_id, "yes")
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass

            await callback.message.answer(TEXTS[user_lang].vip_details)

            # Уведомим админ-чат
            if t_admin_chat_id != 0:
                note = f"🔥 Пользователь по заявке #{ticket_id} хочет VIP."
                try:
                    await callback.bot.send_message(
                        chat_id=t_admin_chat_id,
                        text=note,
                        reply_to_message_id=header_msg_id if header_msg_id else None,
                    )
                except TelegramBadRequest:
                    await callback.bot.send_message(chat_id=t_admin_chat_id, text=note)
            return

        if choice == "no":
            await set_ticket_vip_choice(ticket_id, "no")
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass
            return

    # Нажатия админ-кнопок
    @dp.callback_query(F.data.startswith("a:"))
    async def on_admin_action(callback: types.CallbackQuery):
        # Сразу подтверждаем нажатие (иначе будет "query is too old")
        try:
            await callback.answer()
        except TelegramBadRequest:
            pass

        if admin_chat_id == 0:
            return
        if callback.message.chat.id != admin_chat_id:
            return

        parts = callback.data.split(":")
        if len(parts) != 3:
            return

        action = parts[1]
        ticket_id = int(parts[2])

        t = await get_ticket(ticket_id)
        if not t:
            return

        user_id, lang, status, t_admin_chat_id, header_msg_id, vip_offered, vip_choice = t
        if t_admin_chat_id != admin_chat_id:
            return

        # Принять
        if action == "ok":
            await update_ticket_status(ticket_id, "approved")

            try:
                await callback.message.edit_text(
                    callback.message.text + "\n\n✅ Статус: ПРИНЯТО",
                    reply_markup=None
                )
            except TelegramBadRequest:
                pass

            await bot.send_message(chat_id=user_id, text=TEXTS[lang].approved)
            return

        # Отклонить / Нужны данные — просим админа написать текст (reply)
        if action in ("rej", "need"):
            await update_ticket_status(ticket_id, "waiting_admin_text")

            prompt_text = (
                f"Ответьте (Reply) НА ЭТО сообщение текстом для пользователя.\n"
                f"Тикет #{ticket_id}\n"
                f"Действие: {'ОТКЛОНИТЬ' if action == 'rej' else 'НУЖНЫ ДАННЫЕ'}"
            )
            prompt_msg = await bot.send_message(
                chat_id=admin_chat_id,
                text=prompt_text,
                reply_to_message_id=callback.message.message_id,
            )
            await save_admin_prompt(prompt_msg.message_id, admin_chat_id, ticket_id, action)

            try:
                await callback.message.edit_text(
                    callback.message.text + "\n\n⏳ Статус: ОЖИДАЕТ ТЕКСТ ОТ АДМИНА",
                    reply_markup=None
                )
            except TelegramBadRequest:
                pass
            return

    # Админ пишет reply на prompt → бот отправляет юзеру
    @dp.message()
    async def on_admin_reply(message: types.Message):
        if admin_chat_id == 0:
            return
        if message.chat.id != admin_chat_id:
            return
        if not message.reply_to_message:
            return

        resolved = await resolve_admin_prompt(message.reply_to_message.message_id, admin_chat_id)
        if not resolved:
            return

        ticket_id, action = resolved
        t = await get_ticket(ticket_id)
        if not t:
            await delete_admin_prompt(message.reply_to_message.message_id)
            return

        user_id, lang, status, _, _, _, _ = t

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
        else:
            await message.reply("Неизвестное действие.")
            return

        await delete_admin_prompt(message.reply_to_message.message_id)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
