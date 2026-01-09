import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# === НАСТРОЙКИ ===
API_TOKEN = 'ВСТАВЬ_СВОЙ_ТОКЕН_БОТА' # Твой токен от BotFather
ADMIN_ID = 5694374929 # Твой ID
PORT = 8080 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- ВЕБ-СЕРВЕР ДЛЯ ПОДДЕРЖКИ ЖИЗНИ (ЧТОБЫ НЕ ЗАСЫПАЛ) ---
async def handle(request):
    return web.Response(text="Bot is Alive!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

# --- ЛОГИКА БОТА ---
class Order(StatesGroup):
    waiting_for_nickname = State()

PRICES = {
    "1000": {"name": "1000 руб. доната", "stars": 20, "amount": 1000},
    "2000": {"name": "2000 руб. доната", "stars": 40, "amount": 2000},
    "4250": {"name": "4250 руб. доната", "stars": 70, "amount": 4250}
}

@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    btns = [[InlineKeyboardButton(text=f"💎 {v['name']} — ⭐{v['stars']}", callback_data=f"order_{k}")] for k, v in PRICES.items()]
    await message.answer("👋 Бот активен! Выберите сумму пополнения:", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@dp.callback_query(F.data.startswith("order_"))
async def process_order(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(item_key=callback.data.split("_")[1])
    await callback.message.answer("⌨️ Введите ваш НИК в SAMP:")
    await state.set_state(Order.waiting_for_nickname)
    await callback.answer()

@dp.message(Order.waiting_for_nickname)
async def get_nickname(message: types.Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    data = await state.get_data()
    item = PRICES[data['item_key']]
    btn = [[InlineKeyboardButton(text="⭐ Оплатить Звёздами", callback_data="pay")]]
    await message.answer(f"🛒 Заказ: {item['name']}\n👤 Ник: {message.text}", reply_markup=InlineKeyboardMarkup(inline_keyboard=btn))

@dp.callback_query(F.data == "pay")
async def pay(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item = PRICES[data['item_key']]
    await bot.send_invoice(callback.message.chat.id, title=item['name'], description=f"Ник: {data['nickname']}", payload="stars", provider_token="", currency="XTR", prices=[LabeledPrice(label="XTR", amount=item['stars'])])
    await callback.answer()

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    nick = data.get('nickname')
    amt = PRICES[data['item_key']]['amount']
    # Сообщение ТЕБЕ в личку
    await bot.send_message(ADMIN_ID, f"🔔 ОПЛАТА!\n👤 Ник: {nick}\n💰 Сумма: {amt} руб.\n\n✅ Оплата прошла. Выдай донат вручную!")
    # Сообщение ИГРОКУ
    await message.answer(f"🎉 Спасибо! Донат на ник {nick} будет зачислен в ближайшее время.")
    await state.clear()

async def main():
    await asyncio.gather(start_webserver(), dp.start_polling(bot))

if __name__ == '__main__':
    asyncio.run(main())
    
