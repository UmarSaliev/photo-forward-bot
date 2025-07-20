import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hbold
import asyncio
import os

BOT_TOKEN = os.getenv("8189283086:AAGR_QF2NuupIZA4G_Fhys_81CU-9-BOWaU")
OWNER_IDS = {95293299, 784341697}  # Замените на реальные Telegram ID владельцев

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

user_names = set()
user_ids = set()

@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("👋 Привет! Отправь фото с заданием, и оно будет переслано учителю.")

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "📖 <b>Доступные команды:</b>\n"
        "/start – Приветствие\n"
        "/help – Справка\n"
        "/list – Список учеников (только для учителя)\n"
        "/status – Проверка статуса\n"
        "/ping – Проверка связи\n"
        "/broadcast – Рассылка от учителя"
    )

@dp.message(Command("list"))
async def list_users(message: Message):
    if message.from_user.id not in OWNER_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    if not user_names:
        await message.answer("Пока никто не присылал фото.")
    else:
        response = "📋 <b>Список учеников:</b>\n"
        for name in user_names:
            response += f"– {hbold(name)}\n"
        await message.answer(response)

@dp.message(Command("status"))
async def status_cmd(message: Message):
    await message.answer("✅ Бот работает исправно.")

@dp.message(Command("ping"))
async def ping_cmd(message: Message):
    await message.answer("Да, да я здесь, не беспокойся")

@dp.message(F.text.startswith("/broadcast"))
async def broadcast_cmd(message: Message):
    if message.from_user.id not in OWNER_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.answer("⚠️ Пожалуйста, напишите текст для рассылки после команды.\nПример: /broadcast Завтра контрольная работа!")
        return

    text_to_send = parts[1]
    success, fail = 0, 0
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, f"📢 Сообщение от учителя:\n{text_to_send}")
            success += 1
        except:
            fail += 1

    await message.answer(f"✅ Рассылка завершена. Успешно: {success}, не удалось: {fail}")

@dp.message(F.photo)
async def handle_photo(message: Message):
    user_names.add(message.from_user.full_name)
    user_ids.add(message.from_user.id)

    for owner_id in OWNER_IDS:
        await message.copy_to(owner_id)

    await message.answer("✅ Фото получено, преподаватель уже смотрит.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
