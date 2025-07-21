import os
import logging
from io import BytesIO
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import openai
import pytesseract
from PIL import Image

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN      = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_IDS_RAW  = os.getenv("OWNER_IDS", "")
OWNER_IDS      = [int(x) for x in OWNER_IDS_RAW.split(",") if x.strip().isdigit()]

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не задан в переменных окружения!")
    exit(1)
if not OPENAI_API_KEY:
    logger.error("❌ OPENAI_API_KEY не задан в переменных окружения!")
    exit(1)

openai.api_key = OPENAI_API_KEY

# Функция для вызова OpenAI текстовой модели
async def ask_openai(prompt: str) -> str:
    try:
        resp = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Ошибка OpenAI: {e}"

# --- /check режим ---
async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["checking"] = True
    await update.message.reply_text(
        "🔍 Пришлите текст или фотографию задачи для проверки через ИИ."
    )

# Обработка текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.pop("checking", False):
        prompt = f"Реши эту математическую задачу и объясни шаги:\n{update.message.text}"
        answer = await ask_openai(prompt)
        await update.message.reply_text(answer)
    else:
        await update.message.reply_text(
            "ℹ️ Чтобы проверить задачу, сначала вызовите /check"
        )

# Обработка фотографий через OCR + ИИ
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.pop("checking", False):
        # Скачаем фото во временный буфер
        photo = update.message.photo[-1]
        file = await photo.get_file()
        bio = BytesIO()
        await file.download_to_memory(bio)
        bio.seek(0)
        # OCR распознавание текста
        image = Image.open(bio)
        text = pytesseract.image_to_string(image)
        if not text.strip():
            return await update.message.reply_text("❌ Не удалось распознать текст на изображении.")
        await update.message.reply_text(f"📋 Распознанный текст:\n{text}")
        prompt = f"Реши эту математическую задачу и объясни шаги:\n{text}"
        answer = await ask_openai(prompt)
        await update.message.reply_text(answer)
    else:
        # Переслать владельцам без /check
        for oid in OWNER_IDS:
            await context.bot.forward_message(
                chat_id=oid,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
        await update.message.reply_text("📨 Фото переслано владельцам.")

# Прочие команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-помощник по математике AJ. Напиши /help для списка команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/check      — режим проверки (текст или фото)\n"
        "/ping       — проверить связь\n"
        "/status     — статус бота\n"
        "/list       — список владельцев (только OWNER_IDS)\n"
        "/broadcast  — рассылка (только OWNER_IDS)\n"
        "/task       — получить задачу (заглушка)\n"
        "/definition — получить определение (заглушка)\n"
        "/formula    — получить формулу (заглушка)\n"
        "/theorem    — получить теорему (заглушка)"
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает нормально.")

async def list_owners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in OWNER_IDS:
        await update.message.reply_text(
            "👑 OWNER_IDS:\n" + "\n".join(map(str, OWNER_IDS))
        )
    else:
        await update.message.reply_text("⛔ Доступ запрещён.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("⛔ Только владельцы могут рассылать.")
    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("⚠️ Использование: /broadcast <текст>")
    for uid in OWNER_IDS:
        await context.bot.send_message(chat_id=uid, text=f"📢 Рассылка:\n{msg}")
    await update.message.reply_text("✅ Рассылка выполнена.")

async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📘 Пришлите задачу через /check.")

async def definition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📖 Пришлите термин через /check.")

async def formula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("➗ Пришлите формулу через /check.")

async def theorem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📐 Пришлите теорему через /check.")

# Запуск бота

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("list", list_owners))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("task", task))
    app.add_handler(CommandHandler("definition", definition))
    app.add_handler(CommandHandler("formula", formula))
    app.add_handler(CommandHandler("theorem", theorem))
    app.add_handler(CommandHandler("check", check_command))
    # Хендлеры
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    logger.info("🚀 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
