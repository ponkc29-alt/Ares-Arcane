import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# === НАСТРОЙКИ ===
API_TOKEN = '8509982026:AAGyK_tZ1duG7bQubQg7Os06Guoe1fAxy2A'
ADMIN_ID = 6360408462 # ОБЯЗАТЕЛЬНО: Твой ID из @userinfobot
ADMIN_LINK = "@Qumestlies"
CARD_UAH = "5168 7520 2631 0196"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class Order(StatesGroup):
    waiting_for_nickname = State()

# ПАКЕТЫ
PRICES = {
    "1000": {"name": "1000 руб. доната", "uah": "50", "stars": 20},
    "2000": {"name": "2000 руб. доната", "uah": "100", "stars": 40},
    "4250": {"name": "4250 руб. доната", "uah": "200", "stars": 70}
}

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
        f"👋 Привет! Выберите количество донат-валюты.\n"
        "Оплата: ⭐ Звёзды или 💳 Карта ГРН.",
        reply_markup=get_main_menu()
    )

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
    
    text = (f"🛒 **Ваш заказ:**\n"
            f"📦 Товар: {item['name']}\n"
            f"👤 Ник в игре: `{nickname}`\n\n"
            f"Выберите способ оплаты:")
    
    buttons = [
        [InlineKeyboardButton(text=f"⭐ Оплатить Звёздами ({item['stars']})", callback_data="pay_stars")],
        [InlineKeyboardButton(text=f"💳 Оплатить на Карту ({item['uah']} грн)", callback_data="pay_card")]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data == "pay_stars")
async def pay_stars(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    item = PRICES[user_data['item_key']]
    
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=item['name'],
        description=f"Ник: {user_data['nickname']}",
        payload=f"{item['name']}|{user_data['nickname']}", # Передаем товар и ник
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Звёзды", amount=int(item['stars']))]
    )
    await callback.answer()

@dp.callback_query(F.data == "pay_card")
async def pay_card(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    item = PRICES[user_data['item_key']]
    text = (f"💳 **ОПЛАТА НА КАРТУ (ГРН)**\n\n"
            f"💰 Сумма: `{item['uah']}` грн\n"
            f"💳 Карта: `{CARD_UAH}`\n"
            f"👤 Ник: `{user_data['nickname']}`\n\n"
            f"⚠️ **ИНСТРУКЦИЯ:** Оплатите и отправьте **СКРИНШОТ** чека админу: {ADMIN_LINK}")
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    pay = message.successful_payment
    # Разделяем товар и ник из payload
    product_name, nickname = pay.invoice_payload.split("|")
    
    # 🧾 ЧЕК ДЛЯ ПОЛЬЗОВАТЕЛЯ
    user_receipt = (
        f"🧾 **ВАШ ЧЕК ОБ ОПЛАТЕ**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💎 Товар: {product_name}\n"
        f"⭐ Списано: {pay.total_amount} звёзд\n"
        f"👤 Ник в игре: `{nickname}`\n"
        f"🆔 ID транзакции: `{pay.telegram_payment_charge_id[:10]}...`\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✅ Оплата подтверждена. Валюта будет зачислена админом в ближайшее время!"
    )
    await message.answer(user_receipt, parse_mode="Markdown")

    # 🔔 УВЕДОМЛЕНИЕ АДМИНУ
    admin_msg = (
        f"🔔 **НОВЫЙ ЗАКАЗ (ЗВЁЗДЫ)**\n"
        f"👤 От: @{message.from_user.username}\n"
        f"📦 Товар: {product_name}\n"
        f"🎮 Ник: {nickname}\n"
        f"💰 Сумма: {pay.total_amount} ⭐"
    )
    await bot.send_message(ADMIN_ID, admin_msg)

@dp.callback_query(F.data == "support")
async def support(callback: types.CallbackQuery):
    await callback.message.answer(f"🆘 Админ: {ADMIN_LINK}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
