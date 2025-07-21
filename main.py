import os
import logging
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
BOT_TOKEN        = os.getenv("BOT_TOKEN")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
OWNER_IDS        = [int(x) for x in os.getenv("OWNER_IDS", "").split(",") if x.strip().isdigit()]

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не задан в окружении")
    exit(1)
if not OPENAI_API_KEY:
    logger.warning("⚠️ OPENAI_API_KEY не задан — /check будет недоступен")

openai.api_key = OPENAI_API_KEY

# --- Режим проверки ---
async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["checking"] = True
    await update.message.reply_text("🔍 Пришлите текст или фотографию задачи для проверки.")

# --- Обработка входящего текста ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.pop("checking", False):
        prompt = f"Реши эту математическую задачу и объясни шаги:\n{update.message.text}"
        try:
            resp = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{"role":"user", "content":prompt}],
                temperature=0.2
            )
            answer = resp.choices[0].message.content.strip()
        except Exception as e:
            answer = f"⚠️ Ошибка при обращении к OpenAI: {e}"
        await update.message.reply_text(answer)
    else:
        # Любой другой текст обрабатываем стандартно
        await update.message.reply_text("ℹ️ Чтобы проверить задачу, сначала вызовите /check")

# --- Обработка фотографии ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.pop("checking", False):
        # скачиваем bytes
        photo = update.message.photo[-1]
        f = await photo.get_file()
        buf = BytesIO()
        await f.download_to_memory(buf)
        data = buf.getvalue()
        # отправляем Base64-URI в OpenAI (через GPT-4 Vision или аналог)
        prompt = "Реши математическую задачу на приложенном изображении."
        try:
            b64 = __import__("base64").b64encode(data).decode()
            resp = await openai.ChatCompletion.acreate(
                model="gpt-4o",
                messages=[
                  {"role":"user","content":prompt},
                  {"role":"user","content":[
                    {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}  
                  ]}
                ]
            )
            answer = resp.choices[0].message.content.strip()
        except Exception as e:
            answer = f"⚠️ Ошибка при обработке фото: {e}"
        await update.message.reply_text(answer)
    else:
        # автоматически пересылаем владельцам
        for oid in OWNER_IDS:
            await context.bot.forward_message(
                chat_id=oid,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
        await update.message.reply_text("📨 Фото переслано владельцам.")

# --- Прочие команды-заглушки ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я бот‑помощник по математике. /help")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/check — перейти в режим проверки задачи\n"
        "/ping — проверить связь\n"
        "/status — статус бота\n"
        "/list — показать OWNER_IDS (только им)\n"
        "/broadcast — рассылка (только OWNER_IDS)\n"
        "/task — случайная задача (заглушка)\n"
        "/definition — определение (заглушка)\n"
        "/formula — формула (заглушка)\n"
        "/theorem — теорема (заглушка)"
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот запущен и готов.")

async def list_owners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in OWNER_IDS:
        await update.message.reply_text("👑 OWNER_IDS:\n" + "\n".join(map(str, OWNER_IDS)))
    else:
        await update.message.reply_text("⛔ Нет доступа.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("⛔ Только OWNER_IDS.")
    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("Введите текст после /broadcast")
    for uid in OWNER_IDS:
        await context.bot.send_message(chat_id=uid, text=f"📢 Рассылка:\n{msg}")
    await update.message.reply_text("✅ Рассылка отправлена.")

async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📘 Пришли задачу через /check")

async def definition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📖 Пришли термин через /check")

async def formula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("➗ Пришли формулу через /check")

async def theorem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📐 Пришли теорему через /check")

# --- Сборка и запуск ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("list", list_owners))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("check", check_command))
    app.add_handler(CommandHandler("task", task))
    app.add_handler(CommandHandler("definition", definition))
    app.add_handler(CommandHandler("formula", formula))
    app.add_handler(CommandHandler("theorem", theorem))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("🚀 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
