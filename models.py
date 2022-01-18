#!/usr/bin/python3
from pony.orm import *
import yaml

with open("config.yml", "r") as file_descriptor:
    config = yaml.safe_load(file_descriptor)
    db_path = config['db_path']

db = Database()


class Pairs(db.Entity):
    symbol = Required(str)


class Updated(db.Entity):
    date = Required(str)


class Wallet(db.Entity):
    user_id = Required(int)
    symbol = Required(str)
    type = Required(str)


db.bind(provider='sqlite', filename=db_path, create_db=True)
db.generate_mapping(create_tables=True)
