import logging
import os
import httpx
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters
)

# Конфигурация
TOKEN       = os.getenv("BOT_TOKEN")
OWNER_IDS   = [int(uid) for uid in os.getenv("OWNER_IDS", "").split(",") if uid]
OR_API_KEY  = os.getenv("OPENROUTER_API_KEY")
MODEL       = "openrouter/mistralai/mixtral-8x7b"
students    = set()

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AI-запрос
async def ai_response(prompt: str) -> str:
    url     = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OR_API_KEY}"}
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=headers, json=payload)
            body = r.text  # Исправлено здесь
            if r.status_code != 200:
                logger.error("OpenRouter %s → %s", r.status_code, body)
                return f"⚠️ Ошибка AI: код {r.status_code}\n\n{body}"
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception("AI request failed")
        return f"⚠️ Ошибка AI: {e}"

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я главный помощник мистера Абдужалила 🤓. "
        "Ты можешь пересылать мне задачи, с которыми у тебя возникли проблемы, и я передам их ему 🚀. "
        "Пожалуйста, при отправке четко выдели саму задачу и постарайся объяснить, в чем ты запутался 💯.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 *Доступные команды:*\n\n"
        "/start — начать работу\n"
        "/help — показать команды\n"
        "/ping — проверить связь\n"
        "/status — статус бота\n"
        "/list — список учеников (только учителю)\n"
        "/broadcast — рассылка (только учителю)\n"
        "/task <тема> — сгенерировать задачу\n"
        "/definition <тема> — дать определение\n"
        "/formula <тема> — выдать формулу\n"
        "/theorem <название> — объяснить теорему\n"
        "/check <задача> — решить задачу"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот активен.")

async def list_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("❌ Доступ запрещён.")
    if not students:
        return await update.message.reply_text("Пока никто не отправлял задания.")
    await update.message.reply_text("👨‍🎓 Ученики:\n" + "\n".join(map(str, students)))

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("❌ Доступ запрещён.")
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("✏️ Укажи текст после /broadcast")
    sent = 0
    for uid in students:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ Отправлено {sent} пользователям.")

# Генератор AI‑обработчиков
def make_ai_handler(prefix: str):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = " ".join(context.args)
        if not query:
            return await update.message.reply_text(f"📥 Укажи тему после /{prefix}")
        students.add(update.effective_user.id)
        prompt = f"{prefix.capitalize()} по теме '{query}' простыми словами."
        res = await ai_response(prompt)
        await update.message.reply_text(res)
    return handler

check      = make_ai_handler("реши задачу")
definition = make_ai_handler("дай определение")
formula    = make_ai_handler("выведи формулу")
theorem    = make_ai_handler("объясни теорему")
task       = make_ai_handler("сгенерируй задачу")

# Обработка фотографий: пересылаем учителю
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    students.add(update.effective_user.id)
    for oid in OWNER_IDS:
        await context.bot.forward_message(
            chat_id=oid,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    await update.message.reply_text("📨 Фото отправлено учителю.")

# Запуск
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("list", list_students))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("definition", definition))
    app.add_handler(CommandHandler("formula", formula))
    app.add_handler(CommandHandler("theorem", theorem))
    app.add_handler(CommandHandler("task", task))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()
