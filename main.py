import logging
import os
from telegram import Update
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

# AI-запрос
async def ask_ai(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://t.me/YourBotUsername",  # Замени на имя своего бота
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
    await update.message.reply_text("👋 Привет! Я математический помощник. Напиши задачу или используй команды!")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/task <задача> - решить задачу\n"
        "/check <решение> - проверить решение\n"
        "/definition <термин> - дать определение\n"
        "/formula <тема> - формула\n"
        "/theorem <название> - теорема"
    )

# Обработка команд
async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи задачу после команды. Пример: /task 2x + 3 = 7")
        return
    prompt = "Реши задачу: " + ' '.join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи решение после команды. Пример: /check x = 3")
        return
    prompt = "Проверь решение: " + ' '.join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def definition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи термин. Пример: /definition производная")
        return
    prompt = "Дай определение: " + ' '.join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def formula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи тему. Пример: /formula площадь круга")
        return
    prompt = "Формула: " + ' '.join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

async def theorem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи теорему. Пример: /theorem Пифагора")
        return
    prompt = "Объясни теорему: " + ' '.join(context.args)
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

# Обработка обычного текста
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    response = await ask_ai(prompt)
    await update.message.reply_text(response)

# Запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрация всех команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("task", task))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("definition", definition))
    app.add_handler(CommandHandler("formula", formula))
    app.add_handler(CommandHandler("theorem", theorem))

    # Обработка текста
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("🤖 Бот запущен...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

# Точка входа
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
