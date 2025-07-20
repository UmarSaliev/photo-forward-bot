import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Читаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS_ENV = os.getenv("OWNER_IDS", "")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не задан в переменных окружения!")
    exit(1)

OWNER_IDS = [int(x) for x in OWNER_IDS_ENV.split(",") if x.strip().isdigit()]

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я главный помощник мистера Абдужалила 🤓. Ты можешь пересыласть мне задачи с которыми у тебя возникли проблемы и я передам их ему 🚀. Пожалуйста при отправке четко выдели саму задачу или пример и постарайся обьяснить в чем ты запутался 💯.")

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — начать работу 💻\n"
        "/help — основные команды 📖\n"
        "/ping — проверить связь с хостом 🌐\n"
        "/status — статус активности бота 🤖\n"
        "/list — список учеников отправивших задания 🤓(доступен только учителю)\n"
        "/broadcast — рассылка сообщений ✈️(доступен только учителю)"
    )

# /ping
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я здесь, не беспокойся и всегда готов помочь.")

# /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает исправно.")

# /list (только для владельцев)
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return
    # Здесь можно выгружать реальные данные
    await update.message.reply_text("📋 Список учеников: ...")

# /broadcast текст (только для владельцев)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("⚠️ Используйте: /broadcast ваш текст")
        return
    # Здесь должна быть логика отправки всем user_ids
    await update.message.reply_text("✅ Сообщение отправлено.")

# Обработка фото (если нужно)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📷 Спасибо за фото!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем хендлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("🚀 Бот запущен!")
    app.run_polling()  # Блокирует и запускает свой цикл событий

if __name__ == "__main__":
    main()
