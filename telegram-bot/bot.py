import logging
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import storage

logger = logging.getLogger(__name__)

BOT_TOKEN = "8514951662:AAF8_3HjSp1d_Jm_suT2PZTRrNe3mbXZTic"

HELP_TEXT = (
    "Список команд бота:\n"
    "/link — Привязать аккаунт\n"
    "/unlink — Отвязать аккаунт\n"
    "/status — Информация об аккаунте\n"
    "/tfa — Включить двух-этапную авторизацию\n"
    "/restore — Получить новый пароль\n"
    "/kick — Кикнуть аккаунт от сервера\n"
    "/ban — Заблокировать аккаунт"
)


def get_keyboard(tg_id):
    uuid, info = storage.get_player_by_telegram(tg_id)
    linked = uuid is not None
    tfa_on = info.get("tfa_enabled", False) if info else False

    link_btn = "Отвязать" if linked else "Привязать"
    tfa_btn = "Отключить двух-этапную авторизацию" if tfa_on else "Включить двух-этапную авторизацию"

    return ReplyKeyboardMarkup([
        [KeyboardButton(link_btn), KeyboardButton("Статус")],
        [KeyboardButton(tfa_btn), KeyboardButton("Восстановить пароль")],
        [KeyboardButton("Кикнуть"), KeyboardButton("Заблокировать")],
        [KeyboardButton("Помощь")],
    ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (
        "Список команд бота:\n"
        "/link — Привязать аккаунт\n"
        "/unlink — Отвязать аккаунт\n"
        "/status — Информация об аккаунте\n"
        "/tfa — Включить двух-этапную авторизацию\n"
        "/restore — Получить новый пароль\n"
        "/kick — Кикнуть аккаунт от сервера\n"
        "/ban — Заблокировать аккаунт\n\n"
        f"Ваш UserID: tg#{user_id}"
    )
    await update.message.reply_text(text, reply_markup=get_keyboard(user_id))


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    tg_id = update.effective_user.id

    if text == "Помощь":
        await update.message.reply_text(
            HELP_TEXT + f"\n\nВаш UserID: tg#{tg_id}",
            reply_markup=get_keyboard(tg_id)
        )

    elif text == "Привязать":
        uuid, _ = storage.get_player_by_telegram(tg_id)
        if uuid:
            await update.message.reply_text(
                "Вы уже привязали аккаунт!",
                reply_markup=get_keyboard(tg_id)
            )
            return
        code = ''.join(random.choices(string.digits, k=6))
        storage.create_link_code_pending(tg_id, code)
        await update.message.reply_text(
            f"Ваш код: {code}\n\n"
            "Зайди на сервер и напиши /link {код} в чат.\n"
            "Код действителен 5 минут.",
            reply_markup=get_keyboard(tg_id)
        )

    elif text == "Отвязать":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text("У вас нет привязанных аккаунтов.", reply_markup=get_keyboard(tg_id))
            return
        storage.unlink_telegram(tg_id)
        await update.message.reply_text(f"Аккаунт {info['username']} отвязан!", reply_markup=get_keyboard(tg_id))

    elif text == "Статус":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text("У вас нет привязанных аккаунтов.", reply_markup=get_keyboard(tg_id))
            return
        online = "В сети" if info.get("online") else "Не в сети"
        banned = "Заблокирован" if info.get("banned") else "Нет"
        tfa = "Включена" if info.get("tfa_enabled") else "Выключена"
        await update.message.reply_text(
            f"Аккаунт: {info['username']}\n"
            f"Статус: {online}\n"
            f"Блокировка: {banned}\n"
            f"2FA: {tfa}\n"
            f"IP: {info.get('last_ip', '-')}\n"
            f"Местоположение: {info.get('last_city', '-')}, {info.get('last_country', '-')}",
            reply_markup=get_keyboard(tg_id)
        )

    elif text == "Включить двух-этапную авторизацию":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text("У вас нет привязанных аккаунтов.", reply_markup=get_keyboard(tg_id))
            return
        storage.set_tfa(uuid, True)
        await update.message.reply_text(
            "Двух-этапная авторизация включена!\n"
            "Теперь при входе нужно подтверждать через Telegram.",
            reply_markup=get_keyboard(tg_id)
        )

    elif text == "Отключить двух-этапную авторизацию":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text("У вас нет привязанных аккаунтов.", reply_markup=get_keyboard(tg_id))
            return
        storage.set_tfa(uuid, False)
        await update.message.reply_text(
            "Двух-этапная авторизация отключена!",
            reply_markup=get_keyboard(tg_id)
        )

    elif text == "Восстановить пароль":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text("У вас нет привязанных аккаунтов.", reply_markup=get_keyboard(tg_id))
            return
        chars = string.ascii_letters + string.digits
        new_password = ''.join(random.choices(chars, k=13))
        storage.create_action("restore", uuid, {"password": new_password})
        await update.message.reply_text(
            f"Новый пароль: {new_password}\n\n"
            "Обязательно смените пароль после захода!\n"
            "Команда: /cp <новый_пароль>",
            reply_markup=get_keyboard(tg_id)
        )

    elif text == "Кикнуть":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text("У вас нет привязанных аккаунтов.", reply_markup=get_keyboard(tg_id))
            return
        storage.create_action("kick", uuid)
        await update.message.reply_text("Аккаунт был кикнут!", reply_markup=get_keyboard(tg_id))

    elif text == "Заблокировать":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text("У вас нет привязанных аккаунтов.", reply_markup=get_keyboard(tg_id))
            return
        storage.set_banned(uuid, True)
        storage.create_action("ban", uuid)
        await update.message.reply_text("Аккаунт был заблокирован!", reply_markup=get_keyboard(tg_id))


async def handle_login_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":", 1)
    action = data[0]
    login_id = data[1] if len(data) > 1 else ""

    tg_id = query.from_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await query.edit_message_text("Ошибка.")
        return

    login_req = storage.get_login_request(login_id)
    if not login_req:
        await query.edit_message_text("Запрос устарел.")
        return

    ip = login_req['ip']
    city = login_req.get('city', '-')
    country = login_req.get('country', '-')

    if action == "confirm":
        storage.update_login_status(login_id, "approved")
        await query.edit_message_text(
            "Вход подтверждён!\n\n"
            f"IP: {ip}\n"
            f"{city}, {country}\n\n"
            "Если это были не вы — срочно заблокируйте аккаунт!"
        )
    elif action == "kick":
        storage.update_login_status(login_id, "kicked")
        await query.edit_message_text("Аккаунт был кикнут!")
    elif action == "ban":
        storage.set_banned(uuid, True)
        storage.update_login_status(login_id, "banned")
        storage.create_action("ban", uuid)
        await query.edit_message_text("Аккаунт был заблокирован!")


async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, _ = storage.get_player_by_telegram(tg_id)
    if uuid:
        await update.message.reply_text("Вы уже привязали аккаунт!")
        return

    if not context.args:
        code = ''.join(random.choices(string.digits, k=6))
        storage.create_link_code_pending(tg_id, code)
        await update.message.reply_text(
            f"Ваш код: {code}\n\n"
            "Зайди на сервер и напиши /link {код} в чат."
        )
        return

    code = context.args[0]
    info = storage.check_link_code(code)
    if not info:
        pending = storage.get_pending_link(code)
        if pending:
            storage.link_player(str(tg_id), update.effective_user.username or "player", pending["tg_id"])
            storage.complete_pending_link(code)
            await update.message.reply_text("Вы успешно привязали свой аккаунт", reply_markup=get_keyboard(tg_id))
            return
        await update.message.reply_text("Неверный или просроченный код!")
        return
    if info["confirmed"]:
        await update.message.reply_text("Этот код уже использован!")
        return

    result = storage.confirm_link_code(code, tg_id)
    if result:
        storage.link_player(result["uuid"], result["username"], tg_id)
        await update.message.reply_text("Вы успешно привязали свой аккаунт", reply_markup=get_keyboard(tg_id))
    else:
        await update.message.reply_text("Ошибка при привязке.")


async def cmd_unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("У вас нет привязанных аккаунтов.")
        return
    storage.unlink_telegram(tg_id)
    await update.message.reply_text("Аккаунт успешно отвязан!", reply_markup=get_keyboard(tg_id))


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("У вас нет привязанных аккаунтов.")
        return
    online = "В сети" if info.get("online") else "Не в сети"
    await update.message.reply_text(
        f"{info['username']} | {online} | 2FA: {'да' if info.get('tfa_enabled') else 'нет'}",
        reply_markup=get_keyboard(tg_id)
    )


async def cmd_tfa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("У вас нет привязанных аккаунтов.")
        return
    new = not info.get("tfa_enabled", False)
    storage.set_tfa(uuid, new)
    await update.message.reply_text(
        f"Двух-этапная авторизация {'включена' if new else 'отключена'}!",
        reply_markup=get_keyboard(tg_id)
    )


async def cmd_restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("У вас нет привязанных аккаунтов.")
        return
    chars = string.ascii_letters + string.digits
    new_password = ''.join(random.choices(chars, k=13))
    storage.create_action("restore", uuid, {"password": new_password})
    await update.message.reply_text(
        f"Новый пароль: {new_password}\n\nСмените после захода: /cp <пароль>",
        reply_markup=get_keyboard(tg_id)
    )


async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("У вас нет привязанных аккаунтов.")
        return
    storage.create_action("kick", uuid)
    await update.message.reply_text("Аккаунт был кикнут!", reply_markup=get_keyboard(tg_id))


async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("У вас нет привязанных аккаунтов.")
        return
    storage.set_banned(uuid, True)
    storage.create_action("ban", uuid)
    await update.message.reply_text("Аккаунт был заблокирован!", reply_markup=get_keyboard(tg_id))


def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CallbackQueryHandler(handle_login_button, pattern="^(confirm|kick|ban):"))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link))
    app.add_handler(CommandHandler("unlink", cmd_unlink))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("tfa", cmd_tfa))
    app.add_handler(CommandHandler("restore", cmd_restore))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("ban", cmd_ban))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Starting bot polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
