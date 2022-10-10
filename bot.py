from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv
import os
import json
import inspect
import requests

# local imports
from controller import *
from scrapper import get_stocks_data, get_dolar


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHROME_PATH = os.getenv('CHROME_PATH')
DRIVER_PATH = os.getenv('DRIVER_PATH')
STOCK_EXCHANGES = json.loads(os.getenv('STOCK_EXCHANGES'))


def get_user_name(user):
    if not user.username:
        return user.first_name
    return user.username


def log(message, response):
    user = message.from_user
    name = get_user_name(user)
    print(message.date)
    print(str(user['id']) + " " + name + ": " + message.text)
    print(response)


def reply(message, response):
    log(message, response)
    message.reply_text(response)


def get_symbol_exchanges(symbol):
    exchanges = []
    for exchange in STOCK_EXCHANGES:
        URL = 'https://symbol-search.tradingview.com/symbol_search/?text=' + \
            symbol + '&hl=1&exchange=' + exchange + '&lang=es&type=&domain=production'
        response = requests.get(URL).json()
        if response:
            exchanges.append(response[0]['exchange'] + ":" + response[0]
                             ['symbol'].translate(str.maketrans(dict.fromkeys('</em>'))))
    return exchanges


def get_symbols_data(symbols):
    requested_stocks = []
    cryptos_data = []
    for symbol in symbols:
        crypto_data = get_crypto_data(symbol)
        if crypto_data:
            cryptos_data.append(crypto_data)
        else:
            symbol_exchanges = get_symbol_exchanges(symbol)
            for symbol in symbol_exchanges:
                requested_stocks.append(symbol)
    stocks_data = get_stocks_data(requested_stocks)
    return cryptos_data + stocks_data


def coti(update, context):
    symbols = update.message.text.upper().split(' ')[1:]
    symbols_data = get_symbols_data(symbols)
    reply(update.message, format_message(symbols_data))


def format_message(symbols_data):
    message = ""
    for symbol in symbols_data:
        message += symbol['symbol'] + " (" + symbol['exchange'] + ") " + symbol['price'] + \
            " " + symbol['delta'] + " " + emoji_picker(symbol['delta'] + "\n")
    return message


def emoji_picker(price_change):
    emoji = ""
    if price_change.strip("-+−%") == "0.00":
        emoji = "😐"
    elif "-" in price_change or "−" in price_change:
        emoji = "😨"
    else:
        emoji = "🚀"
    return emoji


def get_crypto_pairs():
    symbol_pairs_URL = 'https://api.binance.com/api/v3/exchangeInfo'
    symbols = []
    json = requests.get(symbol_pairs_URL).json()
    for pair in json['symbols']:
        symbols.append(pair['symbol'])
    return symbols


def get_crypto_data(symbol):
    price_URL = 'https://api.binance.com/api/v3/ticker/price?symbol=' + symbol
    json = requests.get(price_URL).json()
    if 'code' in json:
        return {}
    else:
        daily_delta_URL = 'https://api.binance.com/api/v3/ticker/24hr?symbol=' + symbol
        json['delta'] = requests.get(daily_delta_URL).json()[
            'priceChangePercent']
        return {"symbol": json['symbol'], "exchange": "BINANCE", "price": json['price'], "delta": json['delta']}


def wallet(update, context):
    user_id = update.message.from_user.id
    user_message = update.message.text.upper().split(' ')
    if len(user_message) == 1:
        symbols_tracked = check_wallet(user_id)
        symbols_data = get_symbols_data(symbols_tracked)
        reply(update.message, format_message(symbols_data))
    else:
        for symbol_to_modify in user_message[1:]:
            if is_crypto(symbol_to_modify):
                update_wallet(user_id, symbol_to_modify, "crypto")
            elif get_symbol_exchanges(symbol_to_modify):
                update_wallet(user_id, symbol_to_modify, "stock")
            else:
                reply(update.message,
                      f"No se pudo añadir {symbol_to_modify} ya que no existe en ningún exchange")
        reply(update.message, f'Modificaciones finalizadas!')


def start(update, context):
    name = get_user_name(update.message.from_user)
    reply(update.message, f"Bienvenido {name}!")


def help(update, context):
    help_message = inspect.cleandoc("""Estos son los comandos aceptados:
                        /start - Inicializa el bot
                        /help - Lista los comandos disponibles
                        /dolar - Te tira las cotizaciones del dolar
                        /coti {ticker} - Cotización del ticker
                        /pampa - Cotización del ticker PAMP
                        /ggal - Cotización del ticker GGAL
                        /hola Te saluda :D
                    """)
    reply(update.message, help_message)


def dolar(update, context):
    URL = 'https://www.dolarsi.com/api/api.php?type=valoresprincipales'
    json = requests.get(URL).json()
    text = ""
    for dolar in json:
        nombredolar = dolar['casa']['nombre']
        if(not nombredolar in ['Dolar Soja', 'Bitcoin', 'Dolar turista', 'Argentina', 'Dolar', 'Dolar Oficial']):
            nombredolar = nombredolar[6:]
            variacion = dolar['casa']['variacion']
            compra = dolar['casa']['compra'][:-1]
            venta = dolar['casa']['venta'][:-1]
            text += inspect.cleandoc(f"""
                    {nombredolar} {variacion}%
                    Compra {compra}   Venta {venta}
                """)
            text += '\n'
    reply(update.message, text)


def hola(update, context):
    name = get_user_name(update.message.from_user)
    reply(update.message, f"Hola {name}! lindo día para comprar PAMPA.")


def pampa(update, context):
    update.message.text = ' PAMP'
    coti(update, context)


def ggal(update, context):
    update.message.text = ' GGAL'
    coti(update, context)


PORT = int(os.getenv('PORT', 5000))


def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", help))
    updater.dispatcher.add_handler(CommandHandler("hola", hola))
    updater.dispatcher.add_handler(CommandHandler("dolar", dolar))
    updater.dispatcher.add_handler(CommandHandler("pampa", pampa))
    updater.dispatcher.add_handler(CommandHandler("ggal", ggal))
    updater.dispatcher.add_handler(CommandHandler("coti", coti))
    updater.dispatcher.add_handler(CommandHandler("wallet", wallet))

    updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=BOT_TOKEN)
    updater.bot.set_webhook('https://sonolambdabot.herokuapp.com/' + BOT_TOKEN)
    print("Listening")

    updater.idle()


if __name__ == "__main__":
    main()
