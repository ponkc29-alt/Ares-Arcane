import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery

# === НАСТРОЙКИ ===
API_TOKEN = '8509982026:AAGyK_tZ1duG7bQubQg7Os06Guoe1fAxy2A'
ADMIN_LINK = "@Qumestlies"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# === КЛАВИАТУРЫ ===
def get_main_menu():
    buttons = [
        [InlineKeyboardButton(text="💎 Купить 50 ⭐", callback_data="buy_50")],
        [InlineKeyboardButton(text="💎 Купить 100 ⭐", callback_data="buy_100")],
        [InlineKeyboardButton(text="💎 Купить 500 ⭐", callback_data="buy_500")],
        [InlineKeyboardButton(text="❓ Поддержка", callback_data="support")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# === ОБРАБОТЧИКИ ===

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Это официальный магазин звёзд. Выберите пакет ниже:",
        reply_markup=get_main_menu()
    )

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    amount = int(callback.data.split("_")[1])
    
    # Выставляем счет в Звездах (XTR)
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=f"Покупка {amount} звёзд",
        description=f"Оплата заказа на {amount} звёзд в Ares Arcane",
        payload=f"stars_{amount}",
        provider_token="", # Для звезд пусто
        currency="XTR",
        prices=[LabeledPrice(label="Звёзды", amount=amount)]
    )
    await callback.answer()

# ОБЯЗАТЕЛЬНО: Подтверждение готовности принять платеж
@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Сообщение об успешной оплате
@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    amount = message.successful_payment.total_amount
    await message.answer(
        f"✅ Оплата прошла успешно!\nВы купили {amount} звёзд.\n"
        f"Если они не зачислились, пишите админу: {ADMIN_LINK}"
    )

@dp.callback_query(F.data == "support")
async def process_support(callback: types.CallbackQuery):
    await callback.message.answer(f"🆘 Возникли вопросы? Пишите админу: {ADMIN_LINK}")
    await callback.answer()

# === ЗАПУСК ===
async def main():
    print("--- БОТ ЗАПУЩЕН (ОПЛАТА: ЗВЕЗДЫ) ---")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
