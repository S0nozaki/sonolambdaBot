import psycopg2
from dotenv import load_dotenv
import os
import re

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

pattern = "[:/@]"
DB_TYPE, DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME = re.split(
    pattern, DATABASE_URL.replace("://", "/"))


def open_connection():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME,
                            user=DB_USER, password=DB_PASS, port=DB_PORT)
    cur = conn.cursor()
    return conn, cur


def update_wallet(id, symbol, type):
    conn, cur = open_connection()
    cur.execute(
        "SELECT * FROM wallet WHERE user_id = %s AND symbol = %s", (id, symbol))
    if (cur.fetchone()):
        cur.execute(
            "DELETE FROM wallet WHERE user_id = %s AND symbol = %s", (id, symbol))
    else:
        cur.execute(
            "INSERT INTO wallet(user_id, symbol, type) VALUES (%s, %s, %s)", (id, symbol, type))
    conn.commit()
    close_connection(conn, cur)


def check_wallet(id):
    conn, cur = open_connection()
    cur.execute("SELECT symbol FROM wallet WHERE user_id = %s", [id])
    symbols = [s[0] for s in cur.fetchall()]
    conn.commit()
    close_connection(conn, cur)
    return symbols


def close_connection(conn, cur):
    cur.close()
    conn.close()
