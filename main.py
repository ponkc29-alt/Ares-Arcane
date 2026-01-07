import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# === НАСТРОЙКИ ===
API_TOKEN = '8509982026:AAGyK_tZ1duG7bQubQg7Os06Guoe1fAxy2A' # Вставь сюда токен!
ADMIN_LINK = "@Qumestlies" # Замени на свой ник в Телеграм

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# === КЛАВИАТУРЫ ===
def get_main_menu():
    buttons = [
        [InlineKeyboardButton(text="⭐ 50 звёзд — 100 руб.", callback_data="buy_50_100")],
        [InlineKeyboardButton(text="⭐ 100 звёзд — 200 руб.", callback_data="buy_100_200")],
        [InlineKeyboardButton(text="⭐ 500 звёзд — 950 руб.", callback_data="buy_500_950")],
        [InlineKeyboardButton(text="❓ Поддержка / Контакты", callback_data="support")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="to_main")]
    ])

# === ОБРАБОТЧИКИ (ЛОГИКА) ===

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Это магазин звёзд. Выберите нужное количество ниже.\n"
        "Оплата принимается в **рублях (RUB)**.",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    # Разбиваем данные из кнопки (например: buy_50_100)
    data = callback.data.split("_")
    stars = data[1]
    price = data[2]
    
    text = (
        f"💎 **Заказ: {stars} звёзд**\n"
        f"💰 **К оплате: {price} руб.**\n\n"
        "💳 Для оплаты переведите сумму на карту или кошелёк:\n"
        "`1234 5678 1234 5678` (Пример)\n\n"
        "После оплаты пришлите скриншот чека админу: " + ADMIN_LINK
    )
    
    await callback.message.edit_text(text=text, reply_markup=get_back_button(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите количество звёзд для покупки:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "support")
async def process_support(callback: types.CallbackQuery):
    await callback.message.answer(f"🆘 Возникли вопросы? Пишите админу: {ADMIN_LINK}")
    await callback.answer()

# === ЗАПУСК ===
async def main():
    print("--- БОТ ЗАПУЩЕН (ВАЛЮТА: РУБЛИ) ---")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
