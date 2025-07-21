import os import logging from telegram import Update, InputFile from telegram.ext import ( ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ) import openai from io import BytesIO import base64

Логирование

logging.basicConfig(level=logging.INFO) logger = logging.getLogger(name)

Переменные окружения

BOT_TOKEN = os.getenv("BOT_TOKEN") OWNER_IDS = [int(uid.strip()) for uid in os.getenv("OWNER_IDS", "").split(",") if uid.strip().isdigit()] OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN: logger.error("❌ BOT_TOKEN не задан в переменных окружения!") exit(1)

if not OPENAI_API_KEY: logger.warning("⚠️ OPENAI_API_KEY не задан, /check не будет работать корректно.")

openai.api_key = OPENAI_API_KEY

Хранение состояния /check для пользователей

user_check_mode = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("👋 Привет! Я — бот-помощник по математике AJ. Напиши /help для списка команд.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "/start — Запуск бота\n" "/help — Список команд\n" "/ping — Проверка ответа\n" "/status — Статус бота\n" "/task — Математическая задача\n" "/definition — Определение\n" "/formula — Формула\n" "/theorem — Теорема\n" "/check — Проверка текста или изображения с помощью ИИ\n" "/list — Список владельцев (только для OWNER_IDS)\n" "/broadcast — Рассылка сообщения (только для OWNER_IDS)" )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("🏓 Pong!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("✅ Бот работает!")

async def list_owners(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.effective_user.id in OWNER_IDS: owners = "\n".join(map(str, OWNER_IDS)) await update.message.reply_text(f"👑 Владелец(ы):\n{owners}") else: await update.message.reply_text("⛔ Команда только для владельцев.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.effective_user.id not in OWNER_IDS: return await update.message.reply_text("⛔ Команда только для владельцев.") message = " ".join(context.args) if not message: return await update.message.reply_text("⚠️ Использование: /broadcast <текст>") for user_id in OWNER_IDS: try: await context.bot.send_message(chat_id=user_id, text=f"[Broadcast]\n{message}") except Exception as e: logger.warning(f"Не удалось отправить сообщение {user_id}: {e}") await update.message.reply_text("📣 Сообщение отправлено владельцам.")

async def process_text_ai(text: str) -> str: if not OPENAI_API_KEY: return "❌ OpenAI API ключ не задан!" try: response = openai.ChatCompletion.create( model="gpt-4o", messages=[{"role": "user", "content": text}], ) return response.choices[0].message.content.strip() except Exception as e: return f"⚠️ Ошибка ИИ: {e}"

async def process_photo_ai(file_bytes: bytes) -> str: if not OPENAI_API_KEY: return "❌ OpenAI API ключ не задан!" try: base64_image = base64.b64encode(file_bytes).decode("utf-8") response = openai.ChatCompletion.create( model="gpt-4o", messages=[ {"role": "user", "content": "Реши математическую задачу на изображении."}, { "role": "user", "content": [ { "type": "image_url", "image_url": { "url": f"data:image/jpeg;base64,{base64_image}" }, } ], }, ], ) return response.choices[0].message.content.strip() except Exception as e: return f"⚠️ Ошибка при обработке изображения: {e}"

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE): user_check_mode.add(update.effective_user.id) await update.message.reply_text("📷 Пришли фото или текст задачи, и я постараюсь помочь!")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE): uid = update.effective_user.id if uid in user_check_mode: user_check_mode.remove(uid) response = await process_text_ai(update.message.text) await update.message.reply_text(response) else: await update.message.reply_text("✏️ Текст получен. Напиши /check, чтобы проанализировать.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE): uid = update.effective_user.id photo = update.message.photo[-1] file = await photo.get_file() file_bytes = await file.download_as_bytearray()

if uid in user_check_mode:
    user_check_mode.remove(uid)
    response = await process_photo_ai(file_bytes)
    await update.message.reply_text(response)
else:
    for owner_id in OWNER_IDS:
        try:
            await context.bot.send_photo(chat_id=owner_id, photo=InputFile(BytesIO(file_bytes), filename="photo.jpg"))
        except Exception as e:
            logger.warning(f"Не удалось отправить фото владельцу {owner_id}: {e}")
    await update.message.reply_text("📨 Фото переслано владельцам.")

async def task(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("📚 Отправьте вашу задачу через /check.")

async def definition(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("🧠 Напишите термин, и я объясню его через /check.")

async def formula(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("➗ Напишите формулу, и я помогу разобрать ёё через /check.")

async def theorem(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("📐 Напишите теорему, и я объясню ёё через /check.")

async def main(): app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("ping", ping))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("list", list_owners))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("check", check))
app.add_handler(CommandHandler("task", task))
app.add_handler(CommandHandler("definition", definition))
app.add_handler(CommandHandler("formula", formula))
app.add_handler(CommandHandler("theorem", theorem))

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

logger.info("🚀 Бот запущен!")
await app.run_polling()

if name == "main": import asyncio asyncio.run(main())

