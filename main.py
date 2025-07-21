import os
import logging
import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = set(map(int, os.getenv("OWNER_IDS", "").split(",")))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === OpenRouter Chat Completion ===
async def ask_openrouter(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourapp.com",
        "X-Title": "MathBot",
    }
    payload = {
        "model": "openrouter/cinematika-7b",  # можешь поменять на любой поддерживаемый
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


# === Обработчики команд ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я математический бот с поддержкой AI. Отправь вопрос или используй команды.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Доступные команды:\n/check\n/task\n/definition\n/formula\n/theorem\n/ping\n/status")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает нормально.")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in OWNER_IDS:
        await update.message.reply_text("Ты владелец. Доступ открыт.")
    else:
        await update.message.reply_text("⛔ Эта команда только для владельцев.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith(("/check", "/task", "/definition", "/formula", "/theorem")):
        command, *prompt = text.split(maxsplit=1)
        prompt_text = prompt[0] if prompt else "Объясни это, пожалуйста."
        reply = await ask_openrouter(f"{command} {prompt_text}")
        await update.message.reply_text(reply)
    else:
        reply = await ask_openrouter(text)
        await update.message.reply_text(reply)


# === Обработка фото ===
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in OWNER_IDS and update.message.caption and update.message.caption.startswith("/check"):
        await update.message.reply_text("⛔ Владелец не может проверять свои собственные фото.")
        return

    await update.message.reply_text("🖼️ Обработка изображения... (но пока только текст поддерживается)")
