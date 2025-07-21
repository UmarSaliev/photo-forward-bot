import logging
import os
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = list(map(int, os.getenv("OWNER_IDS", "").split(","))) if os.getenv("OWNER_IDS") else []
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_USERNAME = "@JalilSupportBot"  # Замените на реальный юзернейм бота (например, "@MathTeacherBot")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Основные функции ---
async def ask_ai(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": f"https://t.me/{BOT_USERNAME[1:]}",
        "X-Title": "MathHelperBot"
    }
    json_data = {
        "model": "openrouter/meta-llama/llama-3-8b-instruct:free",
        "messages": [{"role": "user", "content": prompt}]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=json_data,
            timeout=aiohttp.ClientTimeout(total=15) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я бот-помощник по математике. Задайте вопрос или отправьте фото.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные команды:\n"
        "/task - Решить задачу\n"
        "/formula - Получить формулу\n"
        "/theorem - Теорема\n"
        "/search - Поиск по фото\n"
    )
    if update.effective_user.id in OWNER_IDS:
        help_text += "\nКоманды для учителя:\n/broadcast - Рассылка\n/list - Список учеников"
    await update.message.reply_text(help_text)

# --- Обработчики сообщений ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    prompt = update.message.text
    try:
        response = await ask_ai(prompt)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Ошибка в handle_text: {e}")
        await update.message.reply_text("⚠️ Ошибка: не удалось обработать запрос.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_IDS:
        photo = update.message.photo[-1].file_id
        caption = f"📸 Фото от пользователя: {update.message.from_user.username or update.message.from_user.id}"
        for owner_id in OWNER_IDS:
            await context.bot.send_photo(chat_id=owner_id, photo=photo, caption=caption)
        await update.message.reply_text("📤 Фото отправлено учителю!")
    else:
        await update.message.reply_text("❌ Нет доступных получателей.")

# --- Запуск ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    # ... остальные команды ...

    # Обработчики сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))

    # Обработчик ошибок
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Ошибка: {context.error}")
    
    app.add_error_handler(error_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
