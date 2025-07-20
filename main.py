import logging
import os
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем переменные окружения
BOT_TOKEN = os.getenv("8189283086:AAGR_QF2NuupIZA4G_Fhys_81CU-9-BOWaU")
OWNER_IDS = os.getenv("95293299,784341697")

# Проверка наличия токена
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не задан в переменных окружения!")
    exit(1)

# Преобразуем OWNER_IDS в список чисел
if OWNER_IDS:
    OWNER_IDS = [int(x.strip()) for x in OWNER_IDS.split(",")]
else:
    OWNER_IDS = []

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я Telegram-бот.")

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — начать работу\n"
        "/help — помощь\n"
        "/ping — проверить связь\n"
        "/status — статус бота\n"
        "/list — список (только для владельцев)"
    )

# Команда /ping
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

# Команда /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает нормально.")

# Команда /list (только для владельцев)
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in OWNER_IDS:
        await update.message.reply_text("📋 Вот ваш список (пример данных).")
    else:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")

# Запуск бота
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("list", list_command))

    logger.info("✅ Бот запущен...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
