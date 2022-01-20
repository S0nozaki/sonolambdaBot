#!/usr/bin/python3
from pony.orm import *
from dotenv import load_dotenv
import os


load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')

db = Database()


class Pairs(db.Entity):
    symbol = Required(str)


class Updated(db.Entity):
    date = Required(str)


class Wallet(db.Entity):
    user_id = Required(int)
    symbol = Required(str)
    type = Required(str)


db.bind(provider='postgres', user=DB_USER,
        password=DB_PASS, host=DB_HOST, database=DB_NAME)
db.generate_mapping(create_tables=True)
