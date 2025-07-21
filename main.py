import logging
import os
import asyncio

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

# Загрузка .env переменных
load_dotenv()

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = os.getenv("OWNER_IDS", "").split(",")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не задан в переменных окружения!")
    exit(1)

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я помощник учителя математики 🤖📐")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/check — решить задачу\n/task — дай задачу\n/formula — формула\n/theorem — теорема\n/definition — определение")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        await update.message.reply_text("🧠 Обработка фото с задачей... (в будущем — через ИИ)")
        # Тут можно подключить обработку изображения
    else:
        await update.message.reply_text("🔍 Отправь текст или фото задачи для проверки.")

async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вот тебе задача: Найди x, если 2x + 3 = 7")

async def definition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Определение: Периметр — это сумма длин всех сторон фигуры.")

async def formula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Формула: Площадь круга = π * r²")

async def theorem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Теорема Пифагора: a² + b² = c²")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in OWNER_IDS:
        return await update.message.reply_text("❌ У тебя нет доступа к этой команде.")

    if not context.args:
        return await update.message.reply_text("✉️ Используй: /broadcast <текст>")

    message = "📢 Рассылка:\n" + " ".join(context.args)
    for user_id in context.bot_data.get("users", set()):
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
    await update.message.reply_text("✅ Рассылка завершена.")

# Регистрация новых пользователей
async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    context.bot_data.setdefault("users", set()).add(user_id)

# Запуск приложения
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("task", task))
    app.add_handler(CommandHandler("definition", definition))
    app.add_handler(CommandHandler("formula", formula))
    app.add_handler(CommandHandler("theorem", theorem))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Регистрация юзеров
    app.add_handler(MessageHandler(filters.ALL, register_user), group=1)

    logger.info("🚀 Бот запущен!")
    await app.run_polling()


# Запуск с учетом Railway или Jupyter
if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.get_event_loop().run_until_complete(main())
