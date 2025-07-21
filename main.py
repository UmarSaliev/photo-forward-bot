import logging
import os
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = list(map(int, os.getenv("OWNER_IDS", "").split(","))) if os.getenv("OWNER_IDS") else []
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_USERNAME = "@JalilSupportBot"  # Замени на юзернейм бота (например, "@MathHelperBot")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проверка доступа (только для OWNER_IDS)
async def is_owner(update: Update) -> bool:
    return update.effective_user.id in OWNER_IDS

# AI-запрос к OpenRouter
async def ask_ai(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": f"https://t.me/{BOT_USERNAME[1:]}",  # Убираем @ из юзернейма
        "X-Title": "MathHelperBot"
    }
    json_data = {
        "model": "openrouter/meta-llama/llama-3-8b-instruct:free",
        "messages": [{"role": "user", "content": prompt}]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

# Команды для всех
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я математический помощник. Напиши задачу или пришли фото!")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные команды:\n"
        "/task - реши задачу\n"
        "/formula - формула\n"
        "/theorem - теорема\n"
        "/search - поиск по фото\n"
    )
    if await is_owner(update):
        help_text += "\nКоманды для учителя:\n/broadcast - рассылка\n/list - список учеников"
    await update.message.reply_text(help_text)

async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Реши задачу: " + " ".join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def formula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Формула: " + " ".join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def theorem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Теорема: " + " ".join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        await update.message.reply_text("🔎 Анализирую изображение...")
    else:
        prompt = "Поиск: " + " ".join(context.args)
        response = await ask_ai(prompt)
        await update.message.reply_text(response)

# Команды только для OWNER_IDS
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_owner(update):
        await update.message.reply_text("❌ Доступ запрещён.")
        return
    # Здесь логика рассылки (например, сохранённым пользователям)
    await update.message.reply_text("Рассылка запущена!")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_owner(update):
        await update.message.reply_text("❌ Доступ запрещён.")
        return
    # Здесь логика вывода списка учеников
    await update.message.reply_text("Список учеников: ...")

# Обработчики
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Общедоступные команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("task", task))
    app.add_handler(CommandHandler("formula", formula))
    app.add_handler(CommandHandler("theorem", theorem))
    app.add_handler(CommandHandler("search", search))
    
    # Команды только для владельцев
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("list", list_users))

    # Обработка фото и текста
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))

    logger.info("🤖 Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
