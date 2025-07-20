import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import os

# Вставь свои данные ниже
BOT_TOKEN = os.getenv("8189283086:AAGR_QF2NuupIZA4G_Fhys_81CU-9-BOWaU")
OWNER_IDS = {95293299, 784341697}  # замените на свои Telegram user_id

# Хранилище пользователей, отправивших фото
user_ids = set()

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Отправь фото с непонятным заданием — я передам учителю.")

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Этот бот создан для того, чтобы ты мог отправлять фото с заданиями учителю. Просто отправь фото!")

async def list_students(update: Update, context: CallbackContext):
    if update.effective_user.id not in OWNER_IDS:
        return
    if not user_ids:
        await update.message.reply_text("Ученики ещё не отправляли фото.")
    else:
        text = "Ученики, отправившие фото:\n" + "\n".join([str(uid) for uid in user_ids])
        await update.message.reply_text(text)

async def status(update: Update, context: CallbackContext):
    if update.effective_user.id not in OWNER_IDS:
        return
    await update.message.reply_text("✅ Бот работает!")

async def ping(update: Update, context: CallbackContext):
    if update.effective_user.id not in OWNER_IDS:
        return
    await update.message.reply_text("Да, да я тут, спасибо что разбудили!")

async def broadcast(update: Update, context: CallbackContext):
    if update.effective_user.id not in OWNER_IDS:
        return
    if not context.args:
        await update.message.reply_text("Используй: /broadcast Текст сообщения")
        return

    text = " ".join(context.args)
    failed = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение {uid}: {e}")
            failed += 1

    await update.message.reply_text(f"Рассылка завершена. Не удалось отправить {failed} пользователям.")

async def handle_photo(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_ids.add(user_id)

    # Отправка фото владельцам
    for owner_id in OWNER_IDS:
        for photo in update.message.photo:
            await context.bot.send_photo(chat_id=owner_id, photo=photo.file_id)

    await update.message.reply_text("Спасибо, задание принято!")

async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_students))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("Бот запущен")
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
