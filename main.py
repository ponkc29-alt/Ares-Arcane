import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# === НАСТРОЙКИ ===
API_TOKEN = '8509982026:AAGyK_tZ1duG7bQubQg7Os06Guoe1fAxy2A'
ADMIN_ID = 5694374929  # Твой ID вставлен сюда
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

# === МЕНЮ ===
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
    await message.answer(
        "👋 Привет! Выберите количество донат-валюты.\nОплата: ⭐ Звёзды или 💳 Карта ГРН.",
        reply_markup=get_main_menu()
    )

# === ЛОГИКА ЗАКАЗА ===
@dp.callback_query(F.data.startswith("order_"))
async def process_order(callback: types.CallbackQuery, state: FSMContext):
    item_key = callback.data.split("_")[1]
    await state.update_data(item_key=item_key)
    await callback.message.answer("⌨️ Введите ваш **НИК** в игре:")
    await state.set_state(Order.waiting_for_nickname)
    await callback.answer()

@dp.message(Order.waiting_for_nickname)
async def get_nickname(message: types.Message, state: FSMContext):
    nickname = message.text
    user_data = await state.get_data()
    item = PRICES[user_data['item_key']]
    await state.update_data(nickname=nickname)
    
    text = (f"🛒 **Ваш заказ:**\n📦 Товар: {item['name']}\n👤 Ник: `{nickname}`\n\nВыберите способ оплаты:")
    buttons = [
        [InlineKeyboardButton(text=f"⭐ Звёзды ({item['stars']})", callback_data="pay_stars")],
        [InlineKeyboardButton(text=f"💳 Карта ({item['uah']} грн)", callback_data="pay_card")]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

# === РАБОТА СО ЗВЕЗДАМИ ===
@dp.callback_query(F.data == "pay_stars")
async def pay_stars(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item = PRICES[data['item_key']]
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=item['name'],
        description=f"Ник: {data['nickname']}",
        payload=f"{item['name']}|{data['nickname']}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Звёзды", amount=int(item['stars']))]
    )
    await callback.answer()

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    pay = message.successful_payment
    charge_id = pay.telegram_payment_charge_id
    
    await message.answer(f"✅ Оплачено!\n🆔 ID транзакции: `{charge_id}`\n(Сохраните его для возврата)", parse_mode="Markdown")
    
    # Уведомление тебе (админу)
    await bot.send_message(ADMIN_ID, f"🔔 **Новая оплата!**\n🆔 ID для возврата: `{charge_id}`")

# === КОМАНДА ВОЗВРАТА (ДЛЯ ТЕБЯ) ===
@dp.message(Command("refund"))
async def refund_stars(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return # Просто игнорируем чужих

    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Формат: `/refund ID_ТРАНЗАКЦИИ`")
        return

    charge_id = args[1]
    try:
        # Пытаемся вернуть звезды пользователю
        await bot.refund_star_payment(
            user_id=message.from_user.id, 
            telegram_payment_charge_id=charge_id
        )
        await message.answer(f"✅ Возврат по транзакции `{charge_id}` выполнен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# === КАРТА И ПОДДЕРЖКА ===
@dp.callback_query(F.data == "pay_card")
async def pay_card(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item = PRICES[data['item_key']]
    await callback.message.answer(f"💳 Карта: `{CARD_UAH}`\nСумма: {item['uah']} грн\nСкиньте чек: {ADMIN_LINK}")
    await callback.answer()

@dp.callback_query(F.data == "support")
async def support(callback: types.CallbackQuery):
    await callback.message.answer(f"🆘 Поддержка: {ADMIN_LINK}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
