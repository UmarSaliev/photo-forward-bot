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
        "HTTP-Referer": "https://t.me/YourBotUsername",  # Заменить на актуальный юзернейм бота
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
    await update.message.reply_text("👋 Привет! Я математический помощник. Напиши задачу или используй команды: /task, /check, /definition, /formula, /theorem")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 Доступные команды:\n"
        "/task <задача> — решу задачу\n"
        "/check <решение> — проверю решение\n"
        "/definition <термин> — дам определение\n"
        "/formula <тема> — покажу формулу\n"
        "/theorem <название> — объясню теорему"
    )

async def task_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Реши задачу: " + ' '.join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Проверь решение: " + ' '.join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def definition_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Дай определение: " + ' '.join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def formula_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Формула по теме: " + ' '.join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def theorem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "Объясни теорему: " + ' '.join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

# Запуск бота
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрация команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("task", task_cmd))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("definition", definition_cmd))
    app.add_handler(CommandHandler("formula", formula_cmd))
    app.add_handler(CommandHandler("theorem", theorem_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("🤖 Бот запущен...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

# Railway / локальный запуск
if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().create_task(main())
    asyncio.get_event_loop().run_forever()
