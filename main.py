import os
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

async def forward_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg: Message = update.message
    if msg.photo:
        await msg.forward(chat_id=OWNER_ID)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, forward_photo))
    print("🤖 Photo-forwarding bot started!")
    app.run_polling()
