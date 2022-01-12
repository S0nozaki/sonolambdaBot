from selenium.webdriver.firefox import service
from telegram.ext import Updater, CommandHandler
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import inspect
import requests
import time
import yaml

with open("config.yml", "r") as file_descriptor:
    config = yaml.safe_load(file_descriptor)
    bot_token = config['bot_token']
    driver_path = config['driver_path']
    log_path = config['selenium_log_path']

web_service = Service(executable_path=driver_path, log_path=log_path)


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


def get_symbol_exchange(symbol):
    URL = 'https://symbol-search.tradingview.com/symbol_search/?text=' + \
        symbol+'&hl=1&exchange=&lang=es&type=&domain=production'
    response = requests.get(URL).json()
    if not response:
        return ""
    return response[0]['exchange']


def coti(update, context):
    final_response = ""
    tick = update.message.text.split(' ')[1].upper()
    exchange = get_symbol_exchange(tick)
    if not exchange:
        final_response = "No se encuentra el ticker en ningun exchange"
    else:
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(
            options=options, service=web_service)
        driver.implicitly_wait(10)
        driver.get(
            "https://es.tradingview.com/chart/?symbol=" + exchange + "%3A" + tick)
        time.sleep(2)
        current = driver.find_elements(By.CLASS_NAME,
                                       "valueValue-1WIwNaDF")[4].get_attribute("innerText")
        delta = driver.find_elements(By.CLASS_NAME,
                                     "valueValue-1WIwNaDF")[7].get_attribute("innerText").split(' ')[1].strip("()")
        driver.close()
        emoji = emoji_picker(delta)
        final_response = f"{tick} ({exchange}) {current} ({delta}) {emoji}"
    log(update.message, final_response)
    update.message.reply_text(final_response)


def emoji_picker(price_change):
    emoji = ""
    if price_change.strip("-+−%") == "0.00":
        emoji = "😐"
    elif "-" in price_change or "−" in price_change:
        emoji = "😨"
    else:
        emoji = "🚀"
    return emoji


def crypto(update, context):
    final_response = ""
    tick = update.message.text.split(' ')[1].upper()
    price_URL = 'https://api.binance.com/api/v3/ticker/price?symbol=' + tick
    json = requests.get(price_URL).json()
    daily_delta_URL = 'https://api.binance.com/api/v3/ticker/24hr?symbol=' + tick
    json['delta'] = requests.get(daily_delta_URL).json()['priceChangePercent']
    emoji = emoji_picker(json['delta'])
    final_response = f"{json['symbol']} {json['price']} ({json['delta']}%) {emoji}"
    log(update.message, final_response)
    update.message.reply_text(final_response)


def start(update, context):
    name = get_user_name(update.message.from_user)
    update.message.reply_text(f"Bienvenido {name}!")


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
    update.message.reply_text(help_message)


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
    update.message.reply_text(text)


def hola(update, context):
    name = get_user_name(update.message.from_user)
    update.message.reply_text(f"Hola {name}! lindo día para comprar PAMPA.")


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
