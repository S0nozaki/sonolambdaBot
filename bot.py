from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv
import os
import inspect

# local imports
from db_controller import update_wallet, check_wallet
from scrapper import get_symbols_data, get_dolar, get_symbol_exchanges, get_crypto_data


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')


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


def coti(update, context):
    symbols = update.message.text.upper().split(' ')[1:]
    reply(update.message, get_symbols_data(symbols))


def wallet(update, context):
    user_id = update.message.from_user.id
    user_message = update.message.text.upper().split(' ')
    if len(user_message) == 1:
        symbols_tracked = check_wallet(user_id)
        reply(update.message, get_symbols_data(symbols_tracked))
    else:
        for symbol_to_modify in user_message[1:]:
            if get_crypto_data(symbol_to_modify):
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
    reply(update.message, get_dolar())


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
