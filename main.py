import telebot
from telebot import types
from flask import Flask
import threading
import os

# --- НАСТРОЙКИ ---
API_TOKEN = '8327010108:AAEAFgn0DcCDiNbfqwhqVhULlKGKKgI_xyc' 
ADMIN_ID = 5694374929
MY_CARD_NUMBER = "5168 7520 2631 0196"

app = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN)

# Flask нужен, чтобы Koyeb видел, что сервис "жив"
@app.route('/')
def home():
    return "Бот активен и работает!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ЛОГИКА БОТА ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Привет! Введи свой ник в игре для покупки доната:")
    bot.register_next_step_handler(message, get_nickname)

def get_nickname(message):
    nickname = message.text
    if not nickname:
        bot.send_message(message.chat.id, "Пожалуйста, введи ник корректно.")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    rates = [
        ("25 ⭐ — 1000 доната", "25"),
        ("50 ⭐ — 2000 доната", "50"),
        ("100 ⭐ — 2500 доната", "100"),
        ("200 ⭐ — 3500 доната", "200"),
        ("300 ⭐ — 5500 доната", "300"),
        ("400 ⭐ — 11500 доната", "400"),
        ("500 ⭐ — 16000 доната", "500"),
        ("1000 ⭐ — 20000 доната", "1000")
    ]
    
    for text, val in rates:
        markup.add(types.InlineKeyboardButton(text, callback_data=f"buy_{val}_{nickname}"))
    
    bot.send_message(message.chat.id, f"🎮 Ник: {nickname}\nВыбери количество звёзд:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def choose_pay(call):
    _, amount, nickname = call.data.split('_')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Звёзды (Авто)", callback_data=f"stars_{amount}_{nickname}"))
    markup.add(types.InlineKeyboardButton("Карта (Вручную)", callback_data=f"card_{amount}_{nickname}"))
    bot.edit_message_text(f"Ник: {nickname} | Сумма: {amount} ⭐\nВыбери способ оплаты:", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('stars_'))
def pay_stars(call):
    _, amount, nickname = call.data.split('_')
    bot.send_invoice(
        call.message.chat.id,
        title=f"Покупка {amount} ⭐",
        description=f"Донат для игрока: {nickname}",
        provider_token="", 
        currency="XTR",
        prices=[types.LabeledPrice(label="Звёзды", amount=int(amount))],
        invoice_payload=f"{nickname}:{call.from_user.id}"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('card_'))
def pay_card(call):
    nickname = call.data.split('_')[2]
    bot.send_message(call.message.chat.id, f"💳 Переведите оплату на карту:\n`{MY_CARD_NUMBER}`\n\nПосле оплаты скиньте скриншот чека в этот чат.")
    bot.send_message(ADMIN_ID, f"📢 Заявка на карту! Ник: `{nickname}`")

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# --- УВЕДОМЛЕНИЕ ВЛАДЕЛЬЦА ---

@bot.message_handler(content_types=['successful_payment'])
def success(message):
    p = message.successful_payment
    data = p.invoice_payload.split(':')
    report = (
        f"✅ ОПЛАТА ЗВЁЗДАМИ!\n"
        f"Ник: `{data[0]}`\n"
        f"ID игрока: `{data[1]}`\n"
        f"Транзакция: `{p.telegram_payment_charge_id}`"
    )
    bot.send_message(ADMIN_ID, report, parse_mode='Markdown')

# --- ЗАПУСК ---

if __name__ == '__main__':
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Удаляем старые обновления, чтобы бот не тормозил
    bot.remove_webhook()
    print("Бот запущен...")
    bot.polling(none_stop=True, skip_pending=True)
