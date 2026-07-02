import logging
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import storage

logger = logging.getLogger(__name__)

BOT_TOKEN = "8514951662:AAF8_3HjSp1d_Jm_suT2PZTRrNe3mbXZTic"


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Привязать аккаунт", callback_data="menu_link"),
         InlineKeyboardButton("🔓 Отвязать", callback_data="menu_unlink")],
        [InlineKeyboardButton("📊 Статус", callback_data="menu_status"),
         InlineKeyboardButton("🛡 2FA", callback_data="menu_tfa")],
        [InlineKeyboardButton("🔑 Восстановить пароль", callback_data="menu_restore")],
        [InlineKeyboardButton("👢 Кикнуть", callback_data="menu_kick"),
         InlineKeyboardButton("🚫 Заблокировать", callback_data="menu_ban")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "       🛡  **HideRealm** TG2FA\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👋 Привет, **{username or 'игрок'}**!\n\n"
        f"🆔 Ваш UserID: `{user_id}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "       📋 Панель управления\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    tg_id = query.from_user.id

    if data == "menu_link":
        uuid, _ = storage.get_player_by_telegram(tg_id)
        if uuid:
            await query.edit_message_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔗  **Привязка аккаунта**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ Вы уже привязали аккаунт!\n\n"
                "Используйте /unlink для отвязки.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]]),
                parse_mode="Markdown"
            )
            return
        # Generate code
        code = ''.join(random.choices(string.digits, k=6))
        # We store it temporarily - will be matched when player enters in Minecraft
        storage.create_link_code_pending(tg_id, code)
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔗  **Привязка аккаунта**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔑 Ваш код: `{code}`\n\n"
            "📝 **Как привязать:**\n"
            "1. Зайди на сервер\n"
            "2. В чате напиши `/link`\n"
            "3. Увидишь предупреждение\n"
            "4. Напиши `/link` ещё раз\n"
            "5. Введи этот код\n\n"
            "⏰ Код действителен **5 минут**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Новый код", callback_data="menu_link")],
                [InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]
            ]),
            parse_mode="Markdown"
        )

    elif data == "menu_unlink":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await query.edit_message_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔓  **Отвязка аккаунта**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ У вас нет привязанных аккаунтов.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]]),
                parse_mode="Markdown"
            )
            return
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔓  **Отвязка аккаунта**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎮 Аккаунт: `{info['username']}`\n\n"
            "⚠️ Вы уверены?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да, отвязать", callback_data="confirm_unlink")],
                [InlineKeyboardButton("❌ Нет", callback_data="menu_back")]
            ]),
            parse_mode="Markdown"
        )

    elif data == "confirm_unlink":
        storage.unlink_telegram(tg_id)
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔓  **Отвязка аккаунта**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Аккаунт успешно отвязан!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]]),
            parse_mode="Markdown"
        )

    elif data == "menu_status":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await query.edit_message_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📊  **Информация об аккаунте**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ У вас нет привязанных аккаунтов.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]]),
                parse_mode="Markdown"
            )
            return
        online = "🟢 В сети" if info.get("online") else "🔴 Не в сети"
        banned = "✅ Да" if info.get("banned") else "❌ Нет"
        tfa = "✅ Включена" if info.get("tfa_enabled") else "❌ Выключена"
        text = (
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📊  **Информация об аккаунте**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎮 Ник: `{info['username']}`\n"
            f"📡 Статус: {online}\n"
            f"🚫 Блокировка: {banned}\n"
            f"🛡 2FA: {tfa}\n"
            f"🌐 IP: `{info.get('last_ip', '—')}`\n"
            f"📍 Местоположение: {info.get('last_city', '—')}, {info.get('last_country', '—')}\n"
        )
        keyboard = []
        if info.get("banned"):
            keyboard.append([InlineKeyboardButton("✅ Разблокировать", callback_data="do_unban")])
        if info.get("online"):
            keyboard.append([InlineKeyboardButton("👢 Кикнуть", callback_data="do_kick")])
        else:
            keyboard.append([InlineKeyboardButton("🔑 Восстановить пароль", callback_data="do_restore")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="menu_back")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_tfa":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await query.edit_message_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🛡  **Двухэтапная авторизация**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ У вас нет привязанных аккаунтов.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]]),
                parse_mode="Markdown"
            )
            return
        current = info.get("tfa_enabled", False)
        new = not current
        storage.set_tfa(uuid, new)
        state = "включена ✅" if new else "выключена ❌"
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🛡  **Двухэтапная авторизация**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"2FA **{state}**\n\n"
            + ("🔒 Теперь при входе нужно подтверждать через Telegram" if new else "🔓 Теперь вход без подтверждения"),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]]),
            parse_mode="Markdown"
        )

    elif data == "menu_restore":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await query.edit_message_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔑  **Восстановление пароля**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ У вас нет привязанных аккаунтов.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]]),
                parse_mode="Markdown"
            )
            return
        chars = string.ascii_letters + string.digits
        new_password = ''.join(random.choices(chars, k=13))
        storage.create_action("restore", uuid, {"password": new_password})
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔑  **Восстановление пароля**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎮 Аккаунт: `{info['username']}`\n\n"
            f"🔐 Новый пароль: `{new_password}`\n\n"
            "⚠️ **Обязательно смените пароль** после захода!\n"
            "Команда: `/cp <новый_пароль>`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]]),
            parse_mode="Markdown"
        )

    elif data == "menu_kick":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await query.edit_message_text("❌ У вас нет привязанных аккаунтов.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]]))
            return
        storage.create_action("kick", uuid)
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👢  **Кик с сервера**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Аккаунт был кикнут!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]]),
            parse_mode="Markdown"
        )

    elif data == "menu_ban":
        uuid, info = storage.get_player_by_telegram(tg_id)
        if not info:
            await query.edit_message_text("❌ У вас нет привязанных аккаунтов.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]]))
            return
        storage.set_banned(uuid, True)
        storage.create_action("ban", uuid)
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🚫  **Блокировка аккаунта**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Аккаунт был заблокирован!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_back")]]),
            parse_mode="Markdown"
        )

    elif data == "do_unban":
        uuid, _ = storage.get_player_by_telegram(tg_id)
        if uuid:
            storage.set_banned(uuid, False)
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅  **Разблокировка**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Аккаунт был разблокирован!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_status")]]),
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
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_status")]]),
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
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_status")]]),
                parse_mode="Markdown"
            )

    elif data == "menu_back":
        user = update.effective_user
        text = (
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "       🛡  **HideRealm** TG2FA\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👋 Привет, **{user.username or 'игрок'}**!\n\n"
            f"🆔 Ваш UserID: `{tg_id}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "       📋 Панель управления\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")


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


# /link command - for manual code entry
async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, _ = storage.get_player_by_telegram(tg_id)
    if uuid:
        await update.message.reply_text("❌ Вы уже привязали аккаунт!")
        return

    if not context.args:
        # Generate code
        code = ''.join(random.choices(string.digits, k=6))
        storage.create_link_code_pending(tg_id, code)
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔗  **Привязка аккаунта**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔑 Ваш код: `{code}`\n\n"
            "📝 Зайди на сервер и напиши `/link` дважды в чат.",
            parse_mode="Markdown"
        )
        return

    code = context.args[0]
    info = storage.check_link_code(code)
    if not info:
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
            "🛡 Двухэтапная авторизация: ❌ Выключена\n\n"
            "Включите 2FA для защиты аккаунта!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Ошибка при привязке.")


# Simple command aliases
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
        f"📊 **{info['username']}**\n"
        f"📡 {online} | 🚫 {'Заблокирован' if info.get('banned') else 'Нет'} | 🛡 {'2FA' if info.get('tfa_enabled') else '—'}",
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
    await update.message.reply_text(f"🛡 Двухэтапная авторизация {'включена ✅' if new else 'выключена ❌'}")


async def cmd_restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uuid, info = storage.get_player_by_telegram(tg_id)
    if not info:
        await update.message.reply_text("❌ У вас нет привязанных аккаунтов.")
        return
    chars = string.ascii_letters + string.digits
    new_password = ''.join(random.choices(chars, k=13))
    storage.create_action("restore", uuid, {"password": new_password})
    await update.message.reply_text(
        f"🔑 Новый пароль: `{new_password}`\n\n"
        "⚠️ Смените после захода: `/cp <пароль>`",
        parse_mode="Markdown"
    )


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

    # Menu callbacks
    app.add_handler(CallbackQueryHandler(handle_login_button, pattern="^(confirm|kick|ban):"))
    app.add_handler(CallbackQueryHandler(handle_menu, pattern="^menu_|confirm_unlink|do_"))

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link))
    app.add_handler(CommandHandler("unlink", cmd_unlink))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("tfa", cmd_tfa))
    app.add_handler(CommandHandler("restore", cmd_restore))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("ban", cmd_ban))

    logger.info("Starting bot polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
