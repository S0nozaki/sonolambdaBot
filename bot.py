from telegram.ext import Updater, CommandHandler
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import os
import json
import inspect
import requests
import time

# local imports
from controller import *


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DRIVER_PATH = os.getenv('DRIVER_PATH')
LOG_PATH = os.getenv('SELENIUM_LOG_PATH')
STOCK_EXCHANGES = json.loads(os.getenv('STOCK_EXCHANGES'))

web_service = Service(executable_path=DRIVER_PATH, log_path=LOG_PATH)


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
            exchanges.append((response[0]['symbol'].translate(
                str.maketrans(dict.fromkeys('</em>'))), response[0]['exchange']))
    return exchanges


def scrap_symbol_data(exchange, symbol):
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(
        options=options, service=web_service)
    driver.implicitly_wait(10)
    driver.get(
        "https://es.tradingview.com/chart/?symbol=" + exchange + "%3A" + symbol)
    time.sleep(2)
    price = driver.find_elements(By.CLASS_NAME,
                                 "valueValue-1WIwNaDF")[4].get_attribute("innerText")
    delta = driver.find_elements(By.CLASS_NAME,
                                 "valueValue-1WIwNaDF")[7].get_attribute("innerText").split(' ')[1].strip("()")
    driver.close()
    return {'symbol': symbol, 'exchange': exchange, 'price': price, 'delta': delta}


def get_stock_data(symbol):
    response = ""
    symbol_exchanges = get_symbol_exchanges(symbol)
    if not symbol_exchanges:
        response = "No se encuentra el ticker en ningun exchange"
    else:
        for symbol, exchange in symbol_exchanges:
            data = scrap_symbol_data(exchange, symbol)
            emoji = emoji_picker(data['delta'])
            response += f"\n{symbol} ({exchange}) {data['price']} ({data['delta']}) {emoji}"
    return response


def coti(update, context):
    response = ""
    symbols = update.message.text.upper().split(' ')[1:]
    for symbol in symbols:
        if is_crypto(symbol):
            response += get_crypto_data(symbol)
        elif not is_db_updated():
            reset_table_data(Pairs)
            update_crypto_db(get_crypto_pairs())
            print("DB updated")
            if is_crypto(symbol):
                response += get_crypto_data(symbol)
            else:
                response += get_stock_data(symbol)
        else:
            response += get_stock_data(symbol)
    reply(update.message, response)


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
    daily_delta_URL = 'https://api.binance.com/api/v3/ticker/24hr?symbol=' + symbol
    json['delta'] = requests.get(daily_delta_URL).json()['priceChangePercent']
    emoji = emoji_picker(json['delta'])
    return f"\n{json['symbol']} {json['price']} ({json['delta']}%) {emoji}"


def wallet(update, context):
    user_id = update.message.from_user.id
    user_message = update.message.text.upper().split(' ')
    if len(user_message) == 1:
        symbols_tracked = check_wallet(user_id)
        response = ""
        for symbol, type in symbols_tracked:
            if type == "crypto":
                response += get_crypto_data(symbol)
            else:
                response += get_stock_data(symbol)
        reply(update.message, response)
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

    updater.start_polling()
    print("Listening")

    updater.idle()


if __name__ == "__main__":
    main()
