import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery

# === НАСТРОЙКИ ===
API_TOKEN = '8509982026:AAHnSThVeQKWR4Ux9o5t80J_2OCkZJ3fAGY' 
ADMIN_ID = 5694374929  # Твой ID уже здесь

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 1. СТАРТ
@dp.message(Command("start"))
async def start(message: types.Message):
    btn = [[InlineKeyboardButton(text="⭐ Тест (20 звёзд)", callback_data="buy")]]
    await message.answer("Бот готов. Для возврата используй: /refund ID_ТРАНЗАКЦИИ", 
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=btn))

# 2. ОПЛАТА
@dp.callback_query(F.data == "buy")
async def buy(callback: types.CallbackQuery):
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title="Донат",
        description="Тестовый платеж",
        payload="stars",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Звёзды", amount=20)]
    )

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

# 3. ПОСЛЕ ОПЛАТЫ
@dp.message(F.successful_payment)
async def success(message: types.Message):
    tid = message.successful_payment.telegram_payment_charge_id
    await message.answer(f"✅ Оплачено!\nID Транзакции: `{tid}`", parse_mode="Markdown")
    # Шлем тебе готовую короткую команду
    await bot.send_message(ADMIN_ID, f"Для возврата нажми:\n`/refund {tid}`", parse_mode="Markdown")

# === 4. ТВОЯ КОМАНДА (ТОЛЬКО ID ТРАНЗАКЦИИ) ===
@dp.message(Command("refund"))
async def refund(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Ошибка! Пиши так: `/refund MSC12345...`")
        return

    tid = args[1] # Берем только ID транзакции

    try:
        # Пытаемся вернуть. Мы используем твой ADMIN_ID для инициации.
        # Telegram найдет транзакцию в базе по её уникальному ID (tid).
        await bot.refund_star_payment(
            user_id=ADMIN_ID, 
            telegram_payment_charge_id=tid
        )
        await message.answer(f"✅ Готово! Звёзды по транзакции `{tid}` возвращены.")
    except Exception as e:
        # Если Telegram потребует явный ID пользователя, он напишет это здесь
        await message.answer(f"❌ Ошибка: {e}\n\nПопробуй полный формат, если эта транзакция была не твоя.")

async def main():
    print("БОТ ЗАПУЩЕН")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
