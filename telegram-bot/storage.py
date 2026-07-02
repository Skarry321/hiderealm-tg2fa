import json
import os
import threading
import time
import random
import string

DATA_FILE = os.environ.get("BOT_DATA_FILE", "data.json")
_lock = threading.Lock()


def _load():
    if not os.path.exists(DATA_FILE):
        return {
            "players": {},
            "link_codes": {},
            "login_requests": {},
            "pending_actions": {},
            "last_action_id": 0,
            "last_login_id": 0,
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_player_by_telegram(tg_id):
    with _lock:
        data = _load()
        for uuid, info in data["players"].items():
            if info.get("telegram_id") == tg_id:
                return uuid, info
        return None, None


def get_player_by_uuid(uuid):
    with _lock:
        data = _load()
        return data["players"].get(uuid)


def link_player(uuid, username, tg_id):
    with _lock:
        data = _load()
        data["players"][uuid] = {
            "username": username,
            "telegram_id": tg_id,
            "banned": False,
            "tfa_enabled": False,
            "last_ip": "",
            "last_city": "",
            "last_country": "",
            "online": False,
            "last_login": int(time.time()),
            "linked_at": int(time.time()),
        }
        _save(data)


def unlink_telegram(tg_id):
    with _lock:
        data = _load()
        for uuid, info in list(data["players"].items()):
            if info.get("telegram_id") == tg_id:
                del data["players"][uuid]
                _save(data)
                return uuid, info
        return None, None


def set_banned(uuid, banned):
    with _lock:
        data = _load()
        if uuid in data["players"]:
            data["players"][uuid]["banned"] = banned
            _save(data)


def set_tfa(uuid, enabled):
    with _lock:
        data = _load()
        if uuid in data["players"]:
            data["players"][uuid]["tfa_enabled"] = enabled
            _save(data)


def set_online(uuid, online):
    with _lock:
        data = _load()
        if uuid in data["players"]:
            data["players"][uuid]["online"] = online
            _save(data)


def update_last_login(uuid, ip, city, country):
    with _lock:
        data = _load()
        if uuid in data["players"]:
            data["players"][uuid]["last_ip"] = ip
            data["players"][uuid]["last_city"] = city
            data["players"][uuid]["last_country"] = country
            data["players"][uuid]["last_login"] = int(time.time())
            data["players"][uuid]["online"] = True
            _save(data)


def create_link_code(uuid, username):
    code = ''.join(random.choices(string.digits, k=6))
    with _lock:
        data = _load()
        while code in data["link_codes"]:
            code = ''.join(random.choices(string.digits, k=6))
        data["link_codes"][code] = {
            "uuid": uuid,
            "username": username,
            "created_at": int(time.time()),
            "confirmed": False,
            "confirmed_by": None,
        }
        _save(data)
    return code


def confirm_link_code(code, tg_id):
    with _lock:
        data = _load()
        if code not in data["link_codes"]:
            return None
        info = data["link_codes"][code]
        if time.time() - info["created_at"] > 300:
            return None
        info["confirmed"] = True
        info["confirmed_by"] = tg_id
        _save(data)
        return info


def check_link_code(code):
    with _lock:
        data = _load()
        info = data["link_codes"].get(code)
        if info and time.time() - info["created_at"] > 300:
            return None
        return info


def get_link_confirmed(uuid):
    with _lock:
        data = _load()
        for code, info in data["link_codes"].items():
            if info["uuid"] == uuid and info["confirmed"]:
                return info
        return None


def create_login_request(uuid, username, ip, city, country):
    with _lock:
        data = _load()
        data["last_login_id"] += 1
        login_id = f"login_{data['last_login_id']}"
        data["login_requests"][login_id] = {
            "uuid": uuid,
            "username": username,
            "ip": ip,
            "city": city,
            "country": country,
            "status": "pending",
            "created_at": int(time.time()),
        }
        _save(data)
        return login_id


def update_login_status(login_id, status):
    with _lock:
        data = _load()
        if login_id in data["login_requests"]:
            data["login_requests"][login_id]["status"] = status
            _save(data)


def get_login_request(login_id):
    with _lock:
        data = _load()
        return data["login_requests"].get(login_id)


def create_action(action_type, uuid, params=None):
    with _lock:
        data = _load()
        data["last_action_id"] += 1
        action_id = f"action_{data['last_action_id']}"
        data["pending_actions"][action_id] = {
            "id": action_id,
            "type": action_type,
            "uuid": uuid,
            "params": params or {},
            "status": "pending",
            "created_at": int(time.time()),
        }
        _save(data)
        return action_id


def get_pending_actions():
    with _lock:
        data = _load()
        return [v for v in data["pending_actions"].values() if v["status"] == "pending"]


def complete_action(action_id):
    with _lock:
        data = _load()
        if action_id in data["pending_actions"]:
            data["pending_actions"][action_id]["status"] = "completed"
            _save(data)


def cleanup_old():
    with _lock:
        data = _load()
        now = int(time.time())
        data["link_codes"] = {k: v for k, v in data["link_codes"].items() if now - v["created_at"] < 300}
        data["login_requests"] = {k: v for k, v in data["login_requests"].items() if now - v["created_at"] < 120}
        data["pending_actions"] = {k: v for k, v in data["pending_actions"].items() if v["status"] == "pending" and now - v["created_at"] < 3600}
        _save(data)
