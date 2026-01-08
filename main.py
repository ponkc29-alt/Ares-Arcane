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
# УБЕДИСЬ, ЧТО ТУТ ТВОЙ ТОКЕН БЕЗ ЛИШНИХ ПРОБЕЛОВ!
API_TOKEN = '8509982026:AAFhDIHzfISZZyFqZflCqObNLLhWh30xvpk' 
ADMIN_ID = 5694374929 
ADMIN_LINK = "@Qumestlies"
PORT = 8080 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

async def handle(request):
    return web.Response(text="Bot is running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

class Order(StatesGroup):
    waiting_for_nickname = State()

PRICES = {
    "1000": {"name": "1000 руб. доната", "stars": 20},
    "2000": {"name": "2000 руб. доната", "stars": 40},
    "4250": {"name": "4250 руб. доната", "stars": 70}
}

@dp.message(F.text.startswith('/refund'))
async def refund_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await state.clear()
    args = message.text.split()
    if len(args) < 3: return
    try:
        await bot.refund_star_payment(user_id=int(args[1]), telegram_payment_charge_id=args[2])
        await message.answer("✅ Возврат выполнен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    btns = [[InlineKeyboardButton(text=f"💎 {v['name']}", callback_data=f"order_{k}")] for k, v in PRICES.items()]
    await message.answer("👋 Выберите товар:", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@dp.callback_query(F.data.startswith("order_"))
async def process_order(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(item_key=callback.data.split("_")[1])
    await callback.message.answer("⌨️ Введите ваш НИК:")
    await state.set_state(Order.waiting_for_nickname)
    await callback.answer()

# ИСПРАВЛЕННАЯ ФУНКЦИЯ (проверяем, что пришел именно текст)
@dp.message(Order.waiting_for_nickname)
async def get_nickname(message: types.Message, state: FSMContext):
    # Если прислали не текст (стикер, фото и т.д.) - игнорируем
    if not message.text:
        await message.answer("❌ Пожалуйста, введите ник текстом!")
        return
        
    if message.text.startswith('/'): return
    
    data = await state.get_data()
    item = PRICES.get(data.get('item_key'))
    if not item: return

    await state.update_data(nickname=message.text)
    btns = [[InlineKeyboardButton(text="⭐ Оплатить Звёздами", callback_data="pay_stars")]]
    await message.answer(f"🛒 Заказ: {item['name']}\n👤 Ник: `{message.text}`", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@dp.callback_query(F.data == "pay_stars")
async def pay_stars(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item = PRICES.get(data.get('item_key'))
    if not item: return
    
    await bot.send_invoice(callback.message.chat.id, title=item['name'], description=f"Ник: {data['nickname']}", payload="stars", provider_token="", currency="XTR", prices=[LabeledPrice(label="XTR", amount=item['stars'])])
    await callback.answer()

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment(message: types.Message, state: FSMContext):
    await state.clear()
    tid = message.successful_payment.telegram_payment_charge_id
    uid = message.from_user.id
    await bot.send_message(ADMIN_ID, f"🔔 ОПЛАТА!\nЮзер: `{uid}`\nЧек: `{tid}`\n\n`/refund {uid} {tid}`", parse_mode="Markdown")

async def main():
    await asyncio.gather(start_webserver(), dp.start_polling(bot))

if __name__ == '__main__':
    asyncio.run(main())
