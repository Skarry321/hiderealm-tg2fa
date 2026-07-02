import logging
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import storage

logger = logging.getLogger(__name__)

BOT_TOKEN = "8514951662:AAF8_3HjSp1d_Jm_suT2PZTRrNe3mbXZTic"


def reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔗 Привязать"), KeyboardButton("🔓 Отвязать")],
        [KeyboardButton("📊 Статус"), KeyboardButton("🛡 2FA")],
        [KeyboardButton("🔑 Восстановить"), KeyboardButton("👢 Кикнуть")],
        [KeyboardButton("🚫 Заблокировать")],
    ], resize_keyboard=True)


def inline_back():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (
        "📃 Список команд бота:\n"
        "🔸 /link — Привязать аккаунт\n"
        "🔸 /unlink — Отвязать аккаунт\n"
        "🔸 /status — Информация об аккаунте\n"
        "🔸 /tfa — Включить двухэтапную авторизацию\n"
        "🔸 /restore — Получить новый пароль\n"
        "🔸 /kick — Кикнуть аккаунт от сервера\n"
        "🔸 /ban — Заблокировать аккаунт\n\n"
        f"📃 Ваш UserID: tg#{user_id}"
    )
    await update.message.reply_text(text, reply_markup=reply_keyboard())


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    tg_id = update.effective_user.id

    if text == "🔗 Привязать":
        uuid, _ = storage.get_player_by_telegram(tg_id)
        if uuid:
            await update.message.reply_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔗  **Привязка аккаунта**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ Вы уже привязали аккаунт!\n\n"
                "Используйте кнопку 🔓 Отвязать.",
                reply_markup=reply_keyboard(), parse_mode="Markdown"
            )
            return
        code = ''.join(random.choices(string.digits, k=6))
        storage.create_link_code_pending(tg_id, code)
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔗  **Привязка аккаунта**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔑 Ваш код: `{code}`\n\n"
            "📝 **Как привязать:**\n"
            "1. Зайди на сервер\n"
            "2. В чате напиши `/link`\n"
            "3. Увидишь предупреждение\n"
            "4. Напиши `/link {код}` ещё раз\n\n"
            "⏰ Код действителен **5 минут**",
            reply_markup=reply_keyboard(), parse_mode="Markdown"
        )

    elif text == "🔓 Отвязать":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔓  **Отвязка аккаунта**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ У вас нет привязанных аккаунтов.",
                reply_markup=reply_keyboard(), parse_mode="Markdown"
            )
            return
        storage.unlink_telegram(tg_id)
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔓  **Отвязка аккаунта**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Аккаунт `{info['username']}` отвязан!",
            reply_markup=reply_keyboard(), parse_mode="Markdown"
        )

    elif text == "📊 Статус":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text(
                "❌ У вас нет привязанных аккаунтов.",
                reply_markup=reply_keyboard()
            )
            return
        online = "🟢 В сети" if info.get("online") else "🔴 Не в сети"
        banned = "✅ Да" if info.get("banned") else "❌ Нет"
        tfa = "✅ Включена" if info.get("tfa_enabled") else "❌ Выключена"
        keyboard = []
        if info.get("banned"):
            keyboard.append([InlineKeyboardButton("✅ Разблокировать", callback_data="do_unban")])
        if info.get("online"):
            keyboard.append([InlineKeyboardButton("👢 Кикнуть", callback_data="do_kick")])
        else:
            keyboard.append([InlineKeyboardButton("🔑 Восстановить пароль", callback_data="do_restore")])
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📊  **Информация об аккаунте**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎮 Ник: `{info['username']}`\n"
            f"📡 Статус: {online}\n"
            f"🚫 Блокировка: {banned}\n"
            f"🛡 2FA: {tfa}\n"
            f"🌐 IP: `{info.get('last_ip', '—')}`\n"
            f"📍 {info.get('last_city', '—')}, {info.get('last_country', '—')}",
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else reply_keyboard(),
            parse_mode="Markdown"
        )

    elif text == "🛡 2FA":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text("❌ У вас нет привязанных аккаунтов.", reply_markup=reply_keyboard())
            return
        new = not info.get("tfa_enabled", False)
        storage.set_tfa(uuid, new)
        state = "включена ✅" if new else "выключена ❌"
        desc = "🔒 Теперь при входе нужно подтверждать через Telegram" if new else "🔓 Теперь вход без подтверждения"
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🛡  **Двухэтапная авторизация**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"2FA **{state}**\n\n{desc}",
            reply_markup=reply_keyboard(), parse_mode="Markdown"
        )

    elif text == "🔑 Восстановить":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text("❌ У вас нет привязанных аккаунтов.", reply_markup=reply_keyboard())
            return
        chars = string.ascii_letters + string.digits
        new_password = ''.join(random.choices(chars, k=13))
        storage.create_action("restore", uuid, {"password": new_password})
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔑  **Восстановление пароля**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔐 Новый пароль: `{new_password}`\n\n"
            "⚠️ **Обязательно смените пароль** после захода!\n"
            "Команда: `/cp <новый_пароль>`",
            reply_markup=reply_keyboard(), parse_mode="Markdown"
        )

    elif text == "👢 Кикнуть":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text("❌ У вас нет привязанных аккаунтов.", reply_markup=reply_keyboard())
            return
        storage.create_action("kick", uuid)
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👢  **Кик с сервера**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Аккаунт был кикнут!",
            reply_markup=reply_keyboard(), parse_mode="Markdown"
        )

    elif text == "🚫 Заблокировать":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await update.message.reply_text("❌ У вас нет привязанных аккаунтов.", reply_markup=reply_keyboard())
            return
        storage.set_banned(uuid, True)
        storage.create_action("ban", uuid)
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🚫  **Блокировка аккаунта**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Аккаунт был заблокирован!",
            reply_markup=reply_keyboard(), parse_mode="Markdown"
        )


async def handle_login_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":", 1)
    action = data[0]
    login_id = data[1] if len(data) > 1 else ""

    tg_id = query.from_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await query.edit_message_text("❌ Ошибка.")
        return

    login_req = storage.get_login_request(login_id)
    if not login_req:
        await query.edit_message_text("❌ Запрос устарел.")
        return

    ip = login_req['ip']
    city = login_req.get('city', '—')
    country = login_req.get('country', '—')

    if action == "confirm":
        storage.update_login_status(login_id, "approved")
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅  **Вход подтверждён**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🌐 IP: `{ip}`\n"
            f"📍 {city}, {country}\n\n"
            "⚠️ Если это были не вы — срочно заблокируйте аккаунт!",
            parse_mode="Markdown"
        )
    elif action == "kick":
        storage.update_login_status(login_id, "kicked")
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👢  **Кик с сервера**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Аккаунт был кикнут!",
            parse_mode="Markdown"
        )
    elif action == "ban":
        storage.set_banned(uuid, True)
        storage.update_login_status(login_id, "banned")
        storage.create_action("ban", uuid)
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🚫  **Блокировка аккаунта**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Аккаунт был заблокирован!",
            parse_mode="Markdown"
        )


async def handle_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tg_id = query.from_user.id
    data = query.data

    if data == "do_unban":
        uuid, _ = storage.get_player_by_telegram(tg_id)
        if uuid:
            storage.set_banned(uuid, False)
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅  **Разблокировка**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Аккаунт был разблокирован!",
            parse_mode="Markdown"
        )

    elif data == "do_kick":
        uuid, _ = storage.get_player_by_telegram(tg_id)
        if uuid:
            storage.create_action("kick", uuid)
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👢  **Кик с сервера**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Аккаунт был кикнут!",
            parse_mode="Markdown"
        )

    elif data == "do_restore":
        uuid, _ = storage.get_player_by_telegram(tg_id)
        if uuid:
            chars = string.ascii_letters + string.digits
            new_password = ''.join(random.choices(chars, k=13))
            storage.create_action("restore", uuid, {"password": new_password})
            await query.edit_message_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔑  **Восстановление пароля**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🔐 Новый пароль: `{new_password}`\n\n"
                "⚠️ **Обязательно смените пароль** после захода!\n"
                "Команда: `/cp <новый_пароль>`",
                parse_mode="Markdown"
            )


async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, _ = storage.get_player_by_telegram(tg_id)
    if uuid:
        await update.message.reply_text("❌ Вы уже привязали аккаунт!")
        return

    if not context.args:
        code = ''.join(random.choices(string.digits, k=6))
        storage.create_link_code_pending(tg_id, code)
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔗  **Привязка аккаунта**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔑 Ваш код: `{code}`\n\n"
            "📝 Зайди на сервер и напиши `/link {код}` в чат.",
            parse_mode="Markdown"
        )
        return

    code = context.args[0]
    info = storage.check_link_code(code)
    if not info:
        # Try pending link
        pending = storage.get_pending_link(code)
        if pending:
            storage.link_player(str(update.effective_user.id), update.effective_user.username or "player", pending["tg_id"])
            storage.complete_pending_link(code)
            await update.message.reply_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "✅  **Привязка успешна!**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🛡 Двухэтапная авторизация: ❌ Выключена\n\n"
                "Включите 2FA для защиты аккаунта!",
                reply_markup=reply_keyboard(), parse_mode="Markdown"
            )
            return
        await update.message.reply_text("❌ Неверный или просроченный код!")
        return
    if info["confirmed"]:
        await update.message.reply_text("❌ Этот код уже использован!")
        return

    result = storage.confirm_link_code(code, tg_id)
    if result:
        storage.link_player(result["uuid"], result["username"], tg_id)
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅  **Привязка успешна!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎮 Аккаунт: `{result['username']}`\n"
            "🛡 Двухэтапная авторизация: ❌ Выключена",
            reply_markup=reply_keyboard(), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Ошибка при привязке.")


async def cmd_unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("❌ У вас нет привязанных аккаунтов.")
        return
    storage.unlink_telegram(tg_id)
    await update.message.reply_text("✅ Аккаунт успешно отвязан!")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("❌ У вас нет привязанных аккаунтов.")
        return
    online = "🟢 В сети" if info.get("online") else "🔴 Не в сети"
    await update.message.reply_text(
        f"📊 **{info['username']}**\n📡 {online} | 🚫 {'Заблокирован' if info.get('banned') else 'Нет'} | 🛡 {'2FA' if info.get('tfa_enabled') else '—'}",
        parse_mode="Markdown"
    )


async def cmd_tfa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("❌ У вас нет привязанных аккаунтов.")
        return
    new = not info.get("tfa_enabled", False)
    storage.set_tfa(uuid, new)
    await update.message.reply_text(f"🛡 2FA {'включена ✅' if new else 'выключена ❌'}")


async def cmd_restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("❌ У вас нет привязанных аккаунтов.")
        return
    chars = string.ascii_letters + string.digits
    new_password = ''.join(random.choices(chars, k=13))
    storage.create_action("restore", uuid, {"password": new_password})
    await update.message.reply_text(f"🔑 Новый пароль: `{new_password}`\n\n⚠️ Смените после захода: `/cp <пароль>`", parse_mode="Markdown")


async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("❌ У вас нет привязанных аккаунтов.")
        return
    storage.create_action("kick", uuid)
    await update.message.reply_text("👢 Аккаунт был кикнут!")


async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("❌ У вас нет привязанных аккаунтов.")
        return
    storage.set_banned(uuid, True)
    storage.create_action("ban", uuid)
    await update.message.reply_text("🚫 Аккаунт был заблокирован!")


def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CallbackQueryHandler(handle_login_button, pattern="^(confirm|kick|ban):"))
    app.add_handler(CallbackQueryHandler(handle_inline_button, pattern="^(do_unban|do_kick|do_restore)$"))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link))
    app.add_handler(CommandHandler("unlink", cmd_unlink))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("tfa", cmd_tfa))
    app.add_handler(CommandHandler("restore", cmd_restore))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("ban", cmd_ban))

    from telegram.ext import MessageHandler, filters
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Starting bot polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
