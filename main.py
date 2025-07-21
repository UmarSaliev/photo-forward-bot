import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from openai import OpenAI

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка токенов из переменных окружения
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_IDS = [int(i) for i in os.getenv("OWNER_IDS", "").split(",") if i]

# Инициализация клиента OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Хранилище активных режимов
user_modes = {}

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-помощник по математике.\n"
        "/start - Начать\n"
        "/help - Помощь\n"
        "/check - Проверить задачу\n"
        "/task - Новая задача\n"
        "/definition - Определение\n"
        "/formula - Формула\n"
        "/theorem - Теорема"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Просто отправь мне математическую задачу текстом или фото!")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_modes[user_id] = "check"
    await update.message.reply_text("🔍 Пришлите текст или фотографию задачи для проверки")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in OWNER_IDS:
        users = list(user_modes.keys())
        await update.message.reply_text(f"👥 Пользователи: {users}")
    else:
        await update.message.reply_text("⛔ Недостаточно прав.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    mode = user_modes.get(user_id)

    if mode == "check":
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты помощник по математике. Отвечай понятно и по существу."},
                    {"role": "user", "content": text}
                ]
            )
            answer = response.choices[0].message.content
            await update.message.reply_text(f"📘 Ответ:\n{answer}")
        except Exception as e:
            logger.error(f"OpenAI Error: {e}")
            await update.message.reply_text(f"⚠️ Ошибка OpenAI:\n\n{e}")
        finally:
            user_modes.pop(user_id, None)
    else:
        await update.message.reply_text("✉️ Не понял. Напиши /check перед тем как отправить задачу.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mode = user_modes.get(user_id)

    if mode == "check":
        file = await update.message.photo[-1].get_file()
        photo_bytes = await file.download_as_bytearray()
        await update.message.reply_text("🖼️ Получено фото задачи. Я пока не умею его распознавать.")
        # Здесь можно подключить распознавание через OCR
        user_modes.pop(user_id, None)
    elif user_id in OWNER_IDS:
        return
    else:
        for owner in OWNER_IDS:
            await context.bot.forward_message(chat_id=owner, from_chat_id=update.message.chat_id, message_id=update.message.message_id)

# Дополнительные команды
async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 Новая задача: 2x + 5 = 11. Найди x.")

async def definition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 Определение: Парабола — это геометрическое место точек, равноудалённых от фокуса и директрисы.")

async def formula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📐 Формула площади треугольника: S = 1/2 * a * h")

async def theorem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📏 Теорема Пифагора: a² + b² = c²")

# Основная функция запуска
def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(CommandHandler("task", task))
    application.add_handler(CommandHandler("definition", definition))
    application.add_handler(CommandHandler("formula", formula))
    application.add_handler(CommandHandler("theorem", theorem))
    application.add_handler(CommandHandler("list", list_users))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("🚀 Бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()
