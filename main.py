import logging
import os
from telegram import Update, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes
)
from openrouter import OpenRouter

# Конфигурация
TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = [int(uid) for uid in os.getenv("OWNER_IDS", "").split(",") if uid]

# OpenRouter конфигурация
OR_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openrouter/mistralai/mixtral-8x7b"
or_client = OpenRouter(api_key=OR_API_KEY)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я главный помощник мистера Абдужалила 🤓. Ты можешь пересылать мне задачи с которыми у тебя возникли проблемы и я передам их ему 🚀. Пожалуйста при отправке четко выдели саму задачу или пример и постарайся обьяснить в чем ты запутался 💯."
    )

# Обработка команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 *Доступные команды:*
"
        "/start — начать работу 💻\n"
        "/help — основные команды 📖\n"
        "/ping — проверить связь с хостом 🌐\n"
        "/status — статус активности бота 🤖\n"
        "/list — список учеников, отправивших задания 🤓 (только для учителя)\n"
        "/broadcast — рассылка сообщений ✈️ (только для учителя)\n"
        "/task <запрос> — сгенерировать задачу по математике 📌\n"
        "/definition <тема> — дать определение математического термина 📘\n"
        "/formula <тема> — выдать формулу 📐\n"
        "/theorem <название> — объяснить теорему 📏\n"
        "/check <задача> — проверить и решить задачу ✍️"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# Проверка связи
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong! Бот работает.")

# Статус активности
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот активен и готов к работе.")

# Список учеников (заглушка, т.к. база не подключена)
students = set()

async def list_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("❌ У вас нет доступа к этой команде.")
    
    if not students:
        return await update.message.reply_text("Пока никто не отправлял задания.")

    names = [str(s) for s in students]
    await update.message.reply_text("👨‍🎓 Ученики отправившие задания:\n" + "\n".join(names))

# Рассылка
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("❌ У вас нет доступа к этой команде.")
    
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("✏️ Укажите текст рассылки после команды.")

    count = 0
    for user_id in students:
        try:
            await context.bot.send_message(chat_id=user_id, text=text)
            count += 1
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {user_id}: {e}")

    await update.message.reply_text(f"✅ Сообщение отправлено {count} пользователям.")

# Универсальный AI-помощник
async def ai_response(prompt: str) -> str:
    try:
        response = or_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Ошибка AI: {e}"

# Обработчики AI-команд
def make_ai_handler(prefix: str):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = " ".join(context.args)
        if not query:
            await update.message.reply_text(f"📥 Укажи тему после команды. Например: /{prefix} производная")
            return

        students.add(update.effective_user.id)
        prompt = f"{prefix.capitalize()} по теме '{query}' простыми словами для школьника."
        result = await ai_response(prompt)
        await update.message.reply_text(result)
    return handler

check = make_ai_handler("Реши задачу")
definition = make_ai_handler("Дай определение")
formula = make_ai_handler("Выведи формулу")
theorem = make_ai_handler("Объясни теорему")
task = make_ai_handler("Сгенерируй задачу")

# Запуск
if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("list", list_students))
    application.add_handler(CommandHandler("broadcast", broadcast))

    application.add_handler(CommandHandler("check", check))
    application.add_handler(CommandHandler("definition", definition))
    application.add_handler(CommandHandler("formula", formula))
    application.add_handler(CommandHandler("theorem", theorem))
    application.add_handler(CommandHandler("task", task))

    application.run_polling()
