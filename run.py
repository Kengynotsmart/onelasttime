import json,config
from flask import Flask,request,jsonify,render_template
from binance.exceptions import BinanceAPIException
from binance.client import Client
from binance.enums import *
from telegram import Update, ReplyKeyboardMarkup, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

import multiprocessing
import datetime


app = Flask(__name__, static_url_path='/static', static_folder='static')
client = Client(config.API_KEY, config.API_SECRET,tld='com')

@app.route("/")
def index():
    title="FYP BOT"
    info = client.get_account()
    status = client.get_account_api_trading_status()
    # bot_status = get_telegram_bot_status()  # Replace with your function to get the Telegram bot status
    # return render_template('index.html', bot_status=bot_status, title=title, info=info, status=status)
    return render_template('index.html')
    # return "FYP BOT"

# def get_telegram_bot_status():
#     # Import the necessary Telegram Bot API modules
#     # from telegram import Bot, TelegramError

#     # Initialize your bot with the bot token
#     bot = Bot(config.TELEGRAM_BOT_TOKEN)

#     try:
#         # Get the bot information
#         bot_info = bot.get_me()
#         bot_status = bot_info.status

#         # Return the bot status
#         return bot_status

#     except TelegramError as e:
#         # Handle any errors that occur during API request
#         print(f"Failed to get bot status: {e}")
#         return "Unknown"

#     except Exception as e:
#         # Handle any other exceptions
#         print(f"An error occurred while getting bot status: {e}")
#         return "Unknown"


def get_symbol_precision(symbol):
    symbol_info = client.futures_exchange_info()
    symbol_data = next(filter(lambda x: x['symbol'] == symbol, symbol_info['symbols']), None)
    if symbol_data:
        filters = symbol_data['filters']
        for f in filters:
            if f['filterType'] == 'LOT_SIZE':
                return f['stepSize']
    return None

from decimal import Decimal, getcontext
def order(side, trade_symbol, order_type=ORDER_TYPE_MARKET):
    try:
        if side == 'BUY':
            side_type = Client.SIDE_BUY
        elif side == 'SELL':
            side_type = Client.SIDE_SELL
        else:
            raise ValueError("Invalid side value. Please use 'BUY' or 'SELL'.")

        
        contract_size = config.cost_per_trade * 100  # USD value of the contract
        symbol_price = client.futures_symbol_ticker(symbol=trade_symbol)['price']
        contract_value = contract_size / Decimal(symbol_price)
        precision = get_symbol_precision(trade_symbol)
        trade_quantity = contract_value.quantize(Decimal(precision))

        order_message = f"Order Update: 🃏 {trade_symbol} {order_type} - {side_type} {trade_quantity} "
        order = client.futures_create_order(
            symbol=trade_symbol,
            side=side_type,
            type=order_type,
            quantity=trade_quantity
        )
        return order_message

    except BinanceAPIException as e:
        raise Exception(f"An API exception occurred: {e}")

    except Exception as e:
        raise Exception(f"An exception occurred: {e}")




#     return order
# def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
#     order = client.futures_create_order(
#         symbol="XRPUSDT",
#         side=Client.SIDE_SELL,
#         type=ORDER_TYPE_MARKET,
#         quantity=210.2)

def sendMessage(data, chat_id):
    tg_bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    try:
        print('--->Sending message to Telegram')
        tg_bot.sendMessage(
            chat_id,
            data,
            parse_mode="MARKDOWN",
        )
        return True
    except Exception as e:
        print("[X] Telegram Error:\n>", e)
        return False

@app.route('/webhook',methods=['POST'])
def webhook():
    # print(request)
    data = json.loads(request.data)

    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return{
            "code": "error",
            "message":"Wrong Passphrase"
        }

    print(data['ticker'])
    # print(data['bar'])

    trade_symbol = data['ticker']
    side = data['strategy']['order_action'].upper()
    # quantity = data['strategy']['order_contracts']
    # symbol = data['strategy']['order_contracts']
    order_response = order(side, trade_symbol)


    if order_response:
        # Send a message to Telegram
        chat_id = "1396961777"  # Replace with the actual chat ID of the user
        message = order_response
        sendMessage(message, chat_id)

        return{
            "code":"success",
            "message":"order executed"
        }
    else:
        print("order failed")
        return{
            "code":"error",
            "message":"order failed",
        }

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import config
import logging
import requests
from datetime import datetime
from binance.client import Client

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

logger = logging.getLogger(__name__)

dispatcher = None

def error_handler(update, context):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


def start_command(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardMarkup([['/start']])
    update.message.reply_text('Welcome to the bot! Please choose an option:\n/start\n/modify_api_key\n/get_info\n/check_connection\n/check_balance', reply_markup=reply_markup)

def modify_api_key_command(update: Update, context: CallbackContext):
    update.message.reply_text('Please enter your API key:')
    context.user_data['pending_action'] = 'modify_api_key'

def normal_message(input_text):
    user_messgae = str(input_text).lower()
    if user_messgae in ("hi"):
        return "hi"
    if user_messgae in ("chatgpt"):
        return "I am not chatgpt"
    # if user_messgae in (""):
    #     return
    if user_messgae in ("time","time?"):
        now = datetime.now()
        date_time = now.strftime("%d/%m/%y,%H:%M:%S")
        return str(date_time)
    return "What 7 you say"



def handle_message(update: Update, context: CallbackContext):
    message_text = update.message.text
    pending_action = context.user_data.get('pending_action')

    if pending_action == 'modify_api_key':
        # Store the API key in the config file
        config.API_KEY = message_text
        update.message.reply_text('API key saved. Please enter your API secret.')
        context.user_data['pending_action'] = 'modify_api_secret'
    
    elif pending_action == 'modify_api_secret':
        # Store the API secret in the config file
        config.API_SECRET = message_text

        # Get the updated API key and secret from the config file
        api_key = config.API_KEY
        api_secret = config.API_SECRET

        # Send the API key and secret as a confirmation message to the user
        message = f"API key: {api_key}\n\nAPI secret: {api_secret}\n\nPlease confirm the information or enter /modify_api_key to make changes."
        update.message.reply_text(message)
        context.user_data['pending_action'] = None
    
    elif pending_action == 'get_latest_trade':
        try:
            # Call a Binance API endpoint to get the latest trade
            client = Client(config.API_KEY, config.API_SECRET)
            latest_trades = client.get_recent_trades(symbol=message_text)
            
            if latest_trades:
                latest_trade = latest_trades[0]  # Get the first trade in the list (latest trade)
                trade_time = datetime.fromtimestamp(latest_trade['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                formatted_trade = f"Symbol: {message_text}\n" \
                                  f"ID: {latest_trade['id']}\n" \
                                  f"Price: {latest_trade['price']}\n" \
                                  f"Qty: {latest_trade['qty']}\n" \
                                  f"quoteQty: {latest_trade['quoteQty']}\n" \
                                  f"Time: {trade_time}"
                update.message.reply_text(formatted_trade)
            else:
                update.message.reply_text("No trades found.")

        except Exception as e:
            update.message.reply_text("🔴Failed to retrieve the latest trade. \nError: " + str(e))

        context.user_data['pending_action'] = None
    else:
        response = normal_message(message_text)
        update.message.reply_text(response)
        


def sticker(update: Update, context: CallbackContext):
    reply = update.message.sticker.file_id
    context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=reply)


def get_info(update: Update, context: CallbackContext):
    # Get the API key and secret from the config file
    api_key = config.API_KEY
    api_secret = config.API_SECRET
    message = f"API key: {api_key}\n \nAPI secret: {api_secret}\n\nPlease confirm the information or enter /modify_api_key to make changes."
    update.message.reply_text(message)

def get_latest_trade(update: Update, context: CallbackContext):
    try:
        # Prompt the user for the symbol
        update.message.reply_text("Please enter the symbol (e.g., BTCUSDT):")
        context.user_data['pending_action'] = 'get_latest_trade'

    except Exception as e:
        update.message.reply_text("🔴Failed to retrieve the latest trade. \nError: " + str(e))

def check_connection_command(update: Update, context: CallbackContext):
    try:
        # Call a Binance API endpoint to check the connection
        client = Client(config.API_KEY, config.API_SECRET)
        status = client.get_account_api_trading_status()

        # Check Binance API connection status
        update.message.reply_text("🟢Connected to Binance API")

    except Exception as e:
        # update.message.reply_text("🔴Failed to connect to Binance API. Error: " + str(e))
        update.message.reply_text("🔴Failed to connect to Binance API. \nError: " + str(e))



def check_margin_usdt_balance_command(update: Update, context: CallbackContext):
    try:
        client = Client(config.API_KEY, config.API_SECRET)
        account_info = client.futures_account()
        usdt_balance = None
        for asset in account_info['assets']:
            if asset['asset'] == 'USDT':
                usdt_balance = float(asset['marginBalance'])
                break


        if usdt_balance is not None:
            myr_balance = usdt_balance * 4.61

            update.message.reply_text(f"🟢 USDT Balance in Futures Wallet: {usdt_balance:.2f} USDT ≈ {myr_balance:.2f} MYR")
        else:
            update.message.reply_text("❌ USDT balance not found in Margin Wallet.")

    except Exception as e:
        update.message.reply_text(f"🔴 Failed to connect to Binance API to get margin account info. Error: {e}")


def start_bot():
    updater = Updater(token=config.TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('get_info', get_info))
    dispatcher.add_handler(CommandHandler('modify_api_key', modify_api_key_command))
    dispatcher.add_handler(CommandHandler('check_connection', check_connection_command))
    dispatcher.add_handler(CommandHandler('latest_trade', get_latest_trade))
    dispatcher.add_handler(CommandHandler('check_balance', check_margin_usdt_balance_command))
    dispatcher.add_handler(MessageHandler(Filters.sticker, sticker))  #if the user sends sticker
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()

def start_flask():
    app.run(host='127.0.0.1', port=8888)

if __name__ == '__main__':
    # start_bot()
    # Start Flask application in a separate process
    bot_process = multiprocessing.Process(target=start_bot)
    bot_process.start()
    flask_process = multiprocessing.Process(target=start_flask)
    flask_process.start()
    
