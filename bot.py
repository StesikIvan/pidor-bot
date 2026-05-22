import logging
import random
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
import os

from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ChatType

import database as db

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])
TIMEZONE = ZoneInfo("Europe/Moscow")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MAXIM_LINKS = [
    "https://t.me/Gutter999",
    "https://vk.com/zeiro666",
    "discord: gutter666",
]

INTRO_PHRASES = [
    "Просыпаюсь... 🌅",
    "Сейчас покруутим 🎰",
    "Хм, кто же сегодня...",
    "Запускаю алгоритм поиска 🔍",
    "Листаю списки участников... 📋",
    "Та-а-ак, посмотрим 👀",
    "Система анализирует... ⚙️",
    "Достаю карты таро 🃏",
    "Открываю книгу судеб 📖",
    "Спрашиваю у вселенной... 🌌",
]

BUILDUP_PHRASES = [
    "Выбор очевиден...",
    "Да кто бы сомневался 🙄",
    "Удивительно, но предсказуемо...",
    "Ну кто же ещё 🤭",
    "Звёзды сошлись, как обычно ⭐️",
    "Сюрприза не будет...",
    "Результат вас не удивит 😏",
    "Вселенная снова не подвела...",
    "Что ж, всё честно 🎲",
    "Барабаны не врут...",
]

RESULT_TEMPLATES = [
    "Сегодняшний пидор дня — @Gutter999! 🌈\n{link}",
    "Главный гейчик сегодня — @Gutter999 💅\n{link}",
    "Максон снова в деле! @Gutter999 🏆\n{link}",
    "Максимка, это снова ты! @Gutter999 😘\n{link}",
    "Максик не подвёл! @Gutter999 🌸\n{link}",
    "Корона пидора дня достаётся @Gutter999! 👑\n{link}",
    "Барабаны не врут — @Gutter999! 🥁\n{link}",
    "Сегодня главный гейчик Максон — @Gutter999 🎖\n{link}",
    "Снова он, снова @Gutter999! 🔁\n{link}",
    "Вселенная выбрала @Gutter999! ✨\n{link}",
    "Ну конечно же @Gutter999, кто бы сомневался 😂\n{link}",
    "Поздравляем Максика @Gutter999 с заслуженной наградой! 🎉\n{link}",
]

ALREADY_CHOSEN_PHRASES = [
    "Уже выбрали, не суетись! Сегодня гей — @Gutter999 🌈",
    "Максон уже получил корону сегодня 👑 @Gutter999",
    "Всё, вопрос закрыт. @Gutter999 — пидор дня 🔒",
    "Да-да, снова @Gutter999, расходимся 🚶",
    "Максик уже в курсе 😏 @Gutter999",
    "Пидор дня определён и это @Gutter999, ничего не изменится 💅",
    "Зачем переспрашивать, если и так ясно — @Gutter999 🤷",
    "Сегодняшний гейчик уже назначен: @Gutter999 🎖",
    "Максон уже несёт звание с честью сегодня @Gutter999 😂",
    "Повторно не считается, @Gutter999 всё равно пидор дня 🔁",
]


def mention(full_name: str, user_id: int) -> str:
    return f'<a href="tg://user?id={user_id}">{full_name}</a>'


def save_user(user):
    if user and not user.is_bot:
        db.upsert_user(
            chat_id=None,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
        )


def save_group_user(chat_id: int, user):
    if user and not user.is_bot:
        db.upsert_user(
            chat_id=chat_id,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
        )


# Track everyone who writes anything in the group
async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and update.effective_user:
        save_group_user(update.effective_chat.id, update.effective_user)


# Track members joining / being added to the group
async def track_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result: ChatMemberUpdated = update.chat_member
    if not result:
        return
    chat_id = result.chat.id
    new_member = result.new_chat_member
    if new_member and not new_member.user.is_bot:
        from telegram.constants import ChatMemberStatus
        if new_member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        ):
            save_group_user(chat_id, new_member.user)
            logger.info(f"Tracked new member {new_member.user.full_name} in {chat_id}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == ChatType.PRIVATE:
        if user.id == OWNER_ID:
            await update.message.reply_text(
                "Привет, хозяин! 👑\n\n"
                "Команды:\n"
                "/chats — список групп\n"
                "/listusers <code>chat_id</code> — участники\n"
                "/setchoice <code>chat_id user_id</code> — назначить пидора\n"
                "/clearchoice <code>chat_id</code> — сбросить\n"
                "/whosnext <code>chat_id</code> — кто следующий",
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text("Добавь меня в группу и вызови /pidor!")
    else:
        save_group_user(chat.id, user)
        await update.message.reply_text(
            "Привет! Я бот пидора дня 🌈\n\n"
            "/pidor — выбрать пидора дня\n"
            "/pidorstats — статистика за год\n"
            "/pidoralltimestats — статистика за всё время"
        )


async def cmd_pidor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await update.message.reply_text("Работает только в группах.")
        return

    save_group_user(chat.id, user)

    # Удаляем сообщение с командой
    try:
        await update.message.delete()
    except Exception:
        pass

    existing = db.get_today_result(chat.id)
    if existing:
        await context.bot.send_message(
            chat_id=chat.id,
            text=random.choice(ALREADY_CHOSEN_PHRASES),
        )
        return

    link = random.choice(MAXIM_LINKS)
    result = random.choice(RESULT_TEMPLATES).format(link=link)

    db.upsert_user(chat.id, 0, "Gutter999", "Максим")
    db.save_result(chat.id, 0, preset=False)

    await context.bot.send_message(chat_id=chat.id, text=random.choice(INTRO_PHRASES))
    await asyncio.sleep(2)
    await context.bot.send_message(chat_id=chat.id, text=random.choice(BUILDUP_PHRASES))
    await asyncio.sleep(2)
    await context.bot.send_message(chat_id=chat.id, text=result)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return
    year = datetime.now(TIMEZONE).year
    rows = db.get_stats(chat.id, year=year)
    if not rows:
        await update.message.reply_text(f"Статистики за {year} год нет.")
        return
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"📊 <b>Статистика пидоров {year} года:</b>\n"]
    for i, row in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = row["full_name"] + (f" (@{row['username']})" if row["username"] else "")
        lines.append(f"{medal} {name} — <b>{row['cnt']}</b> раз(а)")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_alltime_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return
    rows = db.get_stats(chat.id)
    if not rows:
        await update.message.reply_text("Статистики пока нет.")
        return
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Статистика пидоров за всё время:</b>\n"]
    for i, row in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = row["full_name"] + (f" (@{row['username']})" if row["username"] else "")
        lines.append(f"{medal} {name} — <b>{row['cnt']}</b> раз(а)")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


# ── Owner-only private commands ────────────────────────────────────────────────

def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != OWNER_ID:
            return
        if update.effective_chat.type != ChatType.PRIVATE:
            return
        await func(update, context)
    return wrapper


@owner_only
async def cmd_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_ids = db.get_chats_with_users()
    if not chat_ids:
        await update.message.reply_text("Бот ещё ни в каких группах не работал.")
        return
    lines = ["<b>Группы:</b>\n"]
    for cid in chat_ids:
        lines.append(f"• <code>{cid}</code> — {len(db.get_users(cid))} игроков")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


@owner_only
async def cmd_listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Использование: /listusers <code>chat_id</code>", parse_mode="HTML")
        return
    try:
        chat_id = int(args[0])
    except ValueError:
        await update.message.reply_text("chat_id должен быть числом.")
        return
    users = db.get_users(chat_id)
    if not users:
        await update.message.reply_text("Нет участников.")
        return
    lines = [f"<b>Игроки в {chat_id}:</b>\n"]
    for u in users:
        uname = f" @{u['username']}" if u["username"] else ""
        lines.append(f"• <b>{u['full_name']}</b>{uname} — <code>{u['user_id']}</code>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


@owner_only
async def cmd_setchoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Использование: /setchoice <code>chat_id user_id</code>", parse_mode="HTML"
        )
        return
    try:
        chat_id, user_id = int(args[0]), int(args[1])
    except ValueError:
        await update.message.reply_text("Нужны числа.")
        return
    users = db.get_users(chat_id)
    target = next((u for u in users if u["user_id"] == user_id), None)
    if not target:
        await update.message.reply_text("Пользователь не найден в этой группе.")
        return
    if db.get_today_result(chat_id):
        await update.message.reply_text("⚠️ Сегодня уже выбран. Сработает завтра.")
    db.set_preset(chat_id, user_id)
    await update.message.reply_text(
        f"✅ Следующий пидор дня — <b>{target['full_name']}</b>", parse_mode="HTML"
    )


@owner_only
async def cmd_clearchoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Использование: /clearchoice <code>chat_id</code>", parse_mode="HTML")
        return
    try:
        chat_id = int(args[0])
    except ValueError:
        await update.message.reply_text("chat_id должен быть числом.")
        return
    db.clear_preset(chat_id)
    await update.message.reply_text("✅ Предустановка сброшена.")


@owner_only
async def cmd_whosnext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Использование: /whosnext <code>chat_id</code>", parse_mode="HTML")
        return
    try:
        chat_id = int(args[0])
    except ValueError:
        await update.message.reply_text("chat_id должен быть числом.")
        return
    preset_id = db.get_preset(chat_id)
    if not preset_id:
        await update.message.reply_text("Предустановки нет — будет случайный выбор.")
        return
    users = db.get_users(chat_id)
    target = next((u for u in users if u["user_id"] == preset_id), None)
    name = target["full_name"] if target else str(preset_id)
    await update.message.reply_text(
        f"Следующий пидор дня: <b>{name}</b>", parse_mode="HTML"
    )


async def log_all_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"UPDATE RECEIVED: {update}")


async def reset_daily(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Daily reset: clearing today's pidor results.")
    db.clear_today_results()


def main():
    db.init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Сброс пидора дня каждый день в 00:00 по Москве
    app.job_queue.run_daily(
        reset_daily,
        time=datetime.strptime("00:00", "%H:%M").replace(tzinfo=TIMEZONE).timetz(),
    )

    # Commands — group 0, handled first
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("pidor", cmd_pidor))
    app.add_handler(CommandHandler("pidorstats", cmd_stats))
    app.add_handler(CommandHandler("pidoralltimestats", cmd_alltime_stats))

    # Owner private commands — group 0
    app.add_handler(CommandHandler("chats", cmd_chats))
    app.add_handler(CommandHandler("listusers", cmd_listusers))
    app.add_handler(CommandHandler("setchoice", cmd_setchoice))
    app.add_handler(CommandHandler("clearchoice", cmd_clearchoice))
    app.add_handler(CommandHandler("whosnext", cmd_whosnext))

    # Track member joins — group 0
    app.add_handler(ChatMemberHandler(track_chat_member, ChatMemberHandler.CHAT_MEMBER))

    # Auto-track every message sender — group 1 (runs after commands)
    app.add_handler(
        MessageHandler(filters.ChatType.GROUPS & filters.ALL, track_message), group=1
    )

    logger.info("Bot started.")

    if os.environ.get("PORT"):
        # На Render — запускаем Flask health-check в фоне, бот через polling
        import threading
        from flask import Flask as _Flask
        flask_app = _Flask(__name__)

        @flask_app.route("/")
        def health():
            return "OK", 200

        t = threading.Thread(
            target=lambda: flask_app.run(
                host="0.0.0.0",
                port=int(os.environ["PORT"]),
                use_reloader=False,
            ),
            daemon=True,
        )
        t.start()
        logger.info(f"Health-check server started on port {os.environ['PORT']}")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
