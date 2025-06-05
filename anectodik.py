import pandas as pd
import random
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

#Скрытый токен
def get_token():
    return os.getenv("BOT_TOKEN")
bot = Bot(token=get_token())
dp = Dispatcher(storage=MemoryStorage())
router = Router()

#Базы данных
anekdots = pd.read_excel("anekdots.xlsx")
ratings_file = "ratings.xlsx"

#/start и /help
@router.message(lambda message: message.text in ["/start", "/help"])
async def start(message: Message):
    await message.answer("/category — выбрать категорию\n/topcategories — рейтинг любимых категорий")

#/category
@router.message(lambda message: message.text == "/category")
async def category(message: Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text='Программирование'), KeyboardButton(text='Учёба')],
        [KeyboardButton(text='Работа'), KeyboardButton(text='Общество и Культура')]
    ])
    await message.answer("Выбери категорию:", reply_markup=kb)

#/topcategories
@router.message(lambda message: message.text == "/topcategories")
async def top_categories(message: Message):
    try:
        df = pd.read_excel(ratings_file)
        avg = df.groupby('Категория')['Оценка'].mean().sort_values(ascending=False).head(3)
        txt = '\n'.join([f"{i+1}. {category} — ⭐ {round(score,1)}" for i, (category, score) in enumerate(avg.items())])
        await message.answer("🏆 Топ 3 категории:\n\n" + txt)
    except:
        await message.answer("Пока нет оценок.")

# Категории
@router.message(lambda message: message.text in ['Программирование', 'Учёба', 'Работа', 'Общество и Культура'])
async def shutochki(message: Message):
    category = message.text
    jokes = anekdots[anekdots['Категория'] == category]['Текст'].tolist()
    if not jokes:
        await message.answer("Пока нет анекдотов в этой категории.")
        return

# Рандомайзер шуток и их оценка
    joke = random.choice(jokes)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⭐' * i, callback_data=f"{i}|{category}")] for i in range(1, 6)
    ])
    await message.answer(joke, reply_markup=kb)

#Анализ оценки
@router.callback_query()
async def otvet(call: CallbackQuery):
    stars, category = call.data.split('|')
    username = call.from_user.username or f"id_{call.from_user.id}"
    text = call.message.text
    score = int(stars)

# Обращается к таблице с оценками пользователя
    try:
        df = pd.read_excel(ratings_file)
    except:
        df = pd.DataFrame(columns=['username', 'Текст', 'Оценка', 'Категория'])
    new_row = pd.DataFrame([{
        'username': username,
        'Текст': text,
        'Оценка': score,
        'Категория': category
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(ratings_file, index=False)

    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(f"Спасибо за оценку: {'⭐' * score}")

# Основной запуск
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

asyncio.run(main())