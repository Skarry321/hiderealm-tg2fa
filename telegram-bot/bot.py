import logging
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import storage

logger = logging.getLogger(__name__)

BOT_TOKEN = "8514951662:AAF8_3HjSp1d_Jm_suT2PZTRrNe3mbXZTic"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"Ваш UserID: tg#{user_id}\n\n"
        "Чтобы привязать аккаунт,\n"
        "Введите в игровой чат команду:\n"
        "/link\n\n"
        "Список команд бота:\n"
        "/link <код> - Привязать аккаунт\n"
        "/unlink - Отвязать аккаунт\n"
        "/status - Информация об аккаунте\n"
        "/tfa - Двухэтапная авторизация\n"
        "/restore - Получить новый пароль\n"
        "/kick - Кикнуть аккаунт\n"
        "/ban - Заблокировать аккаунт"
    )


async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, _ = storage.get_player_by_telegram(tg_id)
    if uuid:
        await update.message.reply_text("Вы уже привязали аккаунт!")
        return

    if not context.args:
        await update.message.reply_text("Использование: /link <код>\nКод вы получаете в игре после команды /link")
        return

    code = context.args[0]
    info = storage.check_link_code(code)
    if not info:
        await update.message.reply_text("Неверный или просроченный код! Попробуйте снова в игре.")
        return
    if info["confirmed"]:
        await update.message.reply_text("Этот код уже использован!")
        return

    result = storage.confirm_link_code(code, tg_id)
    if result:
        storage.link_player(result["uuid"], result["username"], tg_id)
        await update.message.reply_text("Вы успешно привязали свой аккаунт")
    else:
        await update.message.reply_text("Ошибка при привязке. Попробуйте снова.")


async def unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    result = storage.unlink_telegram(tg_id)
    if result:
        await update.message.reply_text("Аккаунт успешно отвязан!")
    else:
        await update.message.reply_text("У вас нет привязанных аккаунтов.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("У вас нет привязанных аккаунтов.")
        return

    st = "В сети" if info.get("online") else "Не в сети"
    text = (
        "Информация об аккаунте:\n\n"
        f"Ник: {info['username']}\n"
        f"Статус: {st}\n"
        f"Блокировка: {'Да' if info.get('banned') else 'Нет'}\n"
        f"2FA: {'Включена' if info.get('tfa_enabled') else 'Выключена'}\n"
        f"Последний IP: {info.get('last_ip', '-')}\n"
        f"Последний вход: {info.get('last_city', '-')}, {info.get('last_country', '-')}"
    )
    keyboard = []
    if info.get("banned"):
        keyboard.append([InlineKeyboardButton("Разблокировать", callback_data="unban")])
    if info.get("online"):
        keyboard.append([InlineKeyboardButton("Кикнуть", callback_data="kick")])
    else:
        keyboard.append([InlineKeyboardButton("Восстановить пароль", callback_data="restore")])
    rm = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text(text, reply_markup=rm)


async def tfa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("У вас нет привязанных аккаунтов.")
        return
    new = not info.get("tfa_enabled", False)
    storage.set_tfa(uuid, new)
    await update.message.reply_text(f"Двухэтапная авторизация {'включена' if new else 'выключена'}!")


async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("У вас нет привязанных аккаунтов.")
        return
    chars = string.ascii_letters + string.digits
    new_password = ''.join(random.choices(chars, k=13))
    storage.create_action("restore", uuid, {"password": new_password})
    await update.message.reply_text(
        f"Ваш новый пароль: {new_password}\n\n"
        "Обязательно смените пароль, после захода на сервер!\n"
        "Команда для смены пароля: /cp"
    )


async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("У вас нет привязанных аккаунтов.")
        return
    storage.create_action("kick", uuid)
    await update.message.reply_text("Аккаунт был кикнут!")


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("У вас нет привязанных аккаунтов.")
        return
    storage.set_banned(uuid, True)
    storage.create_action("ban", uuid)
    await update.message.reply_text("Аккаунт был заблокирован!")


async def handle_login_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":", 1)
    action = data[0]
    login_id = data[1] if len(data) > 1 else ""

    tg_id = query.from_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await query.edit_message_text("У вас нет привязанных аккаунтов.")
        return

    login_req = storage.get_login_request(login_id)
    if not login_req:
        await query.edit_message_text("Запрос устарел.")
        return

    if action == "confirm":
        storage.update_login_status(login_id, "approved")
        await query.edit_message_text(
            "Вы вошли в игру\n"
            f"IP: {login_req['ip']}\n"
            f"{login_req.get('city', '-')}, {login_req.get('country', '-')}\n\n"
            "Если это были не вы, то срочно заблокируйте аккаунт!"
        )
    elif action == "kick":
        storage.update_login_status(login_id, "kicked")
        await query.edit_message_text("Аккаунт был кикнут!")
    elif action == "ban":
        storage.set_banned(uuid, True)
        storage.update_login_status(login_id, "banned")
        storage.create_action("ban", uuid)
        await query.edit_message_text("Аккаунт был заблокирован!")


async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tg_id = query.from_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await query.edit_message_text("У вас нет привязанных аккаунтов.")
        return
    if query.data == "unban":
        storage.set_banned(uuid, False)
        await query.edit_message_text("Аккаунт был разблокирован!")
    elif query.data == "kick":
        storage.create_action("kick", uuid)
        await query.edit_message_text("Аккаунт был кикнут!")
    elif query.data == "restore":
        chars = string.ascii_letters + string.digits
        new_password = ''.join(random.choices(chars, k=13))
        storage.create_action("restore", uuid, {"password": new_password})
        await query.edit_message_text(
            f"Ваш новый пароль: {new_password}\n\n"
            "Обязательно смените пароль, после захода на сервер!\n"
            "Команда для смены пароля: /cp"
        )


def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link))
    app.add_handler(CommandHandler("unlink", unlink))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("tfa", tfa))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CallbackQueryHandler(handle_login_button, pattern="^(confirm|kick|ban):"))
    app.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^(unban|kick|restore)$"))
    logger.info("Starting bot polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
