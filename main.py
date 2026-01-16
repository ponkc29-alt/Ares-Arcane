import telebot
from telebot import types
from flask import Flask
import threading
import os

# --- НАСТРОЙКИ ---
API_TOKEN = '8327010108:AAFRvJW09qQmgJ7bqZ9XLyAKIItz9YEL_0U' 
ADMIN_ID = 5694374929
MY_CARD_NUMBER = "5168 7520 2631 0196"

app = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN)

@app.route('/')
def home():
    return "Бот активен и работает на Render!"

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

# --- ЛОГИКА МАГАЗИНА ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Привет! Введи свой ник в игре:")
    bot.register_next_step_handler(message, get_nickname)

def get_nickname(message):
    nickname = message.text
    if not nickname: return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    rates = [
        ("25 ⭐ — 1000 доната", "25"), ("50 ⭐ — 2000 доната", "50"),
        ("100 ⭐ — 2500 доната", "100"), ("200 ⭐ — 3500 доната", "200"),
        ("300 ⭐ — 5500 доната", "300"), ("400 ⭐ — 11500 доната", "400"),
        ("500 ⭐ — 16000 доната", "500"), ("1000 ⭐ — 20000 доната", "1000")
    ]
    for text, val in rates:
        markup.add(types.InlineKeyboardButton(text, callback_data=f"buy_{val}_{nickname}"))
    bot.send_message(message.chat.id, f"🎮 Ник: {nickname}\nВыбери пакет:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def choose_pay(call):
    _, amount, nickname = call.data.split('_')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Звёзды (Авто)", callback_data=f"stars_{amount}_{nickname}"))
    markup.add(types.InlineKeyboardButton("Карта (Вручную)", callback_data=f"card_{amount}_{nickname}"))
    bot.edit_message_text(f"Ник: {nickname} | Сумма: {amount} ⭐\nСпособ оплаты:", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

# Оплата звёздами
@bot.callback_query_handler(func=lambda call: call.data.startswith('stars_'))
def pay_stars(call):
    _, amount, nickname = call.data.split('_')
    bot.send_invoice(
        call.message.chat.id,
        title=f"Донат {amount} ⭐",
        description=f"Ник в игре: {nickname}",
        provider_token="", 
        currency="XTR",
        prices=[types.LabeledPrice(label="Звёзды", amount=int(amount))],
        invoice_payload=f"{nickname}:{call.from_user.id}"
    )

# Оплата картой (просто инфо)
@bot.callback_query_handler(func=lambda call: call.data.startswith('card_'))
def pay_card(call):
    _, amount, nickname = call.data.split('_')
    msg = f"💳 Для оплаты картой переведите сумму на:\n`{MY_CARD_NUMBER}`\n\nПосле оплаты скиньте чек админу."
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

# --- СИСТЕМА ПЛАТЕЖЕЙ И ВОЗВРАТОВ ---

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def success(message):
    p = message.successful_payment
    nickname = p.invoice_payload.split(':')[0]
    charge_id = p.telegram_payment_charge_id
    
    # Уведомление пользователю
    bot.send_message(message.chat.id, f"✅ Оплата прошла! Ник {nickname} получит донат.")
    
    # Уведомление тебе (Админу) с ID для возврата
    bot.send_message(ADMIN_ID, f"💰 КАССА ЗВЁЗД!\n👤 Ник: {nickname}\n💎 Сумма: {p.total_amount} ⭐\n🆔 ID Транзакции: `{charge_id}`")

# КОМАНДА ДЛЯ ВОЗВРАТА (РЕФУНД)
@bot.message_handler(commands=['refund'])
def make_refund(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Используй: /refund ID_ТРАНЗАКЦИИ")
            return
        
        charge_id = args[1]
        # Делаем возврат (только для твоего ID как получателя)
        bot.refund_star_payment(ADMIN_ID, charge_id)
        bot.reply_to(message, "✅ Звёзды успешно возвращены пользователю!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка возврата: {e}")

# --- ЗАПУСК ---
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    print("Бот запущен...")
    bot.infinity_polling(timeout=20, skip_pending=True)
    
