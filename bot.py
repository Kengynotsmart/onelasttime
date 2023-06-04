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
    reply_markup = ReplyKeyboardMarkup([['/modify_api_key']])
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


def main():
    updater = Updater(token=config.TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('get_info', get_info))
    dispatcher.add_handler(CommandHandler('modify_api_key', modify_api_key_command))
    dispatcher.add_handler(CommandHandler('check_connection', check_connection_command))
    dispatcher.add_handler(CommandHandler('check_balance', check_margin_usdt_balance_command))
    dispatcher.add_handler(MessageHandler(Filters.sticker, sticker))  #if the user sends sticker
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()

if __name__ == '__main__':
    main()
