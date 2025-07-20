import logging
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Читаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS_ENV = os.getenv("OWNER_IDS", "")

# Проверяем токен
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не задан в переменных окружения!")
    exit(1)

# Преобразуем строку OWNER_IDS в список int
OWNER_IDS = [int(x) for x in OWNER_IDS_ENV.split(",") if x.strip().isdigit()]

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я Telegram-бот. Введите /help для списка команд.")

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — начать работу\n"
        "/help — помощь\n"
        "/ping — проверить связь\n"
        "/status — статус бота\n"
        "/list — список (только для владельцев)\n"
        "/broadcast — рассылка (только для владельцев)"
    )

# Команда /ping
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

# Команда /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает нормально.")

# Команда /list (только владельцам)
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return
    # Здесь можно вывести реальные данные
    await update.message.reply_text("📋 Список пользователей: (здесь будет список)")

# Команда /broadcast <текст> (только владельцам)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("⚠️ Укажите текст после команды. Пример: /broadcast Привет всем!")
        return
    # Разошлём всем сохранённым ID (нужна реализация хранения user_ids)
    await update.message.reply_text("✅ Рассылка отправлена (эмуляция).")

# Запуск бота
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("broadcast", broadcast))

    logger.info("🚀 Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
