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
    await update.message.reply_text("👋 Привет! Я Telegram‑бот. Введите /help для списка команд.")

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — начать работу\n"
        "/help — справка\n"
        "/ping — проверить связь\n"
        "/status — статус бота\n"
        "/list — список (только владельцам)\n"
        "/broadcast — рассылка (только владельцам)"
    )

# /ping
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

# /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает нормально.")

# /list (только для владельцев)
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return
    # Здесь можно выгружать реальные данные
    await update.message.reply_text("📋 Список пользователей: ...")

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
    await update.message.reply_text("✅ Рассылка отправлена.")

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
