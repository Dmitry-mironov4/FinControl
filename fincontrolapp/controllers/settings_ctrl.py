from database import get_connection
from db_queries import change_password as _change_password


class SettingsController:
    def __init__(self, user_id: int):
        self._user_id = user_id

    def get_user(self):
        with get_connection() as con:
            return con.execute(
                'SELECT username, email, phone FROM users WHERE id=?', (self._user_id,)
            ).fetchone()

    def update_username(self, username: str | None):
        with get_connection() as con:
            con.execute(
                'UPDATE users SET username=? WHERE id=?', (username, self._user_id)
            )

    def reset_data(self):
        with get_connection() as con:
            con.execute('DELETE FROM transactions WHERE user_id=?', (self._user_id,))
            con.execute('DELETE FROM goals WHERE user_id=?', (self._user_id,))
            con.execute('DELETE FROM subscriptions WHERE user_id=?', (self._user_id,))

    def change_password(self, old_pwd: str, new_pwd: str) -> bool:
        return _change_password(self._user_id, old_pwd, new_pwd)

    def delete_account(self):
        with get_connection() as con:
            con.execute('DELETE FROM transactions WHERE user_id=?', (self._user_id,))
            con.execute('DELETE FROM goals WHERE user_id=?', (self._user_id,))
            con.execute('DELETE FROM subscriptions WHERE user_id=?', (self._user_id,))
            con.execute('DELETE FROM users WHERE id=?', (self._user_id,))
