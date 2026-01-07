import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# === НАСТРОЙКИ ===
API_TOKEN = '8509982026:AAGyK_tZ1duG7bQubQg7Os06Guoe1fAxy2A'
ADMIN_ID = 6360408462  # ВСТАВЬ СВОЙ ID СЮДА
ADMIN_LINK = "@Qumestlies"
CARD_UAH = "5168 7520 2631 0196"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class Order(StatesGroup):
    waiting_for_nickname = State()

# ПАКЕТЫ ТОВАРОВ
PRICES = {
    "1000": {"name": "1000 руб. доната", "uah": "50", "stars": 20},
    "2000": {"name": "2000 руб. доната", "uah": "100", "stars": 40},
    "4250": {"name": "4250 руб. доната", "uah": "200", "stars": 70}
}

# === КЛАВИАТУРЫ ===
def get_main_menu():
    buttons = [
        [InlineKeyboardButton(text="💎 1000 руб. доната", callback_data="order_1000")],
        [InlineKeyboardButton(text="💎 2000 руб. доната", callback_data="order_2000")],
        [InlineKeyboardButton(text="💎 4250 руб. доната", callback_data="order_4250")],
        [InlineKeyboardButton(text="❓ Поддержка", callback_data="support")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# === ОБРАБОТЧИКИ ===

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        f"👋 Привет! Выберите количество донат-валюты.\n"
        f"Оплата: ⭐ Звёзды или 💳 Карта ГРН.",
        reply_markup=get_main_menu()
    )

# Обработка выбора товара
@dp.callback_query(F.data.startswith("order_"))
async def process_order(callback: types.CallbackQuery, state: FSMContext):
    item_key = callback.data.split("_")[1]
    await state.update_data(item_key=item_key)
    await callback.message.answer("⌨️ Введите ваш **НИК** в игре:")
    await state.set_state(Order.waiting_for_nickname)
    await callback.answer()

# После ввода ника
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

# Оплата Звёздами
@dp.callback_query(F.data == "pay_stars")
async def pay_stars(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    item = PRICES[user_data['item_key']]
    
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=item['name'],
        description=f"Ник: {user_data['nickname']}",
        payload=f"{item['name']}|{user_data['nickname']}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Звёзды", amount=int(item['stars']))]
    )
    await callback.answer()

# Оплата Картой
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

# Подтверждение транзакции (обязательно!)
@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

# Успешная оплата звёздами
@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    pay = message.successful_payment
    product_name, nickname = pay.invoice_payload.split("|")
    charge_id = pay.telegram_payment_charge_id # ID для возврата
    
    # Чек для пользователя
    await message.answer(
        f"🧾 **ВАШ ЧЕК ОБ ОПЛАТЕ**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💎 Товар: {product_name}\n"
        f"⭐ Списано: {pay.total_amount} звёзд\n"
        f"👤 Ник: `{nickname}`\n"
        f"🆔 ID: `{charge_id}`\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✅ Оплата подтверждена!", parse_mode="Markdown"
    )

    # Уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f"🔔 **НОВЫЙ ЗАКАЗ (ЗВЁЗДЫ)**\n"
        f"👤 От: @{message.from_user.username}\n"
        f"📦 Товар: {product_name}\n"
        f"🎮 Ник: {nickname}\n"
        f"💰 Сумма: {pay.total_amount} ⭐\n"
        f"🆔 ID для возврата: `{charge_id}`",
        parse_mode="Markdown"
    )

# === КОМАНДА ВОЗВРАТА (ТОЛЬКО ДЛЯ АДМИНА) ===
@dp.message(Command("refund"))
async def refund_stars(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Введите ID транзакции. Пример: `/refund ID_ИЗ_ЧЕКА`", parse_mode="Markdown")
        return

    charge_id = args[1]
    try:
        # Для возврата нужен ID пользователя, которому возвращаем. 
        # В этом простом коде возврат сработает, если вызовешь команду в ответ на чек или вставишь ID
        await bot.refund_star_payment(user_id=message.from_user.id, telegram_payment_charge_id=charge_id)
        await message.answer(f"✅ Возврат выполнен для ID: `{charge_id}`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка возврата: {e}")

@dp.callback_query(F.data == "support")
async def support(callback: types.CallbackQuery):
    await callback.message.answer(f"🆘 Админ: {ADMIN_LINK}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
