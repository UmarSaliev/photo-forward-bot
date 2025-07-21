import os
import logging
import httpx
from dotenv import load_dotenv
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# === Загрузка переменных окружения ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = set(map(int, os.getenv("OWNER_IDS", "").split(",")))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# === Логгирование ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === AI через OpenRouter ===
async def ask_openrouter(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourdomain.com",  # Укажи свой домен/TelegramBot ссылку
        "X-Title": "MathBot",
    }
    payload = {
        "model": "gryphe/mythomist-7b",
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Ошибка при запросе к AI: {e}")
        return "⚠️ Произошла ошибка при обращении к AI."

# === Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я AI-бот для математики. Используй команды:\n"
        "/check /task /definition /formula /theorem или просто задай вопрос."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧮 Команды:\n"
        "/check — Проверка примера\n"
        "/task — Помощь с задачей\n"
        "/definition — Определение термина\n"
        "/formula — Формула\n"
        "/theorem — Теорема\n"
        "/ping — Проверка ответа\n"
        "/status — Статус бота\n"
        "/list — Только для владельцев"
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает.")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in OWNER_IDS:
        await update.message.reply_text("🔐 Владелец подтвержден. Доступ открыт.")
    else:
        await update.message.reply_text("⛔ Команда только для владельцев.")

# === Обработка текста ===
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text.startswith(("/check", "/task", "/definition", "/formula", "/theorem")):
        command, *rest = text.split(maxsplit=1)
        prompt = rest[0] if rest else "Поясни подробнее."
        query = f"{command[1:]}: {prompt}"
    else:
        query = text

    response = await ask_openrouter(query)
    await update.message.reply_text(response)

# === Обработка фото ===
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in OWNER_IDS and update.message.caption and update.message.caption.startswith("/check"):
        await update.message.reply_text("⛔ Владелец не может проверять свои собственные фото.")
        return

    await update.message.reply_text("🖼️ Фото получено, но пока я понимаю только текст.")

# === Запуск приложения ===
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("list", list_command))

    # Сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("🤖 Бот запущен...")
    await app.run_polling()

# === Запуск ===
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
