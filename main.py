import asyncio
import os # Добавили для работы с переменными окружения
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# СОВЕТ: На хостинге лучше использовать os.getenv("TOKEN"), 
# но для проверки можно оставить и так
TOKEN = '8787703491:AAFXYfR4c48SbJr40GdHGGprJ1aOQdjG3qI'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# БАЗА ДАННЫХ (в оперативной памяти)
queue = []  
chats = {}  
profiles = {}

# ФУНКЦИИ ДЛЯ КНОПОК
def get_gender_kb():
    b1 = types.KeyboardButton(text="Я парень 👦")
    b2 = types.KeyboardButton(text="Я девушка 👧")
    return types.ReplyKeyboardMarkup(keyboard=[[b1, b2]], resize_keyboard=True)

def get_main_kb():
    b1 = types.KeyboardButton(text="🔍 Найти собеседника")
    return types.ReplyKeyboardMarkup(keyboard=[[b1]], resize_keyboard=True)

def get_stop_kb():
    b1 = types.KeyboardButton(text="❌ Остановить чат")
    return types.ReplyKeyboardMarkup(keyboard=[[b1]], resize_keyboard=True)

# ОБРАБОТКА КОМАНДЫ /START
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    uid = message.from_user.id
    if uid not in profiles:
        await message.answer("Привет! Давай создадим анкету. Кто ты?", reply_markup=get_gender_kb())
    else:
        await message.answer("Ты уже в системе! Жми поиск.", reply_markup=get_main_kb())

# ВЫБОР ПОЛА
@dp.message(F.text.in_(["Я парень 👦", "Я девушка 👧"]))
async def gender_handler(message: types.Message):
    uid = message.from_user.id
    gender = "Парень" if "парень" in message.text.lower() else "Девушка"
    profiles[uid] = {"gender": gender}
    await message.answer("Напиши свой возраст (только число, например: 18):", reply_markup=types.ReplyKeyboardRemove())

# ВВОД ВОЗРАСТА
@dp.message(lambda m: m.text.isdigit())
async def age_handler(message: types.Message):
    uid = message.from_user.id
    # ИСПРАВЛЕНО: Проверяем, что юзер уже выбрал пол, но еще не ввел возраст
    if uid in profiles and "age" not in profiles[uid]:
        age = int(message.text)
        if 12 < age < 90:
            profiles[uid]["age"] = age
            await message.answer(f"Анкета сохранена! Ты {profiles[uid]['gender']}, {age} лет.", reply_markup=get_main_kb())
        else:
            await message.answer("Пожалуйста, введи реальный возраст (от 13 до 89).")

# ПОИСК СОБЕСЕДНИКА
@dp.message(F.text == "🔍 Найти собеседника")
async def search_handler(message: types.Message):
    uid = message.from_user.id
    
    if uid not in profiles or "age" not in profiles[uid]:
        return await message.answer("Сначала заполни анкету через /start")
    
    if uid in chats or uid in queue:
        return await message.answer("Ты уже в поиске или в чате!")

    if len(queue) > 0:
        partner_id = queue.pop(0)
        # Проверка, не пытается ли юзер найти самого себя (если нажал дважды)
        if partner_id == uid:
            queue.append(uid)
            return

        chats[uid] = partner_id
        chats[partner_id] = uid
        
        info_me = f"{profiles[uid]['gender']}, {profiles[uid]['age']} лет"
        info_partner = f"{profiles[partner_id]['gender']}, {profiles[partner_id]['age']} лет"
        
        await bot.send_message(uid, f"Собеседник найден: {info_partner}!", reply_markup=get_stop_kb())
        await bot.send_message(partner_id, f"Собеседник найден: {info_me}!", reply_markup=get_stop_kb())
    else:
        queue.append(uid)
        await message.answer("Ищем кого-то... 🔍", reply_markup=types.ReplyKeyboardRemove())

# ОСТАНОВКА ЧАТА
@dp.message(F.text == "❌ Остановить чат")
async def stop_handler(message: types.Message):
    uid = message.from_user.id
    if uid in chats:
        pid = chats.pop(uid)
        if pid in chats: chats.pop(pid)
        await bot.send_message(uid, "Диалог завершен.", reply_markup=get_main_kb())
        await bot.send_message(pid, "Собеседник отключился.", reply_markup=get_main_kb())
    elif uid in queue:
        queue.remove(uid)
        await message.answer("Поиск отменен.", reply_markup=get_main_kb())

# ПЕРЕСЫЛКА СООБЩЕНИЙ
@dp.message()
async def forward_handler(message: types.Message):
    uid = message.from_user.id
    if uid in chats:
        try:
            # ИСПРАВЛЕНО: Добавлен отступ (Tab) перед await
            await message.copy_to(chat_id=chats[uid])
        except:
            await message.answer("Не удалось отправить сообщение.")
    elif message.text != "🔍 Найти собеседника":
        # Чтобы бот не спамил на каждое сообщение вне чата
        if uid in profiles and "age" in profiles[uid]:
            await message.answer("Нажми кнопку поиска!", reply_markup=get_main_kb())

# ЗАПУСК
async def main_func(): # Переименовал, чтобы не путалось с файлом
    print("БОТ ЗАПУЩЕН!")
    await dp.start_polling(bot)

# ИСПРАВЛЕНО: Правильное написание условия запуска (__name__ и двойные подчёркивания)
if __name__ == "__main__":
    asyncio.run(main_func())
  
