import asyncio, re, io
import matplotlib.pyplot as plt
import numpy as np
from aiogram import Bot, Dispatcher, types, F                                                                                                            
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext                                                                                      # Импорт библиотек, обеспечивающих работоспособность бота
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile
from simpleeval import simple_eval
from fractions import Fraction


TOKEN = "8422770401:AAE6sBntHvZSk4Rzd26UrQjvY8VPWnuEikE"        # Токен Telegram

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())                                       # Диспетчер, отвечающий за функции бота

class S(StatesGroup):
    t = State()
    c = State()
    m = State()
    g = State()

def to_mixed(f: Fraction):
    if f.denominator == 1: return str(f.numerator)
    abs_num = abs(f.numerator)
    whole = abs_num // f.denominator
    rem = abs_num % f.denominator
    if whole == 0: return str(f)
    sign = "-" if f.numerator < 0 else ""
    return f"{sign}{whole} {rem}/{f.denominator}"

def get_k():
    b = [[KeyboardButton(text="💰 Налоги"), KeyboardButton(text="🔢 Калькулятор")],     # Функции бота в меню
         [KeyboardButton(text="📊 Среднее"), KeyboardButton(text="📈 График")]]
    return ReplyKeyboardMarkup(keyboard=b, resize_keyboard=True)

def f_t(v: float):
    if v <= 2400000: return v * 0.13, "13%"
    if v <= 5000000: return 312000 + (v - 2400000) * 0.15, "15%"
    if v <= 20000000: return 702000 + (v - 5000000) * 0.18, "18%"
    return 3402000 + (v - 20000000) * 0.20, "20%+"

@dp.message(Command("start"))                                       # Запрос у Telegram имени пользователя при команде "/start"
async def cmd_s(m: types.Message, state: FSMContext):
    await state.clear()
    await m.answer(f"Привет, {m.from_user.first_name}! Я многофункциональный математический бот ✨\nВыбери режим:", reply_markup=get_k())  

@dp.message(F.text == "💰 Налоги")
async def set_t(m: types.Message, state: FSMContext):
    await state.set_state(S.t)
    await m.answer("Введи сумму годового дохода:")

@dp.message(F.text == "🔢 Калькулятор")
async def set_c(m: types.Message, state: FSMContext):
    await state.set_state(S.c)
    await m.answer("Напиши пример (можно степени ² или дроби 1/2):")

@dp.message(F.text == "📊 Среднее")
async def set_m(m: types.Message, state: FSMContext):
    await state.set_state(S.m)
    await m.answer("Введи числа через пробел:")

@dp.message(F.text == "📈 График")
async def set_g(m: types.Message, state: FSMContext):
    await state.set_state(S.g)
    await m.answer("Введи функцию (например: y = 2x² + 5):")

@dp.message(S.t)
async def p_t(m: types.Message):                                                            
    try:                                                                                                  # Использование "try","except" для защиты от вылетов бота
        v = float(m.text.replace(',', '.').replace(' ', ''))
        r, p = f_t(v)
        await m.answer(f"✅\nНалог: {r:,.2f} ({p})\nНа руки: {v - r:,.2f}")
    except: await m.answer("Введи только число своего дохода!")

@dp.message(S.c)
async def p_c(m: types.Message):
    try:
        e = m.text.lower().replace(',', '.').replace(' ', '').replace('^', '**')
        e = e.replace('²', '**2').replace('³', '**3')
        e = re.sub(r'(\d+)([xх])', r'\1*\2', e)                                                            # Авто-подстановка умножения между числом и X
        e = re.sub(r'(\d+)/(\d+)', r'Fraction(\1,\2)', e)
        res = simple_eval(e, functions={'Fraction': Fraction})
        if isinstance(res, Fraction):
            await m.answer(f"🔢\nОбыкновенная: {res}\nСмешанная: {to_mixed(res)}\nДесятичная: {float(res):g}")
        else:
            await m.answer(f"🔢 Результат: {res:g}")
    except: await m.answer("Ошибка в примере!")

@dp.message(S.m)
async def p_m(m: types.Message):
    try:
        n = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", m.text.replace(',', '.'))]                # Поиск всех чисел в строке через регулярные выражения
        if not n: raise ValueError
        res = sum(n)/len(n)
        await m.answer(f"📊 Среднее: {res:g}")
    except: await m.answer("Введи только числовой набор!")

@dp.message(S.g)
async def p_g(m: types.Message):
    try:
        f = m.text.lower().replace(' ', '').replace('y=', '').replace('у=', '').replace('^', '**')
        f = f.replace('²', '**2').replace('³', '**3')
        f = re.sub(r'(\d+)([xх])', r'\1*\2', f)                                                            # Обработка слитного написания функций
        
        x = np.linspace(-10, 10, 400)                                                                      # Создание массива точек для оси X
        y = [simple_eval(f, names={'x': val}) for val in x]

        plt.figure(figsize=(8, 6))                                                                         # Отрисовка графика через Matplotlib
        plt.plot(x, y, label=f"y = {m.text}", color='blue', lw=2)
        plt.axhline(0, color='black', lw=1); plt.axvline(0, color='black', lw=1)                           # Отрисовка осей координат
        plt.grid(True, linestyle='--'); plt.legend()
        
        buffer = io.BytesIO()                                                                              # Создание буфера в памяти для картинки без сохранения на диск
        plt.savefig(buffer, format='png')
        buffer.seek(0); plt.close()

        await m.answer_photo(BufferedInputFile(buffer.read(), filename="graph.png"), caption=f"📈 График {m.text}")
    except: await m.answer("Ошибка! Пиши формулу через x (например: x² + 2x)")

async def run():                                                                                           # Удаление вебхука и запуск опроса сервера
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
 
if __name__ == "__main__":
    asyncio.run(run())

