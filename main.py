import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
import httpx

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = set(map(int, os.getenv("OWNER_IDS", "").split(",")))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== OpenRouter AI Handler =====
async def ask_openrouter(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me/YourBotUsername",  # Укажи юзернейм бота
        "X-Title": "TelegramMathBot",
    }
    json_data = {
        "model": "mistralai/mixtral-8x7b",
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=json_data,
                timeout=20,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"⚠️ Ошибка AI: {e}")
        return f"⚠️ Ошибка AI: {str(e)}"

# ===== Команды с ИИ =====
async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.split(" ")[0][1:]
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("📌 Введите тему после команды.")
        return

    prompt_map = {
        "check": f"Проверь математическое решение: {query}",
        "task": f"Реши задачу по математике: {query}",
        "definition": f"Дай определение: {query}",
        "formula": f"Напиши формулу по теме: {query}",
        "theorem": f"Объясни теорему: {query}",
    }

    prompt = prompt_map.get(command, query)
    answer = await ask_openrouter(prompt)
    await update.message.reply_text(answer)

# ===== Стандартные команды =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-помощник по математике.\n"
        "📚 *Доступные команды:*\n"
        "/check [пример] – проверить решение\n"
        "/task [задача] – решить задачу\n"
        "/definition [тема] – объяснение\n"
        "/formula [тема] – формула\n"
        "/theorem [тема] – теорема\n"
        "/ping – пинг\n"
        "/status – статус\n"
        "/broadcast [сообщение] – рассылка (только для владельцев)\n",
        parse_mode="Markdown"
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает!")

async def list_owners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("⛔ Нет доступа.")
    await update.message.reply_text(f"👑 Владелец(ы): {', '.join(map(str, OWNER_IDS))}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("⛔ Нет доступа.")
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("📌 Введите сообщение.")
    
    for user_id in OWNER_IDS:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"📢 Рассылка:\n\n{text}")
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение {user_id}: {e}")
    await update.message.reply_text("✅ Сообщение разослано.")

# ===== Запуск =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("list", list_owners))
    app.add_handler(CommandHandler("broadcast", broadcast))

    for cmd in ["check", "task", "definition", "formula", "theorem"]:
        app.add_handler(CommandHandler(cmd, ai_command))

    logger.info("🚀 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
