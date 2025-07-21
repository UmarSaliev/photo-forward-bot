import logging
import os
from telegram import Update, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from openai import OpenAI
from PIL import Image
import pytesseract
from io import BytesIO

# Настройка логгирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Настройка OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ID владельцев бота (можно указать несколько)
OWNER_IDS = {123456789}  # Замените на свои Telegram ID

# Состояние пользователя для команды /check
user_check_mode = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я математический бот с поддержкой ИИ. Отправь /help для списка команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Начать
/help - Помощь
/check - Проверить задачу с помощью ИИ
/task - Получить случайную задачу
/definition - Объяснение термина
/formula - Формула по теме
/theorem - Теорема по теме"
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_check_mode.add(update.effective_user.id)
    await update.message.reply_text("🔍 Пришлите текст или фотографию задачи для проверки")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_check_mode:
        user_check_mode.remove(user_id)
        question = update.message.text
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты математический помощник. Решай кратко и понятно."},
                    {"role": "user", "content": question}
                ]
            )
            reply = response.choices[0].message.content
            await update.message.reply_text(f"✏️ Ответ: {reply}")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Ошибка OpenAI: {e}")
    else:
        await update.message.reply_text("ℹ️ Я не распознал команду. Используй /help")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()
    image = Image.open(BytesIO(image_bytes))

    text = pytesseract.image_to_string(image)

    if user_id in user_check_mode:
        user_check_mode.remove(user_id)
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты математик. Распознай задачу с изображения и реши её."},
                    {"role": "user", "content": text}
                ]
            )
            reply = response.choices[0].message.content
            await update.message.reply_text(f"📷 Задача распознана и решена: {reply}")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Ошибка OpenAI: {e}")
    else:
        # Только владельцам отправлять
        for owner_id in OWNER_IDS:
            await context.bot.send_photo(chat_id=owner_id, photo=photo.file_id, caption=f"📤 Фото от @{update.effective_user.username or user_id}")

async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Пока эта функция в разработке")

async def definition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📘 Пока эта функция в разработке")

async def formula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📐 Пока эта функция в разработке")

async def theorem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📏 Пока эта функция в разработке")

async def main():
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("task", task))
    application.add_handler(CommandHandler("definition", definition))
    application.add_handler(CommandHandler("formula", formula))
    application.add_handler(CommandHandler("theorem", theorem))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🚀 Бот запущен!")
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
