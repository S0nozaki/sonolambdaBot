#!/usr/bin/python3
from pony.orm import *
from dotenv import load_dotenv
import os
import re

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

pattern = "[:/@]"
DB_TYPE, DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME = re.split(
    pattern, DATABASE_URL.replace("://", "/"))


db = Database()


class Pairs(db.Entity):
    symbol = Required(str)


class Updated(db.Entity):
    date = Required(str)


class Wallet(db.Entity):
    user_id = Required(int)
    symbol = Required(str)
    type = Required(str)


db.bind(provider=DB_TYPE, user=DB_USER,
        password=DB_PASS, host=DB_HOST, database=DB_NAME)
db.generate_mapping(create_tables=True)
