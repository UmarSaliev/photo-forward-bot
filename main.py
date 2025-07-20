import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# === НАСТРОЙКИ ===
BOT_TOKEN = "8189283086:AAGR_QF2NuupIZA4G_Fhys_81CU-9-BOWaU"
OWNER_IDS = [95293299, 784341697]  # Замените на ваши Telegram ID

# === ЛОГГИРОВАНИЕ ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# === ГЛОБАЛЬНОЕ ХРАНИЛИЩЕ ===
senders = set()

# === ОБРАБОТЧИК ФОТО ===
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not update.message.photo:
        return

    senders.add(f"@{user.username}" if user.username else f"{user.first_name} ({user.id})")

    for owner_id in OWNER_IDS:
        await context.bot.forward_message(
            chat_id=owner_id,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )

    await update.message.reply_text("Спасибо, задание получено! ✅")

# === /LIST ===
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return

    if not senders:
        await update.message.reply_text("Список отправителей пока пуст.")
    else:
        await update.message.reply_text("\n".join(sorted(senders)))

# === /START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Спасибо за то что отправил задание- скоро я его решу и отправлю тебе ответ.")

# === /HELP ===
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Отправь сюда фотографию непонятного задания — и я попробую его решить.")

# === ЗАПУСК ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    print("Бот запущен...")
    app.run_polling()
