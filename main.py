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
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.default import DefaultBotProperties # <--- ВАЖНОЕ ИЗМЕНЕНИЕ

load_dotenv()
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
DB_PATH = "bot.db"
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

if not BOT_TOKEN:
    exit("Error: BOT_TOKEN not found in .env")

# --- ТЕКСТЫ И НАСТРОЙКИ ---
@dataclass(frozen=True)
class LangText:
    greeting: str
    help_text: str
    submitted: str
    vip_offer: str
    vip_details: str
    approved: str
    rejected_prefix: str
    need_info_prefix: str
    banned_msg: str

KZ_GREETING = """💸 <b>Тарифтер және қызметтер</b>

💡Хабарландыру қосу — ТЕГІН (айдың соңына дейін)
• Мәліметтерді қабылдау және тексеру
• Сайтқа жариялау

🗓 Жариялану мерзімі: 30 күн
"""

RU_GREETING = """💸 <b>Тарифы и услуги</b>

💡 Добавление объявления — БЕСПЛАТНО (до конца месяца)
• Приём и проверка информации
• Публикация на сайте

🗓 Срок размещения: 30 дней
"""

VIP_DETAILS_RU = "🔥 <b>VIP-статус</b>\nРеквизиты: ..."
VIP_DETAILS_KZ = "🔥 <b>VIP мәртебесі</b>\nТөлем деректемелері: ..."

TEXTS = {
    "ru": LangText(
        greeting=RU_GREETING,
        help_text="✉️ Отправьте вашу заявку или вопрос сообщением.",
        submitted="✅ <b>Заявка отправлена.</b> Ожидайте проверку.",
        vip_offer="🚀 Хотите добавить VIP-статус?",
        vip_details=VIP_DETAILS_RU,
        approved="🎉 <b>Заявка принята!</b> Скоро она появится на канале.",
        rejected_prefix="❌ <b>Заявка отклонена.</b> Причина:",
        need_info_prefix="📝 <b>Нужны уточнения:</b>",
        banned_msg="⛔️ Вы заблокированы в этом боте."
    ),
    "kz": LangText(
        greeting=KZ_GREETING,
        help_text="✉️ Өтініміңізді хабарлама ретінде жіберіңіз.",
        submitted="✅ <b>Өтінім жіберілді.</b> Тексеруді күтіңіз.",
        vip_offer="🚀 VIP мәртебесін қосқыңыз келе ме?",
        vip_details=VIP_DETAILS_KZ,
        approved="🎉 <b>Өтінім қабылданды!</b>",
        rejected_prefix="❌ <b>Өтінім қабылданбады.</b> Себебі:",
        need_info_prefix="📝 <b>Қосымша ақпарат қажет:</b>",
        banned_msg="⛔️ Сіз бұғатталдыңыз."
    ),
}

# --- КЛАВИАТУРЫ ---
def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang:kz"),
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")]
    ])

def admin_actions_kb(ticket_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"a:ok:{ticket_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"a:rej:{ticket_id}"),
        ],
        [
            InlineKeyboardButton(text="📝 Запросить инфо", callback_data=f"a:need:{ticket_id}"),
        ],
        [
            InlineKeyboardButton(text="⛔️ БАН ЮЗЕРА", callback_data=f"ban:{user_id}:{ticket_id}")
        ]
    ])

def vip_offer_kb(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, хочу VIP", callback_data=f"vip:yes:{ticket_id}"),
            InlineKeyboardButton(text="❌ Нет, спасибо", callback_data=f"vip:no:{ticket_id}"),
        ]
    ])

# --- БАЗА ДАННЫХ (Helpers) ---
async def db_exec(sql: str, params: tuple = ()):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(sql, params)
        await db.commit()

async def db_fetch(sql: str, params: tuple = ()):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(sql, params)
        return await cur.fetchone()

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                lang TEXT NOT NULL,
                is_banned INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lang TEXT NOT NULL,
                status TEXT NOT NULL,
                admin_chat_id INTEGER NOT NULL,
                admin_header_msg_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS message_map (
                admin_msg_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_prompts (
                prompt_msg_id INTEGER PRIMARY KEY,
                admin_chat_id INTEGER NOT NULL,
                ticket_id INTEGER NOT NULL,
                action TEXT NOT NULL
            )
        """)
        await db.commit()

# --- ЛОГИКА ---

async def main():
    await init_db()
    
    # ВОТ ЗДЕСЬ БЫЛА ОШИБКА, ТЕПЕРЬ ИСПРАВЛЕНО:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        if message.chat.type == "private":
            await message.answer("👋 Тілді таңдаңыз / Выберите язык:", reply_markup=lang_keyboard())
        elif message.chat.id == ADMIN_CHAT_ID:
            await message.answer("🤖 Бот админ-панели активен.")

    @dp.callback_query(F.data.startswith("lang:"))
    async def on_lang(cb: types.CallbackQuery):
        lang = cb.data.split(":")[1]
        await db_exec("INSERT INTO users(user_id, lang) VALUES(?, ?) ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang", (cb.from_user.id, lang))
        await cb.message.edit_reply_markup(reply_markup=None)
        await cb.message.answer(TEXTS[lang].greeting)
        await cb.answer()

    # АДМИН: Ответ на сообщения
    @dp.message(F.chat.id == ADMIN_CHAT_ID, F.reply_to_message)
    async def admin_reply_handler(message: types.Message):
        prompt_data = await db_fetch("SELECT ticket_id, action FROM admin_prompts WHERE prompt_msg_id=?", (message.reply_to_message.message_id,))
        
        if prompt_data:
            ticket_id, action = prompt_data
            t_data = await db_fetch("SELECT user_id, lang FROM tickets WHERE id=?", (ticket_id,))
            if not t_data:
                await message.reply("⚠️ Тикет не найден.")
                return

            user_id, lang = t_data
            text_prefix = TEXTS[lang].rejected_prefix if action == "rej" else TEXTS[lang].need_info_prefix
            full_text = f"{text_prefix}\n\n{message.text or '...'}"

            try:
                await bot.send_message(user_id, full_text)
                await message.react([types.ReactionTypeEmoji(emoji="👌")])
                await message.reply(f"✅ Ответ отправлен пользователю (Тикет #{ticket_id})")
                
                new_status = "rejected" if action == "rej" else "need_info"
                await db_exec("UPDATE tickets SET status=? WHERE id=?", (new_status, ticket_id))
                await db_exec("DELETE FROM admin_prompts WHERE prompt_msg_id=?", (message.reply_to_message.message_id,))
            except Exception as e:
                await message.reply(f"❌ Не удалось отправить:\n{e}")
            return

        target_user_id = await db_fetch("SELECT user_id FROM message_map WHERE admin_msg_id=?", (message.reply_to_message.message_id,))
        
        if target_user_id:
            user_id = target_user_id[0]
            try:
                await message.copy_to(chat_id=user_id)
                await message.react([types.ReactionTypeEmoji(emoji="👍")])
            except TelegramBadRequest:
                await message.reply("❌ Пользователь заблокировал бота.")
            except Exception as e:
                await message.reply(f"❌ Ошибка отправки: {e}")

    # ЮЗЕР: Отправка сообщения
    @dp.message(F.chat.type == "private")
    async def user_msg_handler(message: types.Message):
        if message.text and message.text.startswith("/"): return

        user_id = message.from_user.id
        
        user_row = await db_fetch("SELECT lang, is_banned FROM users WHERE user_id=?", (user_id,))
        lang = user_row[0] if user_row else "ru"
        is_banned = user_row[1] if user_row else 0

        if is_banned:
            await message.answer(TEXTS[lang].banned_msg)
            return

        cur = await aiosqlite.connect(DB_PATH)
        async with cur as db:
            await db.execute("INSERT INTO tickets(user_id, lang, status, admin_chat_id) VALUES(?, ?, ?, ?)", (user_id, lang, "new", ADMIN_CHAT_ID))
            await db.commit()
            ticket_id = cur.lastrowid

        safe_name = html.escape(message.from_user.full_name)
        username = message.from_user.username
        user_link = f"<a href='tg://user?id={user_id}'>{safe_name}</a>"
        if username:
            user_link += f" (@{username})"
        
        header_text = (
            f"🆕 <b>Заявка #{ticket_id}</b>\n"
            f"👤 От: {user_link}\n"
            f"🌍 Язык: {lang.upper()}\n"
            f"🆔 ID: <code>{user_id}</code>"
        )

        try:
            await bot.send_message(ADMIN_CHAT_ID, header_text, reply_markup=admin_actions_kb(ticket_id, user_id))
            forwarded_msg = await message.forward(chat_id=ADMIN_CHAT_ID)
            await db_exec("INSERT INTO message_map (admin_msg_id, user_id) VALUES (?, ?)", (forwarded_msg.message_id, user_id))
            
            await message.answer(TEXTS[lang].submitted)
            await message.answer(TEXTS[lang].vip_offer, reply_markup=vip_offer_kb(ticket_id))
            
        except Exception as e:
            logging.error(f"Error in user_msg_handler: {e}")

    # КНОПКИ
    @dp.callback_query(F.data.startswith("a:"))
    async def admin_actions(cb: types.CallbackQuery):
        parts = cb.data.split(":")
        action = parts[1]
        ticket_id = int(parts[2])

        t_data = await db_fetch("SELECT user_id, lang FROM tickets WHERE id=?", (ticket_id,))
        if not t_data:
            await cb.answer("Тикет устарел", show_alert=True)
            return
        
        user_id, lang = t_data

        if action == "ok":
            await db_exec("UPDATE tickets SET status='approved' WHERE id=?", (ticket_id,))
            try:
                await bot.send_message(user_id, TEXTS[lang].approved)
                await cb.message.edit_text(cb.message.html_text + "\n\n✅ <b>СТАТУС: ПРИНЯТО</b>", reply_markup=None)
            except Exception:
                pass
        elif action in ("rej", "need"):
            action_text = "ОТКЛОНИТЬ" if action == "rej" else "ЗАПРОСИТЬ ИНФО"
            prompt_msg = await cb.message.reply(f"⌨️ <b>Введите текст для действия: {action_text}</b>\nОтветьте (Reply) на это сообщение.")
            await db_exec("INSERT OR REPLACE INTO admin_prompts (prompt_msg_id, admin_chat_id, ticket_id, action) VALUES(?,?,?,?)", (prompt_msg.message_id, ADMIN_CHAT_ID, ticket_id, action))
            await cb.message.edit_text(cb.message.html_text + f"\n\n⏳ <b>ОЖИДАНИЕ ТЕКСТА ({action_text})</b>", reply_markup=None)
            await cb.answer("Жду текст (Reply)")

    @dp.callback_query(F.data.startswith("ban:"))
    async def admin_ban_user(cb: types.CallbackQuery):
        _, target_user_id, ticket_id = cb.data.split(":")
        target_user_id = int(target_user_id)
        row = await db_fetch("SELECT is_banned FROM users WHERE user_id=?", (target_user_id,))
        is_now_banned = row[0] if row else 0

        if is_now_banned:
            await db_exec("UPDATE users SET is_banned=0 WHERE user_id=?", (target_user_id,))
            await cb.answer("Пользователь РАЗБАНЕН ✅")
            await cb.bot.send_message(ADMIN_CHAT_ID, f"User {target_user_id} разбанен.")
        else:
            await db_exec("UPDATE users SET is_banned=1 WHERE user_id=?", (target_user_id,))
            await cb.answer("Пользователь ЗАБАНЕН ⛔️")
            await cb.bot.send_message(ADMIN_CHAT_ID, f"User {target_user_id} забанен!")
            try:
                await cb.message.edit_reply_markup(reply_markup=None)
            except:
                pass

    @dp.callback_query(F.data.startswith("vip:"))
    async def vip_user_choice(cb: types.CallbackQuery):
        _, choice, t_id = cb.data.split(":")
        lang = await db_fetch("SELECT lang FROM users WHERE user_id=?", (cb.from_user.id,))
        lang = lang[0] if lang else "ru"

        if choice == "yes":
            await cb.message.edit_text(TEXTS[lang].vip_details, parse_mode="HTML")
            await bot.send_message(ADMIN_CHAT_ID, f"🤑 <b>Юзер по тикету #{t_id} хочет VIP!</b>", reply_to_message_id=None)
        else:
            await cb.message.delete()
        await cb.answer()

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
