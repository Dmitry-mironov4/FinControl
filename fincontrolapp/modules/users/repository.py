import sqlite3
from .model import User

class UserRepository:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def create(self, user: User) -> int:
        cursor = self.con.execute('''
            INSERT INTO users (telegram_id, email, phone, username, password_hash)
            VALUES (?, ?, ?, ?, ?)
        ''', (user.telegram_id, user.email, user.phone, user.username, user.password_hash))
        self.con.commit()
        return cursor.lastrowid
    
    def _row_to_user(self, row) -> User:
        return User(id=row['id'], 
                    telegram_id=row['telegram_id'], 
                    email=row['email'], 
                    phone=row['phone'], 
                    username=row['username'], 
                    password_hash=row['password_hash'], 
                    created_at=row['created_at'])
    
    def get_by_id(self, user_id: int) -> User | None:
        cursor = self.con.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            return self.row_to_user(row)
        return None

    def get_by_contact(self, email: str | None = None, phone: str | None = None) -> User | None:
        if not email and not phone:
            return None
        query = 'SELECT * FROM users WHERE'
        params = []
        if email:
            query += ' email = ?'
            params.append(email)
        if phone:
            if email:
                query += ' OR'
            query += ' phone = ?'
            params.append(phone)
        cursor = self.con.execute(query, tuple(params))
        row = cursor.fetchone()
        if row:
            return self.row_to_user(row)
        return None

