import json,config
from flask import Flask,request,jsonify,render_template
from binance.exceptions import BinanceAPIException
from binance.client import Client
from binance.enums import *
# from bot import start_bot, dispatcher, Update
app = Flask(__name__, static_url_path='/static', static_folder='static')

client = Client(config.API_KEY, config.API_SECRET,tld='com')

@app.route("/")
def index():
    title="FYP BOT"
    info = client.get_account()
    status = client.get_account_api_trading_status()
    return render_template('index.html')
    # return "FYP BOT"

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

        print(f"Sending order: {order_type} - {side_type} {trade_quantity} {trade_symbol}")
        order = client.futures_create_order(
            symbol=trade_symbol,
            side=side_type,
            type=order_type,
            quantity=trade_quantity
        )
        return order

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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8888, debug=True)
