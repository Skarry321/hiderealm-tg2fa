import logging
import threading
import time
import requests as http_requests
from flask import Flask, request, jsonify
import storage

logger = logging.getLogger(__name__)
app = Flask(__name__)

BOT_TOKEN = "8514951662:AAF8_3HjSp1d_Jm_suT2PZTRrNe3mbXZTic"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_telegram(tg_id, text, buttons=None):
    payload = {"chat_id": tg_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        payload["reply_markup"] = {
            "inline_keyboard": [
                [{"text": b["text"], "callback_data": b["callback_data"]}]
                for b in buttons
            ]
        }
    try:
        http_requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=5)
    except Exception as e:
        logger.error(f"Telegram send error: {e}")


@app.route("/api/link/create", methods=["POST"])
def link_create():
    data = request.get_json(force=True)
    uuid = data.get("uuid", "")
    username = data.get("username", "")
    if not uuid or not username:
        return jsonify({"error": "missing fields"}), 400
    code = storage.create_link_code(uuid, username)
    return jsonify({"code": code})


@app.route("/api/link/verify", methods=["POST"])
def link_verify():
    data = request.get_json(force=True)
    uuid = data.get("uuid", "")
    username = data.get("username", "")
    code = data.get("code", "")
    if not uuid or not code:
        return jsonify({"error": "missing fields"}), 400

    pending = storage.get_pending_link(code)
    if not pending:
        return jsonify({"success": False, "error": "invalid_or_expired_code"})

    tg_id = pending["tg_id"]
    storage.link_player(uuid, username, tg_id)
    storage.complete_pending_link(code)
    send_telegram(tg_id, "✅ Вы успешно привязали свой аккаунт")
    return jsonify({"success": True, "telegram_id": tg_id})


@app.route("/api/link/check", methods=["GET"])
def link_check():
    uuid = request.args.get("uuid", "")
    if not uuid:
        return jsonify({"error": "missing uuid"}), 400
    info = storage.get_link_confirmed(uuid)
    if info:
        return jsonify({"confirmed": True, "telegram_id": info.get("confirmed_by")})
    return jsonify({"confirmed": False})


@app.route("/api/player/join", methods=["POST"])
def player_join():
    data = request.get_json(force=True)
    uuid = data.get("uuid", "")
    username = data.get("username", "")
    ip = data.get("ip", "")
    city = data.get("city", "")
    country = data.get("country", "")

    player = storage.get_player_by_uuid(uuid)
    if not player:
        return jsonify({"action": "none", "reason": "not_linked"})

    storage.update_last_login(uuid, ip, city, country)

    if player.get("banned"):
        return jsonify({"action": "banned", "reason": "account_banned"})

    login_id = storage.create_login_request(uuid, username, ip, city, country)
    tg_id = player["telegram_id"]

    city_country = f"{city}, {country}" if city else country

    needs_approval = player.get("tfa_enabled", False)
    if needs_approval:
        text = (
            f"\U000026a0 Подтвердите вход в аккаунт\n"
            f"IP: {ip}\n"
            f"{city_country}"
        )
        buttons = [
            {"text": "\u2705 Подтвердить", "callback_data": f"confirm:{login_id}"},
            {"text": "\U0001f4a2 Кикнуть", "callback_data": f"kick:{login_id}"},
            {"text": "\U0001f6ab Заблокировать", "callback_data": f"ban:{login_id}"},
        ]
        send_telegram(tg_id, text, buttons)
        return jsonify({"action": "pending", "login_id": login_id})
    else:
        text = (
            "Вы вошли в игру\n"
            f"IP: {ip}\n"
            f"{city_country}\n\n"
            "Если это были не вы, то срочно заблокируйте аккаунт!"
        )
        send_telegram(tg_id, text)
        return jsonify({"action": "allow", "login_id": login_id})


@app.route("/api/player/login-status", methods=["GET"])
def login_status():
    login_id = request.args.get("login_id", "")
    if not login_id:
        return jsonify({"error": "missing login_id"}), 400
    req = storage.get_login_request(login_id)
    if not req:
        return jsonify({"status": "expired"})
    if time.time() - req["created_at"] > 60:
        storage.update_login_status(login_id, "timeout")
        return jsonify({"status": "timeout"})
    return jsonify({"status": req["status"]})


@app.route("/api/player/leave", methods=["POST"])
def player_leave():
    data = request.get_json(force=True)
    uuid = data.get("uuid", "")
    storage.set_online(uuid, False)

    player = storage.get_player_by_uuid(uuid)
    if player:
        send_telegram(player["telegram_id"], "\u2796 Вы вышли из игры")

    return jsonify({"ok": True})


@app.route("/api/player/status", methods=["GET"])
def player_status():
    uuid = request.args.get("uuid", "")
    if not uuid:
        return jsonify({"error": "missing uuid"}), 400
    player = storage.get_player_by_uuid(uuid)
    if not player:
        return jsonify({"exists": False})
    return jsonify({
        "exists": True,
        "username": player["username"],
        "banned": player["banned"],
        "tfa_enabled": player["tfa_enabled"],
        "online": player.get("online", False),
        "last_ip": player.get("last_ip", ""),
    })


@app.route("/api/actions/pending", methods=["GET"])
def actions_pending():
    server_id = request.args.get("server_id", "main")
    actions = storage.get_pending_actions()
    return jsonify({"actions": actions})


@app.route("/api/actions/complete", methods=["POST"])
def actions_complete():
    data = request.get_json(force=True)
    action_id = data.get("action_id", "")
    storage.complete_action(action_id)
    return jsonify({"ok": True})


def run_api(host="0.0.0.0", port=5000):
    logger.info(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)


def start_api_thread(host="0.0.0.0", port=5000):
    t = threading.Thread(target=run_api, args=(host, port), daemon=True)
    t.start()
    return t
