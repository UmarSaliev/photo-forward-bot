import logging
import os
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests

OWNER_IDS = [123456789]  # Замените на свой ID
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я главный помощник мистера Абдужалила 🤓. Ты можешь пересылать мне задачи с которыми у тебя возникли проблемы и я передам их ему 🚀. Пожалуйста при отправке четко выдели саму задачу или пример и постарайся обьяснить в чем ты запутался 💯.\n"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши /check и пришли мне математическую задачу в тексте или фото!")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_states.get(user_id) == "awaiting_check":
        user_states[user_id] = None
        await process_with_ai(update, update.message.text)
    else:
        await update.message.reply_text("🔍 Отправь текст или фото задачи для проверки с командой /check.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_states.get(user_id) == "awaiting_check":
        user_states[user_id] = None
        photo_file = await update.message.photo[-1].get_file()
        file_path = f"photo_{user_id}.jpg"
        await photo_file.download_to_drive(file_path)
        await update.message.reply_text("📸 Фото задачи получено. Отправка в ИИ...")
        await process_with_ai(update, f"[Изображение задачи: {file_path}]")  # Можно распознать с OCR позже
    elif user_id in OWNER_IDS:
        await context.bot.send_photo(chat_id=OWNER_IDS[0], photo=update.message.photo[-1].file_id)

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_states[update.effective_user.id] = "awaiting_check"
    await update.message.reply_text("🔍 Пришли текст или фото задачи для проверки.")

async def process_with_ai(update: Update, prompt: str):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": "openai/gpt-3.5-turbo",  # Можно заменить на другой, например mistralai/mistral-7b
        "messages": [
            {"role": "system", "content": "Ты — математический помощник. Отвечай чётко, кратко и по теме."},
            {"role": "user", "content": prompt},
        ],
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
        data = response.json()

        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text("⚠️ Ошибка при получении ответа от ИИ.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при подключении к ИИ:\n{e}")

async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_with_ai(update, "Придумай интересную задачу по математике.")

async def definition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_with_ai(update, "Объясни математический термин.")

async def formula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_with_ai(update, "Приведи математическую формулу с объяснением.")

async def theorem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_with_ai(update, "Назови и объясни важную математическую теорему.")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(CommandHandler("task", task))
    application.add_handler(CommandHandler("definition", definition))
    application.add_handler(CommandHandler("formula", formula))
    application.add_handler(CommandHandler("theorem", theorem))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("🚀 Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
