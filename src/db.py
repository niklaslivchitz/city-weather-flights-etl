"""This file builds some reusable functions for interacting with the MySQL database"""


import os
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, URL
from sqlalchemy.dialects.mysql import insert

load_dotenv(find_dotenv(usecwd=True, raise_error_if_not_found=True), override=True)

#Here we define a function to create a SQLAlchemy engine for connecting to the MySQL database. The engine quickly lets us connect to the database and execute SQL queries.

def get_engine(database="cities"):
    url = URL.create(
        "mysql+pymysql",
        username="root",
        password=os.getenv("MYSQL_PASSWORD"),
        host="127.0.0.1",
        port=3306,
        database=database,  # None → server-level engine for CREATE/DROP DATABASE
    )
    return create_engine(url)

#insert_ignore lets us populate the database with reruns without having things crash from duplicate primary keys.

def insert_ignore(table, conn, keys, data_iter):
    rows = [dict(zip(keys, row)) for row in data_iter]
    stmt = insert(table.table).values(rows).prefix_with("IGNORE")
    return conn.execute(stmt).rowcount