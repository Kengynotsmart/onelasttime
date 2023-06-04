from binance.client import Client
import config
# from python-binance import Client

client = Client(config.API_KEY,config.API_SECRET)

candles = client.get_klines(symbol='BTCUSDT',interval=Client.KLINE_INTERVAL_30MINUTE)

print(len(candles))
