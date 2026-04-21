import sqlite3
from .model import Category

class CategoryRepository:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def get_all(self, type_=None) -> list[Category]:
        query = 'SELECT * FROM categories'
        params = []
        if type_:
            query += ' WHERE type = ?'
            params.append(type_)
        cursor = self.con.execute(query, tuple(params))
        return [Category(id=row['id'], name=row['name'], type=row['type']) for row in cursor.fetchall()]