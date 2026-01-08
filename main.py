import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# === НАСТРОЙКИ ===
API_TOKEN = 'ВСТАВЬ_СВОЙ_ТОКЕН_ТУТ' 
ADMIN_ID = 5694374929 
ADMIN_LINK = "@Qumestlies"
CARD_UAH = "5168 7520 2631 0196"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class Order(StatesGroup):
    waiting_for_nickname = State()

# ТВОИ ТОВАРЫ И ЦЕНЫ (Звезды: 20, 40, 70)
PRICES = {
    "1000": {"name": "1000 руб. доната", "uah": "50", "stars": 20},
    "2000": {"name": "2000 руб. доната", "uah": "100", "stars": 40},
    "4250": {"name": "4250 руб. доната", "uah": "200", "stars": 70}
}

def get_main_menu():
    buttons = [[InlineKeyboardButton(text=f"💎 {v['name']}", callback_data=f"order_{k}")] for k, v in PRICES.items()]
    buttons.append([InlineKeyboardButton(text="❓ Поддержка", callback_data="support")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("👋 Привет! Выберите количество доната для покупки:", reply_markup=get_main_menu())

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
        [InlineKeyboardButton(text="⭐ Оплатить Звёздами", callback_data="pay_stars")],
        [InlineKeyboardButton(text="💳 Оплатить на Карту", callback_data="pay_card")]
    ]
    await message.answer(
        f"🛒 **Ваш заказ:**\nТОВАР: {item['name']}\nНИК: `{nickname}`\n\nВыберите способ оплаты:", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), 
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "pay_stars")
async def pay_stars(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item = PRICES[data['item_key']]
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=item['name'],
        description=f"Пополнение для ника: {data['nickname']}",
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
    tid = message.successful_payment.telegram_payment_charge_id
    # Сообщение пользователю
    await message.answer(f"✅ Оплата прошла успешно!\n🆔 ID транзакции: `{tid}`\nОжидайте зачисления доната.", parse_mode="Markdown")
    
    # Сообщение ТЕБЕ (админу) с готовой командой возврата
    await bot.send_message(
        ADMIN_ID, 
        f"🔔 **НОВАЯ ОПЛАТА!**\n💎 Товар: {message.successful_payment.total_amount} звёзд\n🆔 ID: `{tid}`\n\nЧтобы вернуть звёзды, нажми:\n`/refund {tid}`",
        parse_mode="Markdown"
    )

# === БЕЗОПАСНАЯ КОМАНДА ВОЗВРАТА (ТОЛЬКО ДЛЯ ТЕБЯ) ===
@dp.message(F.text.startswith('/refund'))
async def refund_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return # Игнорируем всех, кроме тебя

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("⚠️ Пиши так: `/refund MSC_12345...`")
        return

    charge_id = parts[1]
    
    try:
        # Прямой возврат через Telegram
        await bot.refund_star_payment(user_id=ADMIN_ID, telegram_payment_charge_id=charge_id)
        await message.answer(f"✅ Возврат выполнен!\nТранзакция `{charge_id}` аннулирована.")
    except Exception as e:
        await message.answer(f"❌ Ошибка возврата: {e}")

@dp.callback_query(F.data == "pay_card")
async def pay_card(callback: types.CallbackQuery):
    await callback.message.answer(f"💳 Переведите сумму на карту:\n`{CARD_UAH}`\n\nПосле оплаты отправьте чек: {ADMIN_LINK}", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "support")
async def support(callback: types.CallbackQuery):
    await callback.message.answer(f"🆘 По всем вопросам пишите: {ADMIN_LINK}")
    await callback.answer()

async def main():
    print("--- БОТ ЗАПУЩЕН И ГОТОВ К ПРОДАЖАМ ---")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
