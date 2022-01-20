#!/usr/bin/python3
from pony.orm import *
import yaml

with open("config.yml", "r") as file_descriptor:
    config = yaml.safe_load(file_descriptor)
    db_user = config['db_user']
    db_pass = config['db_pass']
    db_host = config['db_host']
    db_name = config['db_name']

db = Database()


class Pairs(db.Entity):
    symbol = Required(str)


class Updated(db.Entity):
    date = Required(str)


class Wallet(db.Entity):
    user_id = Required(int)
    symbol = Required(str)
    type = Required(str)


db.bind(provider='postgres', user=db_user,
        password=db_pass, host=db_host, database=db_name)
db.generate_mapping(create_tables=True)
