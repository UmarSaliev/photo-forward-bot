import logging
import os
import io
import base64
import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = set(map(int, os.getenv("OWNER_IDS", "").split(",")))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL_ID = "openrouter/anthropic/claude-3-haiku"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я главный помощник мистера Абдужалила 🤓. "
        "Ты можешь пересылать мне задачи, с которыми у тебя возникли проблемы, и я передам их ему 🚀. "
        "Пожалуйста, при отправке четко выдели саму задачу и постарайся объяснить, в чем ты запутался 💯.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown_v2(
        "📚 *Доступные команды:*\n"
        "/check \\- Проверка решения по фото\n"
        "/task \\- Новая задача\n"
        "/definition \\- Определение термина\n"
        "/formula \\- Формула по теме\n"
        "/theorem \\- Теорема и пример"
    )

async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in OWNER_IDS and context.user_data.get("mode") == "check":
        await update.message.reply_text("⚠️ Владелец не может использовать /check на фото.")
        return

    photo = await update.message.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()

    image_b64 = base64.b64encode(photo_bytes).decode("utf-8")
    prompt = f"На изображении находится задача по математике. Помоги решить её пошагово."

    result = await ask_openrouter(prompt, image_b64)
    await update.message.reply_text(result or "⚠️ Ошибка AI")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    result = await ask_openrouter(text)
    await update.message.reply_text(result or "⚠️ Ошибка AI")

async def ask_openrouter(prompt, image_b64=None):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://t.me/YourBot",  # укажи своего бота
        "X-Title": "Telegram Math Bot",
    }
    messages = [{"role": "user", "content": prompt}]
    if image_b64:
        messages[0]["content"] = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
        ]

    data = {
        "model": MODEL_ID,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            if response.status_code != 200:
                return f"⚠️ Ошибка AI: код {response.status_code}"
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Ошибка AI: {str(e)}"

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.PHOTO, image_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
