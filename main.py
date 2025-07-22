import logging
import os
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler
)
import aiohttp
from dotenv import load_dotenv
import atexit
from threading import Timer
import copy

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = list(map(int, os.getenv("OWNER_IDS", "").split(","))) if os.getenv("OWNER_IDS") else []
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_USERNAME = "@JalilSupportBot"
USER_DATA_FILE = "user_data.json"
BACKUP_FILE = "user_data_backup.json"

# Состояния для ConversationHandler
GET_NAME, BROADCAST = range(2)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Улучшенная система хранения данных ---
class UserDataManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.data = cls._load_data()
            cls._instance.lock = False
        return cls._instance
    
    @staticmethod
    def _load_data():
        """Пытаемся загрузить данные из основного или резервного файла"""
        for file_path in [USER_DATA_FILE, BACKUP_FILE]:
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        return {}
    
    def save(self):
        """Безопасное сохранение с резервной копией"""
        if self.lock or not self.data:
            return
            
        self.lock = True
        try:
            temp_file = f"{USER_DATA_FILE}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            
            if os.path.exists(USER_DATA_FILE):
                os.replace(USER_DATA_FILE, BACKUP_FILE)
            
            os.replace(temp_file, USER_DATA_FILE)
            
        except Exception as e:
            logger.error(f"Ошибка сохранения данных: {e}")
        finally:
            self.lock = False
    
    def get(self, user_id: str):
        return self.data.get(user_id, {})
    
    def set(self, user_id: str, full_name: str, username: str):
        self.data[user_id] = {
            "full_name": full_name,
            "username": username or "нет_username"
        }
        self.save()
    
    def get_all(self):
        return copy.deepcopy(self.data)

# Инициализация менеджера данных
user_manager = UserDataManager()

# --- Автосохранение каждые 5 минут ---
def auto_save():
    user_manager.save()
    Timer(300, auto_save).start()

# --- Проверка прав ---
async def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

# --- Регистрация пользователей ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start - начало регистрации пользователя"""
    user = update.effective_user
    user_id = str(user.id)
    
    # Проверяем, есть ли уже данные о пользователе
    if user_manager.get(user_id):
        await update.message.reply_text(
            f"👋 С возвращением, {user.full_name}!\n"
            f"Используйте /help для списка команд"
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "👋 Добро пожаловать! Я - бот для помощи в учебе.\n"
        "Пожалуйста, введите ваше полное имя (как в школе):"
    )
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение имени пользователя и сохранение данных"""
    user = update.effective_user
    full_name = update.message.text
    user_id = str(user.id)
    
    user_manager.set(user_id, full_name, user.username)
    
    await update.message.reply_text(
        f"✅ Спасибо, {full_name}!\n"
        f"Теперь вы можете использовать все функции бота.\n"
        f"Используйте /help для списка команд"
    )
    return ConversationHandler.END

# --- Рассылка сообщений ---
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало рассылки (только для учителей)"""
    if not await is_owner(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ только для учителей")
        return
    
    await update.message.reply_text(
        "📢 Введите сообщение для рассылки (текст или фото с подписью):\n"
        "Для отмены используйте /cancel"
    )
    return BROADCAST

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка рассылки"""
    user_data = user_manager.get_all()
    if not user_data:
        await update.message.reply_text("❌ Нет пользователей для рассылки")
        return ConversationHandler.END
    
    successful = 0
    failed = []
    
    try:
        # Рассылка текста
        if update.message.text:
            for user_id in user_data:
                try:
                    await context.bot.send_message(
                        chat_id=int(user_id),
                        text=f"📢 Сообщение от учителя:\n\n{update.message.text}"
                    )
                    successful += 1
                except Exception as e:
                    failed.append(user_id)
                    logger.error(f"Ошибка отправки для {user_id}: {e}")
        
        # Рассылка фото
        elif update.message.photo:
            photo = update.message.photo[-1].file_id
            caption = update.message.caption or ""
            for user_id in user_data:
                try:
                    await context.bot.send_photo(
                        chat_id=int(user_id),
                        photo=photo,
                        caption=f"📢 {caption}" if caption else "📢 Сообщение от учителя"
                    )
                    successful += 1
                except Exception as e:
                    failed.append(user_id)
                    logger.error(f"Ошибка отправки фото для {user_id}: {e}")
        
        # Отчет
        report = f"✅ Рассылка завершена:\nОтправлено: {successful}\nНе удалось: {len(failed)}"
        if failed:
            report += f"\n\nОшибки у ID: {', '.join(failed[:5])}{'...' if len(failed) > 5 else ''}"
        
        await update.message.reply_text(report)
    
    except Exception as e:
        logger.error(f"Ошибка рассылки: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при рассылке")
    
    return ConversationHandler.END

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена рассылки"""
    await update.message.reply_text("❌ Рассылка отменена")
    return ConversationHandler.END

# --- Обработка медиа от учеников ---
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылает фото учеников учителям (с подписью или без)"""
    try:
        if not update.message.photo:
            return  # Игнорируем сообщения без фото

        user_id = str(update.effective_user.id)
        user_info = user_manager.get(user_id)
        
        # Формируем базовое сообщение
        base_caption = (
            f"📩 От ученика {user_info.get('full_name', 'Неизвестный')}\n"
            f"@{user_info.get('username', 'нет_username')}"
        )
        
        # Добавляем подпись пользователя, если она есть
        full_caption = base_caption
        if update.message.caption:
            full_caption += f"\n\n{update.message.caption}"
        
        # Отправка всем учителям
        for teacher_id in OWNER_IDS:
            try:
                await context.bot.send_photo(
                    chat_id=teacher_id,
                    photo=update.message.photo[-1].file_id,
                    caption=full_caption if full_caption else None
                )
            except Exception as e:
                logger.error(f"Ошибка отправки учителю {teacher_id}: {e}")
        
        await update.message.reply_text("✅ Ваше фото отправлено учителям")
    
    except Exception as e:
        logger.error(f"Ошибка в handle_media: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при отправке фото")

# --- Команды ИИ ---
async def ask_ai(prompt: str, context: str = "") -> str:
    """Функция для взаимодействия с ИИ через OpenRouter"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{context}\n\n{prompt}"}
        ]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error = await response.text()
                    logger.error(f"Ошибка API: {error}")
                    return "⚠️ Произошла ошибка при обработке запроса"
    except Exception as e:
        logger.error(f"Ошибка соединения: {e}")
        return "⚠️ Не удалось соединиться с сервером ИИ"

async def task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Решение задачи"""
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите задачу после команды /task")
        return
    
    task = " ".join(context.args)
    await update.message.reply_text("🔍 Решаю задачу...")
    
    response = await ask_ai(
        f"Реши эту задачу по шагам: {task}",
        "Ты опытный преподаватель. Реши задачу подробно с объяснениями каждого шага."
    )
    
    await update.message.reply_text(f"📚 Решение задачи:\n\n{response}")

async def formula_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Объяснение формулы"""
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите формулу после команды /formula")
        return
    
    formula = " ".join(context.args)
    await update.message.reply_text("🔍 Объясняю формулу...")
    
    response = await ask_ai(
        f"Объясни эту формулу: {formula}",
        "Ты опытный преподаватель. Объясни формулу простым языком с примерами."
    )
    
    await update.message.reply_text(f"📖 Объяснение формулы:\n\n{response}")

async def theorem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Объяснение теоремы"""
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите теорему после команды /theorem")
        return
    
    theorem = " ".join(context.args)
    await update.message.reply_text("🔍 Объясняю теорему...")
    
    response = await ask_ai(
        f"Объясни эту теорему: {theorem}",
        "Ты опытный преподаватель. Объясни теорему с доказательством и примерами."
    )
    
    await update.message.reply_text(f"📖 Объяснение теоремы:\n\n{response}")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск информации"""
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите запрос после команды /search")
        return
    
    query = " ".join(context.args)
    await update.message.reply_text("🔍 Ищу информацию...")
    
    response = await ask_ai(
        f"Найди информацию по запросу: {query}",
        "Ты опытный преподаватель. Дай развернутый ответ на запрос с примерами."
    )
    
    await update.message.reply_text(f"🔎 Результаты поиска:\n\n{response}")

# --- Команда списка пользователей ---
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список пользователей (только для учителей)"""
    if not await is_owner(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ только для учителей")
        return
    
    user_data = user_manager.get_all()
    if not user_data:
        await update.message.reply_text("❌ Нет зарегистрированных пользователей")
        return
    
    message = ["📝 Список пользователей:"]
    for user_id, data in user_data.items():
        message.append(
            f"👤 {data.get('full_name', 'Неизвестный')} "
            f"(@{data.get('username', 'нет_username')}) "
            f"ID: {user_id}"
        )
    
    # Разбиваем сообщение на части, если оно слишком длинное
    full_message = "\n".join(message)
    for i in range(0, len(full_message), 4096):
        await update.message.reply_text(full_message[i:i+4096])

# --- Обновленная help-команда ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/task - Решить задачу\n"
        "/formula - Объяснить формулу\n"
        "/theorem - Объяснить теорему\n"
        "/search - Найти информацию\n"
    )
    
    if await is_owner(update.effective_user.id):
        help_text += (
            "\n👨‍🏫 Команды учителя:\n"
            "/list - Список учеников\n"
            "/broadcast - Рассылка сообщений"
        )
    
    await update.message.reply_text(help_text)

# --- Запуск бота ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Обработчики
    app.add_handler(MessageHandler(filters.PHOTO, handle_media))  # Ловим ВСЕ фото
    
    # ConversationHandler для рассылки
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_command)],
        states={
            BROADCAST: [
                MessageHandler(filters.TEXT | filters.PHOTO, handle_broadcast),
                CommandHandler("cancel", cancel_broadcast)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_broadcast)]
    ))
    
    # ConversationHandler для регистрации
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={GET_NAME: [MessageHandler(filters.TEXT, get_name)]},
        fallbacks=[]
    ))

    # Регистрация команд
    commands = [
        ("help", help_command),
        ("task", task_command),
        ("formula", formula_command),
        ("theorem", theorem_command),
        ("search", search_command),
        ("list", list_command)
    ]
    for cmd, handler in commands:
        app.add_handler(CommandHandler(cmd, handler))

    # Обработка ошибок
    app.add_error_handler(lambda u, c: logger.error(c.error))
    
    # Система автосохранения
    auto_save()
    atexit.register(user_manager.save)
    
    logger.info("Бот запущен с функцией рассылки")
    app.run_polling()

if __name__ == "__main__":
    main()
