import logging
import os
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = list(map(int, os.getenv("OWNER_IDS", "").split(",")))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AI-запрос к OpenRouter
async def ask_ai(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://t.me/YourBotUsername",  # Измени на свой юзернейм
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

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я математический помощник. Напиши задачу или пришли фото!")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/task - реши задачу
/check - проверь решение
/definition - дай определение
/formula - формула
/theorem - теорема")

async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Реши задачу: " + " ".join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Проверь решение: " + " ".join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def definition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Дай определение: " + " ".join(context.args)
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

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

# Запуск
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("task", task))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("definition", definition))
    app.add_handler(CommandHandler("formula", formula))
    app.add_handler(CommandHandler("theorem", theorem))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("🤖 Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
