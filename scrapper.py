import os
import requests
import json
import datetime
from dotenv import load_dotenv
from websocket import create_connection
from bs4 import BeautifulSoup

load_dotenv()


def get_dolar():
    url = "https://dolarhoy.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0"
    }
    response = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    cotizations = soup.find(class_="cotizacion").find(
        class_="is-vertical").find_all(class_="is-child")
    response = ""
    for cotization in cotizations:
        name = cotization.find("a")
        compra = cotization.find(class_="compra").find(class_="val")
        venta = cotization.find(class_="venta").find(class_="val")
        response += name.text + "\n"
        if compra:
            response += "Compra: " + compra.text + " "
        if venta:
            response += "Venta: " + venta.text + "\n"
    return response


def get_stocks_data(symbols):
    url = "https://www.tradingview.com/accounts/signin/"
    USER = os.getenv("TW_USER")
    PASS = os.getenv("TW_PASS")
    CHART = os.getenv("TW_CHART")
    date = datetime.datetime.now().strftime("%Y_%m_%d-%H-%M")

    data = {"username": USER, "password": PASS, "remember": "on"}
    headers = {
        "Referer":  "https://www.tradingview.com"
    }
    response = requests.post(url=url, data=data, headers=headers)
    user = response.json()["user"]
    token = user["auth_token"]
    session = "qs_" + user["session_hash"][-12:]
    chart_session = "cs_" + user["private_channel"][-12:]
    ws = create_connection(
        'wss://data.tradingview.com/socket.io/websocket?from=chart/' + CHART + '/&date=' + date, headers=headers)
    print("Starting request")
    sendMessage(ws, "set_auth_token", [token])
    sendMessage(ws, "chart_create_session", [chart_session, ""])
    sendMessage(ws, "quote_create_session", [session])
    sendMessage(ws, "quote_set_fields", [session, "base-currency-logoid", "ch", "chp", "currency-logoid", "currency_code", "currency_id", "base_currency_id", "current_session", "description", "exchange", "format", "fractional", "is_tradable",
                "language", "local_description", "listed_exchange", "logoid", "lp", "lp_time", "minmov", "minmove2", "original_name", "pricescale", "pro_name", "short_name", "type", "update_mode", "volume", "value_unit_id"])

    request_symbols_data(ws, session, chart_session, symbols)

    symbols_count = len(symbols)
    symbol_info = []
    while symbols_count > 0:
        try:
            result = ws.recv()
            if result.find("{\"n\"") > -1:
                prices = result.split(",{\"n\"")[1:]
                for price in prices:
                    actions = json.loads(
                        "{\"n\"" + price.split("]")[0])["v"]
                    symbol_info.append({"symbol": actions["short_name"], "exchange": actions["listed_exchange"], "price": str(
                        actions["lp"]), "delta": str(actions["chp"])})
                    symbols_count -= 1
        except Exception as e:
            print(e)
            break
    ws.close()
    return symbol_info


def request_symbols_data(ws, session, chart_session, symbols):
    counter = 0
    previous_symbol = ""
    for symbol in symbols:
        counter += 1
        if counter == 1:
            sendMessage(ws, "quote_add_symbols", [
                session, "={\"adjustment\":\"splits\",\"symbol\":\"" + symbol + "\"}"])
            sendMessage(ws, "resolve_symbol", [
                        chart_session, "sds_sym_1", "={\"adjustment\":\"splits\",\"symbol\":\"" + symbol + "\"}"])
            sendMessage(ws, "create_series", [
                        chart_session, "sds_1", "s1", "sds_sym_1", "1D", 1, ""])
            sendMessage(ws, "quote_fast_symbols", [session, symbol])
        else:
            sendMessage(ws, "quote_remove_symbols", [
                session, "={\"adjustment\":\"splits\",\"currency-id\":\"USD\",\"symbol\":\"" + previous_symbol + "\"}"])
            sendMessage(ws, "quote_add_symbols", [
                        session, "={\"adjustment\":\"splits\",\"symbol\":\"" + symbol + "\"}"])
            sendMessage(ws, "resolve_symbol", [
                        chart_session, "sds_sym_"+str(counter), "={\"adjustment\":\"splits\",\"symbol\":\"" + symbol + "\"}"])
            sendMessage(ws, "modify_series", [
                        chart_session, "sds_1", "s"+str(counter), "sds_sym_"+str(counter), "1D", ""])
        previous_symbol = symbol


def sendMessage(ws, func, args):
    ws.send(createMessage(func, args))


def createMessage(func, args):
    message = json.dumps({
        "m": func,
        "p": args
    }, separators=(',', ':'))
    return "~m~" + str(len(message)) + "~m~" + message