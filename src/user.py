import json
from pathlib import Path
from typing import Any, Dict, Optional

from .config import BASE_DIR


class UsersJSONUtil:
    def __init__(self):
        self.users_json: Path = BASE_DIR / "users.json"

        if not self.users_json.exists():
            self.users_json.write_text("{}")

    def load_users(self) -> Dict[str, Dict[str, Any]]:
        try:
            data = json.loads(self.users_json.read_text())
        except json.JSONDecodeError:
            data = {}

        if not isinstance(data, dict):
            data = {}

        return data

    def save_users(self, users: Dict[str, Dict[str, Any]]):
        self.users_json.write_text(json.dumps(users, indent=4, ensure_ascii=False))

    def set_user(
        self,
        tg_id: str,
        firstname: Optional[str],
        username: Optional[str],
    ):
        users = self.load_users()

        if tg_id not in users:
            users[tg_id] = {
                "firstname": firstname or "UnknownFirstname",
                "username": username or "UnknownUsername",
            }

        self.save_users(users)


users_json_util = UsersJSONUtil()
