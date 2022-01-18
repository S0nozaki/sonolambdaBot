from datetime import date

# local imports
from models import *


def reset_table_data(table):
    db.drop_table(table, if_exists=True, with_all_data=True)
    db.create_tables()


@db_session
def is_db_updated():
    today = date.today().strftime("%d/%m/%Y")
    result = select(p.date for p in Updated if p.date == today).first()
    return bool(result)


@db_session
def update_crypto_db(pairs):
    for pair in pairs:
        Pairs(symbol=pair)
    delete(p for p in Updated)
    today = date.today().strftime("%d/%m/%Y")
    Updated(date=today)


@db_session
def is_crypto(symbol):
    result = select(p.symbol for p in Pairs if p.symbol == symbol).first()
    return bool(result)


@db_session
def update_wallet(id, symbol, type):
    is_symbol_tracked = select(
        p for p in Wallet if p.user_id == id and p.symbol == symbol).first()
    if is_symbol_tracked:
        delete(p for p in Wallet if p.user_id == id and p.symbol == symbol)
    else:
        Wallet(user_id=id, symbol=symbol, type=type)


@db_session
def check_wallet(id):
    symbols_tracked = select((p.symbol, p.type)
                             for p in Wallet if p.user_id == id)[:]
    return symbols_tracked
