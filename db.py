import sqlite3
from typing import Dict, Tuple


class Database:

    def __init__(self):
        self._db = sqlite3.connect('Chateau.sqlite')
        self._cursor = self._db.cursor()

    def commit(self):
        self._db.commit()

    def close(self):
        self._db.commit()

    def creates_tables(self):
        self._cursor.execute("""CREATE TABLE IF NOT EXISTS guilds(
                id INT,
                name VARCHAR(40),
                owner_id INT,
                owner_name VARCHAR(40)
            )""")
        self._cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                gid INT,
                uid INT,
                roles TEXT,
                exp INT DEFAULT 0,
                money BIGINT DEFAULT 0,
                lvl INT DEFAULT 0,
                messages INT DEFAULT 0,
                voice_min INT DEFAULT 0,
                warnings INT DEFAULT 0,
                FOREIGN KEY(gid) REFERENCES guilds(id)
            )""")
        self._cursor.execute("""CREATE TABLE IF NOT EXISTS shops(
                gid INT,
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                name VARCHAR(40),
                description TEXT,
                FOREIGN KEY(gid) REFERENCES guilds(id)
            )""")
        self._cursor.execute("""CREATE TABLE IF NOT EXISTS products(
                gid INT,
                sid INT,
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                price INT,
                name VARCHAR(40),
                FOREIGN KEY(gid) REFERENCES guilds(id),
                FOREIGN KEY(sid) REFERENCES shops(id)
            )""")

    def select_one(self, table: str, fields: Tuple, field_for_selection: Dict, addition: str = ''):
        columns = ', '.join(fields)
        condition = ' AND '.join(str(field) + ' = ?' for field in field_for_selection.keys())
        values = tuple(field_for_selection.values())
        _sql = f'SELECT {columns} FROM {table} ' \
               f'WHERE {condition} ' \
               f'{addition}'.rstrip()
        self._cursor.execute(_sql, values)
        return self._cursor.fetchone()

    def select_many(self, table: str, fields: Tuple, field_for_selection: Dict, addition: str = ''):
        columns = ', '.join(fields)
        condition = ' AND '.join(str(field) + ' = ?' for field in field_for_selection.keys())
        values = tuple(field_for_selection.values())
        _sql = f'SELECT {columns} FROM {table} ' \
               f'WHERE {condition} ' \
               f'{addition}'.rstrip()
        self._cursor.execute(_sql, values)
        return self._cursor.fetchall()

    def insert_one(self, table: str, column_and_value: Dict):
        if len(column_and_value) == 1:
            column = ''.join(column_and_value.keys())
            value = tuple(column_and_value.get(column))
            _sql = f'INSERT INTO {table}({column}) ' \
                   f'VALUES (?)'
            self._cursor.execute(_sql, value)

    # @decorator
    def insert_many(self, table: str, columns_and_values: Dict):
        columns = ', '.join(columns_and_values.keys())
        values = tuple(columns_and_values.values())
        placeholders = ', '.join('?' * len(columns_and_values.keys()))
        _sql = f'INSERT INTO {table}({columns}) ' \
               f'VALUES ({placeholders})'
        self._cursor.execute(_sql, values)

    def update(self, table: str, columns_and_values: Dict, field_for_selection: Dict):
        data = [f'{column} = {value}' for column, value in columns_and_values.items()]
        expressions = ', '.join(data)
        condition = ' AND '.join(str(field) + ' = ?' for field in field_for_selection.keys())
        values = tuple(field_for_selection.values())
        _sql = f'UPDATE {table} ' \
               f'SET {expressions} ' \
               f'WHERE {condition}'
        self._cursor.execute(_sql, values)

    def delete(self, table: str, field_for_selection: Dict):
        condition = ' AND '.join(str(field) + ' = ?' for field in field_for_selection.keys())
        values = tuple(field_for_selection.values())
        _sql = f'DELETE FROM {table} ' \
               f'WHERE {condition}'
        self._cursor.execute(_sql, values)
