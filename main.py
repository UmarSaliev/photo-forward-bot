import os
import logging
import asyncio
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from openai import AsyncOpenAI

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_IDS = os.getenv("OWNER_IDS", "")
OWNER_IDS = list(map(int, OWNER_IDS.split(","))) if OWNER_IDS else []

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не задан в переменных окружения!")
    exit(1)

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я бот-помощник по математике. Используй /help для списка команд.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = (
        "/check — проверить текст или изображение с задачей\n"
        "/task — отправить случайную задачу\n"
        "/definition — объяснение математического понятия\n"
        "/formula — показать формулу\n"
        "/theorem — рассказать теорему\n"
        "/broadcast — [для владельцев] отправка сообщения всем"
    )
    await update.message.reply_text(f"📘 Список команд:\n{commands}")

# --- ИИ-функции ---
async def ask_openai(prompt: str) -> str:
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Ошибка OpenAI: {e}")
        return "Произошла ошибка при обращении к ИИ."

# --- Команды /check, /task и др. ---
async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📤 Отправьте задачу в виде текста или изображения, и я постараюсь её решить.")
    context.user_data["awaiting_check"] = True

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_check"):
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = "/tmp/temp.jpg"
        await file.download_to_drive(file_path)

        await update.message.reply_text("📷 Фото получено. Попробую распознать и решить...")
        # ⚠️ Здесь можно вставить интеграцию с OCR или моделью распознавания задач
        await update.message.reply_text("Пока я не умею решать фото, но скоро научусь 😉")
        context.user_data["awaiting_check"] = False
    elif update.message.from_user.id in OWNER_IDS:
        # Только владельцы получают фото без команды
        await update.message.forward(chat_id=OWNER_IDS[0])

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_check"):
        response = await ask_openai(update.message.text)
        await update.message.reply_text(f"📥 Ответ:\n{response}")
        context.user_data["awaiting_check"] = False

async def task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Придумай интересную задачу по математике для ученика средней школы."
    response = await ask_openai(prompt)
    await update.message.reply_text(response)

async def definition_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Объясни простыми словами математическое определение."
    response = await ask_openai(prompt)
    await update.message.reply_text(response)

async def formula_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Приведи полезную математическую формулу и объясни её."
    response = await ask_openai(prompt)
    await update.message.reply_text(response)

async def theorem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Назови математическую теорему и объясни её."
    response = await ask_openai(prompt)
    await update.message.reply_text(response)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in OWNER_IDS:
        return await update.message.reply_text("⛔ Эта команда доступна только владельцам бота.")
    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("Введите текст для рассылки.")
    for uid in OWNER_IDS:
        try:
            await context.bot.send_message(chat_id=uid, text=f"[📢 Рассылка]\n{msg}")
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение {uid}: {e}")
    await update.message.reply_text("✅ Рассылка отправлена.")

# --- Основной запуск ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("check", check_command))
    app.add_handler(CommandHandler("task", task_command))
    app.add_handler(CommandHandler("definition", definition_command))
    app.add_handler(CommandHandler("formula", formula_command))
    app.add_handler(CommandHandler("theorem", theorem_command))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("🚀 Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
