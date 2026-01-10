import telebot
from telebot import types
from flask import Flask
import threading

# --- ТВОИ ДАННЫЕ ---
API_TOKEN = '8509982026:AAFhDIHzfISZZyFqZflCqObNLLhWh30xvpk' 
ADMIN_ID = 5694374929
MY_CARD_NUMBER = "5168 7520 2631 0196"

app = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- ГЛАВНАЯ ЛОГИКА ---

@bot.message_handler(commands=['start'])
def start(message):
    # Если пишет админ (ТЫ), бот подтверждает работоспособность
    if message.from_user.id == ADMIN_ID:
        bot.set_my_commands([
            types.BotCommand("start", "Запустить бота"),
            types.BotCommand("refund", "Возврат (ID_ТГ ID_ТРАНЗ)")
        ])
        bot.send_message(ADMIN_ID, "🛡️ Система обновлена. Функция /refund активна и будет работать всегда.")
    
    bot.send_message(message.chat.id, "👋 Привет! Введи свой ник в игре для покупки:")
    bot.register_next_step_handler(message, get_nickname)

def get_nickname(message):
    nickname = message.text
    if not nickname: return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("50 ⭐ — 100 руб.", callback_data=f"buy_50_{nickname}"))
    markup.add(types.InlineKeyboardButton("100 ⭐ — 200 руб.", callback_data=f"buy_100_{nickname}"))
    
    bot.send_message(message.chat.id, f"🎮 Ник: {nickname}\nВыберите количество Звезд:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def choose_pay(call):
    _, amount, nickname = call.data.split('_')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Звезды (Авто)", callback_data=f"stars_{amount}_{nickname}"))
    markup.add(types.InlineKeyboardButton("Карта (Вручную)", callback_data=f"card_{amount}_{nickname}"))
    bot.edit_message_text(f"Ник: {nickname} | Сумма: {amount} ⭐\nВыбери способ оплаты:", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('stars_'))
def pay_stars(call):
    _, amount, nickname = call.data.split('_')
    bot.send_invoice(
        call.message.chat.id,
        title=f"Донат {amount} ⭐",
        description=f"Ник: {nickname}",
        provider_token="", currency="XTR",
        prices=[types.LabeledPrice(label="Звезды", amount=int(amount))],
        invoice_payload=f"{nickname}:{call.from_user.id}"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('card_'))
def pay_card(call):
    bot.send_message(call.message.chat.id, f"💳 Переведите сумму на карту:\n`{MY_CARD_NUMBER}`\n\nПосле оплаты пришлите чек.")

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# --- УВЕДОМЛЕНИЯ ---

@bot.message_handler(content_types=['successful_payment'])
def success(message):
    p = message.successful_payment
    data = p.invoice_payload.split(':')
    # Бот присылает тебе данные, а ты сам вводишь /refund
    report = (
        f"✅ Оплата прошла!\n"
        f"Ник: `{data[0]}`\n"
        f"ID игрока: `{data[1]}`\n"
        f"ID транзакции: `{p.telegram_payment_charge_id}`"
    )
    bot.send_message(ADMIN_ID, report, parse_mode='Markdown')

# --- ВЕЧНАЯ КОМАНДА REFUND (ТЫ ВВОДИШЬ ЕЁ САМ) ---

@bot.message_handler(commands=['refund'])
def make_refund(message):
    if message.from_user.id != ADMIN_ID: return

    args = message.text.split()
    # Проверка: ввел ли ты ID человека и ID транзакции
    if len(args) < 3:
        bot.reply_to(message, "❌ Введи: /refund [ID_ЧЕЛОВЕКА] [ID_ТРАНЗАКЦИИ]")
        return

    try:
        user_id = int(args[1])
        charge_id = args[2]
        
        # Сам процесс возврата
        bot.refund_star_payment(user_id=user_id, telegram_payment_charge_id=charge_id)
        bot.reply_to(message, f"✅ Возврат для {user_id} выполнен! Команда готова к следующему возврату.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
    
