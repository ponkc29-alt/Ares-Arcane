import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# === НАСТРОЙКИ ===
API_TOKEN = '8509982026:AAGyK_tZ1duG7bQubQg7Os06Guoe1fAxy2A'
ADMIN_ID = 5694374929  # Твой ID. Только ты сможешь делать возврат.
ADMIN_LINK = "@Qumestlies"
CARD_UAH = "5168 7520 2631 0196"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class Order(StatesGroup):
    waiting_for_nickname = State()

PRICES = {
    "1000": {"name": "1000 руб. доната", "uah": "50", "stars": 20},
    "2000": {"name": "2000 руб. доната", "uah": "100", "stars": 40},
    "4250": {"name": "4250 руб. доната", "uah": "200", "stars": 70}
}

# === ГЛАВНОЕ МЕНЮ ===
def get_main_menu():
    buttons = [
        [InlineKeyboardButton(text="💎 1000 руб. доната", callback_data="order_1000")],
        [InlineKeyboardButton(text="💎 2000 руб. доната", callback_data="order_2000")],
        [InlineKeyboardButton(text="💎 4250 руб. доната", callback_data="order_4250")],
        [InlineKeyboardButton(text="❓ Поддержка", callback_data="support")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("👋 Магазин готов! Выберите товар:", reply_markup=get_main_menu())

# === ПРОЦЕСС ЗАКАЗА ===
@dp.callback_query(F.data.startswith("order_"))
async def process_order(callback: types.CallbackQuery, state: FSMContext):
    item_key = callback.data.split("_")[1]
    await state.update_data(item_key=item_key)
    await callback.message.answer("⌨️ Введите ваш НИК в игре:")
    await state.set_state(Order.waiting_for_nickname)
    await callback.answer()

@dp.message(Order.waiting_for_nickname)
async def get_nickname(message: types.Message, state: FSMContext):
    nickname = message.text
    user_data = await state.get_data()
    item = PRICES[user_data['item_key']]
    await state.update_data(nickname=nickname)
    
    buttons = [
        [InlineKeyboardButton(text=f"⭐ Звёзды ({item['stars']})", callback_data="pay_stars")],
        [InlineKeyboardButton(text=f"💳 Карта ({item['uah']} грн)", callback_data="pay_card")]
    ]
    await message.answer(f"📦 {item['name']}\n👤 Ник: {nickname}\nВыберите способ оплаты:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# === ОПЛАТА ЗВЕЗДАМИ ===
@dp.callback_query(F.data == "pay_stars")
async def pay_stars(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item = PRICES[data['item_key']]
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=item['name'],
        description=f"Ник: {data['nickname']}",
        payload="stars_order",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Звёзды", amount=item['stars'])]
    )
    await callback.answer()

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    pay = message.successful_payment
    charge_id = pay.telegram_
