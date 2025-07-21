import logging
import os
import httpx
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters
)

# Конфигурация
TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = [int(uid) for uid in os.getenv("OWNER_IDS", "").split(",") if uid]
OR_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openrouter/mistralai/mixtral-8x7b"

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище пользователей
students = set()

# Универсальный AI-запрос
async def ai_response(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OR_API_KEY}",
        "HTTP-Referer": "https://t.me/YOUR_BOT_USERNAME",
        "X-Title": "MathBot"
    }
    json_data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"AI error: {e}")
        return f"⚠️ Ошибка AI: {e}"

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я главный помощник мистера Абдужалила 🤓. "
        "Ты можешь пересылать мне задачи, с которыми у тебя возникли проблемы, и я передам их ему 🚀. "
        "Пожалуйста, при отправке четко выдели саму задачу и постарайся объяснить, в чем ты запутался 💯."
    )

# Хелп
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📚 *Доступные команды:*

/start — начать работу 💻
/help — основные команды 📖
/ping — проверить связь с хостом 🌐
/status — статус активности бота 🤖
/list — список учеников (только для учителя) 🤓
/broadcast — рассылка сообщений ✈️ (только для учителя)
/task <тема> — сгенерировать задачу 📌
/definition <тема> — дать определение 📘
/formula <тема> — выдать формулу 📐
/theorem <название> — объяснить теорему 📏
/check <задача> — решить задачу ✍️
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

# Прочие команды
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong! Бот работает.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот активен и готов к работе.")

async def list_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("❌ У вас нет доступа к этой команде.")

    if not students:
        return await update.message.reply_text("Пока никто не отправлял задания.")

    names = [str(uid) for uid in students]
    await update.message.reply_text("👨‍🎓 Ученики отправившие задания:\n" + "\n".join(names))

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("❌ У вас нет доступа к этой команде.")

    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("✏️ Укажите текст рассылки после команды.")

    count = 0
    for uid in students:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            count += 1
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {uid}: {e}")

    await update.message.reply_text(f"✅ Сообщение отправлено {count} пользователям.")

# Генерация обработчиков AI-команд
def make_ai_handler(prefix: str):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = " ".join(context.args)
        if not query:
            await update.message.reply_text(f"📥 Укажи тему после команды. Например: /{prefix} производная")
            return

        students.add(update.effective_user.id)
        prompt = f"{prefix.capitalize()} по теме '{query}' простыми словами для школьника."
        result = await ai_response(prompt)
        await update.message.reply_text(result)
    return handler

# Обработчики
check = make_ai_handler("Реши задачу")
definition = make_ai_handler("Дай определение")
formula = make_ai_handler("Выведи формулу")
theorem = make_ai_handler("Объясни теорему")
task = make_ai_handler("Сгенерируй задачу")

# Запуск
if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("list", list_students))
    application.add_handler(CommandHandler("broadcast", broadcast))

    application.add_handler(CommandHandler("check", check))
    application.add_handler(CommandHandler("definition", definition))
    application.add_handler(CommandHandler("formula", formula))
    application.add_handler(CommandHandler("theorem", theorem))
    application.add_handler(CommandHandler("task", task))

    application.run_polling()
