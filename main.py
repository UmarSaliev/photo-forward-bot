import os
import logging
import asyncio
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен и ID владельцев из переменных окружения
BOT_TOKEN = os.getenv("8189283086:AAGR_QF2NuupIZA4G_Fhys_81CU-9-BOWaU")
OWNER_IDS = [int(uid) for uid in os.getenv("95293299", "784341697").split(",") if uid.strip().isdigit()]

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я математический бот.\nНапиши /help, чтобы увидеть доступные команды.")

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Список команд:\n"
        "/start — начать работу\n"
        "/help — справка\n"
        "/ping — проверить онлайн\n"
        "/status — статус бота\n"
        "/list — список чего-либо (доступно только владельцам)"
    )

# Команда /ping
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает!")

# Команда /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Всё в порядке. Бот запущен.")

# Команда /list (только для владельцев)
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in OWNER_IDS:
        await update.message.reply_text("📋 Вот ваш список: ...")
    else:
        await update.message.reply_text("🚫 У вас нет доступа к этой команде.")

# Ответ на фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📷 Спасибо за фото!")

# Основная функция запуска
async def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан в переменных окружения!")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Установка команд для меню Telegram
    await application.bot.set_my_commands([
        BotCommand("start", "Начать работу"),
        BotCommand("help", "Справка по боту"),
        BotCommand("ping", "Проверить онлайн"),
        BotCommand("status", "Показать статус"),
        BotCommand("list", "Список (только для владельцев)"),
    ])

    # Запуск
    logger.info("🚀 Бот запущен!")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
