import hashlib
import os
from .repository import UserRepository
from .model import User

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + key.hex()

def verify_password(stored: str, provided: str) -> bool:
    try:
        salt_hex, key_hex = stored.split(':')
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac('sha256', provided.encode('utf-8'), salt, 100000)
        return key.hex() == key_hex
    except Exception:
        return False

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register_user(self, user: User, password: str) -> int:
        existing_user = self.repository.get_by_contact(email=user.email, phone=user.phone)
        if existing_user:
            raise ValueError("Пользователь с таким email или телефоном уже существует")
        user.password_hash = hash_password(password)
        return self.repository.create(user)
    
    def login_user(self, email=None, phone=None, password=None):
        user = self.repository.get_by_contact(email=email, phone=phone)
        if not user:
            raise ValueError("Пользователь не найден")
        if not verify_password(user.password_hash, password):
            raise ValueError("Неверный пароль")
        return user