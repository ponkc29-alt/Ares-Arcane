import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# === НАСТРОЙКИ ===
API_TOKEN = '8509982026:AAHnSThVeQKWR4Ux9o5t80J_2OCkZJ3fAGY' 
ADMIN_ID = 5694374929 
ADMIN_LINK = "@Qumestlies"
CARD_UAH = "5168 7520 2631 0196"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Order(StatesGroup):
    waiting_for_nickname = State()

# ТОВАРЫ
PRICES = {
    "1000": {"name": "1000 руб. доната", "stars": 20},
    "2000": {"name": "2000 руб. доната", "stars": 40},
    "4250": {"name": "4250 руб. доната", "stars": 70}
}

# 1. ПРИОРИТЕТНАЯ КОМАНДА ВОЗВРАТА (ВСЕГДА АКТИВНА)
@dp.message(F.text.startswith('/refund'))
async def refund_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.clear() # Полностью "заканчиваем" любые другие действия
    args = message.text.split()
    
    if len(args) < 3:
        await message.answer("⚠️ Пиши: `/refund [UID] [TID]`")
        return

    try:
        target_uid = int(args[1])
        charge_id = args[2]
        await bot.refund_star_payment(user_id=target_uid, telegram_payment_charge_id=charge_id)
        await message.answer(f"✅ ВОЗВРАТ ВЫПОЛНЕН!\nПользователь: `{target_uid}`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка возврата: {e}")

# 2. СТАРТ (СБРОСИТЬ ВСЁ)
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    buttons = [[InlineKeyboardButton(text=f"💎 {v['name']} ({v['stars']} ⭐)", callback_data=f"order_{k}")] for k, v in PRICES.items()]
    buttons.append([InlineKeyboardButton(text="❓ Поддержка", callback_data="support")])
    await message.answer("👋 Бот готов. Выберите товар:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("order_"))
async def process_order(callback: types.CallbackQuery, state: FSMContext):
    item_key = callback.data.split("_")[1]
    await state.update_data(item_key=item_key)
    await callback.message.answer("⌨️ Введите ваш НИК в игре:")
    await state.set_state(Order.waiting_for_nickname)
    await callback.answer()

@dp.message(Order.waiting_for_nickname)
async def get_nickname(message: types.Message, state: FSMContext):
    if message.text.startswith('/'): return # Игнорируем команды

    nickname = message.text
    user_data = await state.get_data()
    item = PRICES[user_data['item_key']]
    await state.update_data(nickname=nickname)
    
    btns = [[InlineKeyboardButton(text="⭐ Звёзды", callback_data="pay_stars")],
            [InlineKeyboardButton(text="💳 Карта", callback_data="pay_card")]]
    await message.answer(f"🛒 Заказ: {item['name']}\n👤 Ник: `{nickname}`", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@dp.callback_query(F.data == "pay_stars")
async def pay_stars(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item = PRICES[data['item_key']]
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=item['name'],
        description=f"Ник: {data['nickname']}",
        payload="stars_payment", 
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Звёзды", amount=item['stars'])]
    )
    await callback.answer()

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

# 3. УСПЕШНАЯ ОПЛАТА (ТУТ МЫ ЗАКАНЧИВАЕМ ПЛАТЕЖ)
@dp.message(F.successful_payment)
async def success_payment(message: types.Message, state: FSMContext):
    await state.clear() # ЗАКАНЧИВАЕМ ПЛАТЕЖ И ОЖИДАНИЕ НИКА
    tid = message.successful_payment.telegram_payment_charge_id
    uid = message.from_user.id
    
    await message.answer(f"✅ Оплачено успешно!")
    
    # Сообщение тебе
    await bot.send_message(ADMIN_ID, f"🔔 **ОПЛАТА!**\n👤 Юзер: `{uid}`\n🆔 Чек: `{tid}`\n\nКоманда возврата:\n`/refund {uid} {tid}`", parse_mode="Markdown")

@dp.callback_query(F.data == "pay_card")
async def pay_card(callback: types.CallbackQuery):
    await callback.message.answer(f"💳 Карта: `{CARD_UAH}`\nСкиньте чек: {ADMIN_LINK}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
