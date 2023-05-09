import os
import openai
import logging
import requests
import random
import pytz
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime
import settings
settings.init()


# Задаем уровень логов
if not os.path.exists('/tmp/mainbot_log/'):
    os.makedirs('/tmp/mainbot_log/')

logging.basicConfig(filename='/tmp/mainbot_log/error.log', level=logging.ERROR,
                    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

logging.basicConfig(filename='/tmp/mainbot_log/info.log', level=logging.INFO,
                    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Инициализация бота
storage = MemoryStorage()
openai.api_key = settings.openai
bot = Bot(token=settings.tg_token)
dp = Dispatcher(bot, storage=storage)

# Функция для получения текущего времени в определенном часовом поясе
def get_time_in_timezone(tz_name):
    tz = pytz.timezone(tz_name)
    current_time = datetime.now(tz)
    return current_time.strftime('%H:%M')

# Функция для отправки сообщения пользователю с приветственным сообщением
async def send_welcome_message(message: types.Message):
    user_name = message.from_user.first_name
    await message.answer(f'''Привет {user_name}!\nРада тебя видеть \U0001F618\n
P.S. Данный бот создан мужчиной для девушек и работает в режиме пилотного проекта.\nПока...
Посмотрим что из этого выйдет!\U0001F609''')

# Функция для обработки нажатия на кнопки Horoscope
async def send_horoscope_message(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("\U0001F4CC На день", callback_data="day"),
        InlineKeyboardButton("\U0001F5D3 На неделю", callback_data="week"),
        InlineKeyboardButton("\U0001F313 На месяц", callback_data="month"),
        InlineKeyboardButton("\U0001F407 На год", callback_data="year"),
    )
    await message.reply("На сколько вы доверяете звёздам?", reply_markup=keyboard)

# Функция для обработки нажатия на кнопки с выбором продолжительности предсказания
async def process_horoscope_callback(callback_query: types.CallbackQuery, state: FSMContext):
    date = callback_query.data # сохраняем выбранную дату в переменную date
    await state.update_data(date=date)  # сохраняем переменную date в контексте коллбека
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Овен\U00002648", callback_data="aries"),
        InlineKeyboardButton("Телец\U00002649", callback_data="taurus"),
        InlineKeyboardButton("Близнецы\U0000264A", callback_data="gemini"),
        InlineKeyboardButton("Рак\U0000264B", callback_data="cancer"),
        InlineKeyboardButton("Лев\U0000264C", callback_data="leo"),
        InlineKeyboardButton("Дева\U0000264D", callback_data="virgo"),
        InlineKeyboardButton("Весы\U0000264E", callback_data="libra"),
        InlineKeyboardButton("Скорпион\U0000264F", callback_data="scorpio"),
        InlineKeyboardButton("Стрелец\U00002650", callback_data="sagittarius"),
        InlineKeyboardButton("Козерог\U00002651", callback_data="capricorn"),
        InlineKeyboardButton("Водолей\U00002652", callback_data="aquarius"),
        InlineKeyboardButton("Рыбы\U00002653", callback_data="pisces"),
    )
    await callback_query.message.edit_text(text="Выберите свой знак зодиака:", reply_markup=keyboard)

# Функция для обработки нажатия на кнопки с выбором знака зодиака
async def process_zodiac_callback(callback_query: types.CallbackQuery, state: FSMContext):
    sign = callback_query.data  # сохраняем выбранный знак в 'sign'
    data = await state.get_data()  # получаем сохранённые переменные из контекста коллбека
    date = data.get("date")  # получаем переменную 'date'
    await get_horoscope(date, sign, callback_query.message.chat.id)  # получаем гороскоп и отправляем его

# Функция парсинга гороскопа
async def get_horoscope(date, sign, chat_id):
    url = f"https://www.marieclaire.ru/astro/{sign}/{date}/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    zodiac = soup.find_all("div", class_="block-text")
    clear_zodiac = zodiac[0].text
    await bot.send_message(chat_id, clear_zodiac, reply_markup=types.ReplyKeyboardRemove())

# Функция для обработки нажатия на кнопку Motivation
async def send_motivation_message(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Для работы \U0001F4BB", callback_data="for_work"),
        InlineKeyboardButton("Для учёбы \U0001F393", callback_data="for_stady"),
        InlineKeyboardButton("Для принятия важного решения \U0001F9E0", callback_data="for_do"),
        InlineKeyboardButton("Для самоуверенности \U0001FAE6", callback_data="for_confidence"),
        InlineKeyboardButton("Для хорошего настроения \U0001F929", callback_data="for_happy"),
        InlineKeyboardButton("Для укрепления взаимоотношений \U0001F498", callback_data="for_heart"),
        InlineKeyboardButton("Для прекращения отношений \U0001F494", callback_data="for_broken_heart"),
    )
    await message.answer("Нажми и подожди\U0001F631\n\nМинутка мотивации для...", reply_markup=keyboard)

# Функция формирования запроса для мотивации в зависимости от нажатой кнопки
async def process_motivation_callback(callback_query: types.CallbackQuery):
    prompt = "Бот, напиши девушке несколько слов мотивации " + callback_query.data
    response_text = generate_response(prompt)
    message = await callback_query.message.answer(response_text)
    return (prompt)

# Функция отправки запроса в OpenAI и получения ответа
def generate_response(prompt):
        completion = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "user", "content": prompt}
  ]
)
        return completion.choices[0].message.content

# Функция для обработки нажатия на кнопки Magic_ball
async def send_magicball_message(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Я готова!", callback_data="ready"),
    )
    await message.answer('''Чётко представь свой вопрос ко мне\n\nМысленно посчитай до пяти \U0001F4AD\n
\U0001D7CF... \n
\U0001D7D0... \n
\U0001D7D1... \n
\U0001D7D2... \n
\U0001D7D3..! \n\n
Готова?''', reply_markup=keyboard)

# Функция отправки сгенерированного рандомного ответа
async def process_magicball_callback(callback_query: types.CallbackQuery):
    response_text = generate_random()
    await callback_query.message.answer(response_text)

# Функция для генерации рандомного ответа из двух списков 'first' и 'second'
def generate_random():
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "lists.txt"))
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    first = [line.strip() for line in lines if line.startswith("first:")]
    second = [line.strip() for line in lines if line.startswith("second:")]
    first = random.choice(first[0][6:].split("/"))
    second = random.choice(second[0][7:].split("/"))
    return f"{first} {second}"

# Определение состояний пользовательской машины
class DreamForm(StatesGroup):
    prompt = State()  # Шаг для запроса текста

# Функция для обработки нажатия на кнопку Dream
async def send_dream_prompt(message: types.Message, state: FSMContext):
    await message.answer("Коротко опиши свой сон:")
    await DreamForm.prompt.set()  # Установка состояния пользователя в "prompt"
    
# Функция "расшифровки" значения сна с помощью OpenAI
async def process_dream_text(message: types.Message, state: FSMContext):
    prompt = "Бот, мне приснилось " + message.text + ". Что это значит?"
    response_text = generate_response(prompt)
    await message.answer(response_text)
    await state.finish()  # Сброс состояния пользователя
  
# Функция для обработки нажатия на кнопку Playlist
async def send_playlist_message(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("\U0001F399 Яндекс Музыка", url="https://music.yandex.ru/playlist/daily"),
        InlineKeyboardButton("\U0001F39A Spotify", url="https://open.spotify.com/collection/playlists"),
        InlineKeyboardButton("\U0001F3B8 Apple Music", url="https://music.apple.com/ru/radio?l=ru"),
        InlineKeyboardButton("\U0001F3B6 VK Music", url="https://vk.com/audio"),
        InlineKeyboardButton("\U0001F50A Сбер Звук", url="https://zvuk.com/waves"),
    )
    await message.reply("Выбери музыкальный сервис", reply_markup=keyboard)
  
# Функция для обработки нажатия на кнопки Info
async def send_info_message(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Telegram", url="https://t.me/Niko_from_Niko"),
        InlineKeyboardButton("VK", url="https://vk.com/nikohaker"),
        InlineKeyboardButton("\U0001F63C GitHub", url="https://github.com/nikohakerinc/OptimisticLadyBot")
        
    )
    await message.answer('''@OptimisticLadyBot V.2.0''', parse_mode=types.ParseMode.HTML, reply_markup=keyboard)
    
# Добавляем хендлеры (обработчики)
dp.register_message_handler(send_welcome_message, commands=["start"])
dp.register_message_handler(send_horoscope_message, commands=['horoscope'])
dp.register_callback_query_handler(process_horoscope_callback, lambda c: c.data in ["day", "week", "month", "year"])
dp.register_callback_query_handler(process_zodiac_callback, lambda c: c.data in ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"])
dp.register_message_handler(send_motivation_message, commands=['motivation'])
dp.register_callback_query_handler(process_motivation_callback, lambda c: c.data in ["for_work", "for_stady", "for_do", "for_confidence", "for_happy", "for_heart", "for_broken_heart"])
dp.register_message_handler(send_magicball_message, commands=['magic_ball'])
dp.register_callback_query_handler(process_magicball_callback, lambda c: c.data == 'ready')
dp.register_message_handler(send_dream_prompt, commands=['dream'])
dp.register_message_handler(process_dream_text, state=DreamForm.prompt)
dp.register_message_handler(send_playlist_message, commands=['playlist'])
dp.register_message_handler(send_info_message, commands=['info'])

#Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    
print ('Bot stoping!')
