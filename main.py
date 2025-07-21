import os
import logging
import base64
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import openai

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = [int(uid.strip()) for uid in os.getenv("OWNER_IDS", "").split(",") if uid.strip().isdigit()]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Проверка переменных
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не задан в переменных окружения!")
    exit(1)
if not OPENAI_API_KEY:
    logger.warning("⚠️ OPENAI_API_KEY не задан, /check не будет работать.")

openai.api_key = OPENAI_API_KEY

# Состояние /check
user_check_mode = set()

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я — бот-помощник по математике AJ. Напиши /help для списка команд.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — Запуск бота\n"
        "/help — Список команд\n"
        "/ping — Проверка ответа\n"
        "/status — Статус бота\n"
        "/task — Математическая задача\n"
        "/definition — Определение\n"
        "/formula — Формула\n"
        "/theorem — Теорема\n"
        "/check — Проверка текста или изображения с помощью ИИ\n"
        "/list — Список владельцев (только для OWNER_IDS)\n"
        "/broadcast — Рассылка (только для OWNER_IDS)"
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает!")

async def list_owners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in OWNER_IDS:
        await update.message.reply_text("👑 Владелец(ы):\n" + "\n".join(map(str, OWNER_IDS)))
    else:
        await update.message.reply_text("⛔ Команда только для владельцев.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("⛔ Команда только для владельцев.")
    message = " ".join(context.args)
    if not message:
        return await update.message.reply_text("⚠️ Использование: /broadcast <текст>")
    for user_id in OWNER_IDS:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"[Broadcast]\n{message}")
        except Exception as e:
            logger.warning(f"❌ Не удалось отправить {user_id}: {e}")
    await update.message.reply_text("📣 Рассылка завершена.")

# AI обработка
async def process_text_ai(text: str) -> str:
    if not OPENAI_API_KEY:
        return "❌ OpenAI API ключ не задан!"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": text}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Ошибка OpenAI: {e}"

async def process_photo_ai(image_bytes: bytes) -> str:
    if not OPENAI_API_KEY:
        return "❌ OpenAI API ключ не задан!"
    try:
        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Реши математическую задачу на изображении."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                        }
                    ],
                },
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Ошибка при обработке изображения: {e}"

# /check
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_check_mode.add(update.effective_user.id)
    await update.message.reply_text("📥 Пришли текст или фото задачи для анализа.")

# Обработка текста
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_check_mode:
        user_check_mode.remove(uid)
        reply = await process_text_ai(update.message.text)
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("✏️ Напиши /check перед отправкой задачи.")

# Обработка фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()

    if uid in user_check_mode:
        user_check_mode.remove(uid)
        result = await process_photo_ai(image_bytes)
        await update.message.reply_text(result)
    else:
        for owner_id in OWNER_IDS:
            try:
                await context.bot.send_photo(
                    chat_id=owner_id,
                    photo=InputFile(BytesIO(image_bytes), filename="photo.jpg")
                )
            except Exception as e:
                logger.warning(f"Не удалось отправить фото владельцу {owner_id}: {e}")
        await update.message.reply_text("📨 Фото отправлено владельцам.")

# Заглушки
async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📘 Отправьте задачу через /check.")

async def definition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📖 Напишите термин через /check.")

async def formula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("➗ Напишите формулу через /check.")

async def theorem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📐 Напишите теорему через /check.")

# Main
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("list", list_owners))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("task", task))
    app.add_handler(CommandHandler("definition", definition))
    app.add_handler(CommandHandler("formula", formula))
    app.add_handler(CommandHandler("theorem", theorem))

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("🚀 Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
