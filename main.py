import logging
import os
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import openai
from io import BytesIO

# Логгинг
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_IDS = os.getenv("OWNER_IDS", "")
OWNER_IDS = set(map(int, OWNER_IDS.split(","))) if OWNER_IDS else set()

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не задан в переменных окружения!")
    exit(1)

# Установка ключа OpenAI
openai.api_key = OPENAI_API_KEY

# Функция генерации ответа от ИИ
async def ask_openai(prompt: str) -> str:
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Ошибка OpenAI: {e}"

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот-помощник учителя математики. Используй /help чтобы узнать, что я умею.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/task — объяснение математического задания\n"
        "/definition — определение математического термина\n"
        "/formula — выдача математических формул\n"
        "/theorem — известные теоремы\n"
        "/check — проанализировать текст или фото с задачей"
    )

# Обработка команд с AI
async def handle_ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE, prefix: str):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Пожалуйста, введите вопрос после команды.")
        return
    prompt = f"{prefix}: {query}"
    reply = await ask_openai(prompt)
    await update.message.reply_text(reply)

async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_ai_command(update, context, "Объясни математическое задание")

async def definition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_ai_command(update, context, "Дай определение по математике")

async def formula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_ai_command(update, context, "Приведи формулу")

async def theorem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_ai_command(update, context, "Объясни математическую теорему")

# /check
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        msg = update.message.reply_to_message
        if msg.text:
            response = await ask_openai(f"Реши задачу: {msg.text}")
            await update.message.reply_text(response)
        elif msg.photo:
            await update.message.reply_text("📷 Распознавание фото пока в разработке.")
    else:
        await update.message.reply_text("Напиши или ответь на сообщение с задачей, которую хочешь проверить.")

# Обработка фото (автоматическая, если не /check)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in OWNER_IDS:
        return  # Не пересылаем самим себе
    # Если не вызвана команда /check, фото пересылается OWNER
    if context.chat_data.get("checking"):
        return
    for owner_id in OWNER_IDS:
        await context.bot.forward_message(chat_id=owner_id, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)

# Главная функция
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("task", task))
    app.add_handler(CommandHandler("definition", definition))
    app.add_handler(CommandHandler("formula", formula))
    app.add_handler(CommandHandler("theorem", theorem))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("🚀 Бот запущен!")
    await app.run_polling()

# Вместо asyncio.run(main()) — корректный запуск
if __name__ == "__main__":
    import asyncio
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
