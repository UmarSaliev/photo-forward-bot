import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import aiohttp
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = list(map(int, os.getenv("OWNER_IDS", "").split(","))) if os.getenv("OWNER_IDS") else []
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_USERNAME = "@JalilSupportBot"  # Замените на реальный юзернейм

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def is_owner(update: Update) -> bool:
    """Проверяет, является ли пользователь владельцем"""
    return update.effective_user.id in OWNER_IDS

async def ask_ai(prompt: str) -> str:
    """Запрос к OpenRouter API"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": f"https://t.me/{BOT_USERNAME[1:]}",
        "X-Title": "MathHelperBot"
    }
    payload = {
        "model": "openrouter/meta-llama/llama-3-8b-instruct:free",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"OpenRouter error: {e}")
        return "⚠️ Произошла ошибка при обработке запроса"

# Команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я бот-помощник по математике.\n"
        "Отправьте мне задачу, формулу или теорему."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📚 Доступные команды:\n"
        "/task <текст> - Решить задачу\n"
        "/formula <текст> - Найти формулу\n"
        "/theorem <текст> - Информация о теореме\n"
        "/search <текст/фото> - Поиск информации"
    )
    
    if await is_owner(update):
        help_text += "\n\n👨‍🏫 Команды для учителя:\n/broadcast - Рассылка\n/list - Список учеников"
    
    await update.message.reply_text(help_text)

async def handle_math_request(update: Update, context: ContextTypes.DEFAULT_TYPE, prefix: str):
    """Общий обработчик математических запросов"""
    if not context.args:
        await update.message.reply_text(f"ℹ️ Использование: /{prefix} <запрос>")
        return
    
    prompt = f"{prefix}: {' '.join(context.args)}"
    try:
        response = await ask_ai(prompt)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error in handle_math_request: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при обработке запроса")

async def task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /task"""
    await handle_math_request(update, context, "Реши задачу")

async def formula_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /formula"""
    await handle_math_request(update, context, "Формула")

async def theorem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /theorem"""
    await handle_math_request(update, context, "Теорема")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /search"""
    if update.message.photo:
        await update.message.reply_text("🔍 Анализирую изображение...")
        # Здесь можно добавить обработку фото
    elif context.args:
        await handle_math_request(update, context, "Поиск")
    else:
        await update.message.reply_text("ℹ️ Отправьте текст или фото с задачей")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /broadcast (только для владельцев)"""
    if not await is_owner(update):
        await update.message.reply_text("⛔ Доступ запрещен")
        return
    
    # Реализация рассылки
    await update.message.reply_text("📢 Режим рассылки активирован")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /list (только для владельцев)"""
    if not await is_owner(update):
        await update.message.reply_text("⛔ Доступ запрещен")
        return
    
    # Реализация вывода списка
    await update.message.reply_text("📋 Список учеников")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        response = await ask_ai(update.message.text)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error in handle_text_message: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при обработке сообщения")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фотографий"""
    if OWNER_IDS:
        try:
            photo = update.message.photo[-1].file_id
            caption = (
                f"📸 Фото от пользователя:\n"
                f"ID: {update.message.from_user.id}\n"
                f"Username: @{update.message.from_user.username}"
            )
            
            for owner_id in OWNER_IDS:
                await context.bot.send_photo(
                    chat_id=owner_id,
                    photo=photo,
                    caption=caption
                )
            
            await update.message.reply_text("📤 Фото отправлено учителю!")
        except Exception as e:
            logger.error(f"Error forwarding photo: {e}")
            await update.message.reply_text("⚠️ Не удалось отправить фото")
    else:
        await update.message.reply_text("ℹ️ Фото получено")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error: {context.error}")
    if update.message:
        await update.message.reply_text("⚠️ Произошла внутренняя ошибка")

def main():
    """Запуск бота"""
    application = ApplicationBuilder().token(TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("task", task_command))
    application.add_handler(CommandHandler("formula", formula_command))
    application.add_handler(CommandHandler("theorem", theorem_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("list", list_command))

    # Регистрация обработчиков сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))

    # Регистрация обработчика ошибок
    application.add_error_handler(error_handler)

    logger.info("Бот запущен и готов к работе")
    application.run_polling()

if __name__ == "__main__":
    main()
