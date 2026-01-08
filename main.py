import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery

# === НАСТРОЙКИ ===
API_TOKEN = 'ВСТАВЬ_СВОЙ_ТОКЕН' 
ADMIN_ID = 5694374929 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Обработка команды /refund максимально просто
@dp.message(F.text.startswith('/refund'))
async def refund_handler(message: types.Message):
    # ПРОВЕРКА: Бот вообще видит твой ID?
    if message.from_user.id != ADMIN_ID:
        print(f"Пришла команда от НЕ АДМИНА: {message.from_user.id}")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("⚠️ Пиши: `/refund MSC123456789`", parse_mode="Markdown")
        return

    charge_id = parts[1]
    
    try:
        # Пытаемся сделать возврат
        await bot.refund_star_payment(user_id=ADMIN_ID, telegram_payment_charge_id=charge_id)
        await message.answer(f"✅ Успех! Звезды по транзакции {charge_id} возвращены.")
    except Exception as e:
        # Если Telegram выдаст ошибку, мы её увидим
        await message.answer(f"❌ Ошибка Telegram: {e}")

# Все остальные функции (старт, инвойсы)
@dp.message(Command("start"))
async def start(message: types.Message):
    btn = [[InlineKeyboardButton(text="⭐ Тест 20 звезд", callback_data="buy")]]
    await message.answer("Бот запущен. Если не работает возврат — проверь ID транзакции.", reply_markup=InlineKeyboardMarkup(inline_keyboard=btn))

@dp.callback_query(F.data == "buy")
async def buy(callback: types.CallbackQuery):
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title="Тест",
        description="Возврат работает!",
        payload="test",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Звёзды", amount=20)]
    )

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def success(message: types.Message):
    tid = message.successful_payment.telegram_payment_charge_id
    await message.answer(f"✅ Оплачено!\nКоманда:\n`/refund {tid}`", parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
