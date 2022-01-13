from telegram.ext import Updater, CommandHandler
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from datetime import date
import inspect
import requests
import time
import yaml
import sqlite3

with open("config.yml", "r") as file_descriptor:
    config = yaml.safe_load(file_descriptor)
    bot_token = config['bot_token']
    driver_path = config['driver_path']
    log_path = config['selenium_log_path']
    stock_exchanges = config['stock_exchanges']
    db = config['db']

web_service = Service(executable_path=driver_path, log_path=log_path)


def is_db_updated(date):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute(f"SELECT * FROM updated WHERE date == '{date}'")
    result = c.fetchall()
    conn.close()
    return bool(result)


def update_crypto_db():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('''CREATE TABLE if not exists pairs(symbol TEXT)''')
    c.execute('''DELETE FROM pairs''')
    pairs = get_crypto_pairs()
    for pair in pairs:
        c.execute("INSERT INTO pairs(symbol) VALUES(?)", [pair])
    c.execute('''CREATE TABLE if not exists updated(date TEXT)''')
    c.execute('''DELETE FROM updated''')
    today = date.today().strftime("%d/%m/%Y")
    c.execute("INSERT INTO updated(date) VALUES(?)", [today])
    conn.commit()
    conn.close()


def is_crypto(symbol):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute(f"SELECT * FROM pairs WHERE symbol == '{symbol}'")
    result = c.fetchall()
    conn.close()
    return bool(result)


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
    for exchange in stock_exchanges:
        URL = 'https://symbol-search.tradingview.com/symbol_search/?text=' + \
            symbol + '&hl=1&exchange=' + exchange + '&lang=es&type=&domain=production'
        response = requests.get(URL).json()
        if response:
            exchanges.append((response[0]['symbol'].strip(
                "<em>/"), response[0]['exchange']))
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
    symbol = update.message.text.split(' ')[1].upper()
    if is_crypto(symbol):
        crypto(update, context)
    else:
        reply(update.message, get_stock_data(symbol))


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


def crypto(update, context):
    tick = update.message.text.split(' ')[1].upper()
    price_URL = 'https://api.binance.com/api/v3/ticker/price?symbol=' + tick
    json = requests.get(price_URL).json()
    daily_delta_URL = 'https://api.binance.com/api/v3/ticker/24hr?symbol=' + tick
    json['delta'] = requests.get(daily_delta_URL).json()['priceChangePercent']
    emoji = emoji_picker(json['delta'])
    final_response = f"{json['symbol']} {json['price']} ({json['delta']}%) {emoji}"
    reply(update.message, final_response)


def start(update, context):
    name = get_user_name(update.message.from_user)
    reply(update.message, f"Bienvenido {name}!")


def help(update, context):
    help_message = inspect.cleandoc("""Estos son los comandos aceptados:
                        /start - Inicializa el bot
                        /help - Lista los comandos disponibles
                        /dolar - Te tira las cotizaciones del dolar
                        /coti {ticker} - Cotización del ticker
                        /crypto {cryptopar} - Cotización del par crypto
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
    updater = Updater(bot_token, use_context=True)
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", help))
    updater.dispatcher.add_handler(CommandHandler("hola", hola))
    updater.dispatcher.add_handler(CommandHandler("dolar", dolar))
    updater.dispatcher.add_handler(CommandHandler("pampa", pampa))
    updater.dispatcher.add_handler(CommandHandler("ggal", ggal))
    updater.dispatcher.add_handler(CommandHandler("coti", coti))
    updater.dispatcher.add_handler(CommandHandler("crypto", crypto))

    updater.start_polling()
    print("Listening")

    updater.idle()


if __name__ == "__main__":
    main()
