from datetime import date

# local imports
from models import *


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
    symbols_tracked = select(p.symbol for p in Wallet if p.user_id == id)[:]
    return symbols_tracked
