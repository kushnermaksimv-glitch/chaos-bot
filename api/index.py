import telebot
from telebot import types
from flask import Flask, request
import random
import string

BOT_TOKEN = "8797637018:AAEPb5IZ62NnXEp5hhbVFhzhI1gcVMW8fFg"
SECRET_CODE = "7777"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

processed_updates = set()
creators = set()          # Список ID создателей
AVATAR_FILE_IDS = []     # База загруженных аватарок
saved_states = {}        # Хранилище исходного состояния чатов {chat_id: {"permissions": ..., "reactions": ...}}

REACTION_SETS = [
    [types.ReactionTypeEmoji("👍"), types.ReactionTypeEmoji("👎")],
    [types.ReactionTypeEmoji("🤡"), types.ReactionTypeEmoji("💩"), types.ReactionTypeEmoji("🔥")],
    [types.ReactionTypeEmoji("❤️"), types.ReactionTypeEmoji("😍"), types.ReactionTypeEmoji("🎉")],
]


def generate_random_tag(length=8):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+"
    return "".join(random.choice(chars) for _ in range(length))


def setup_bot_commands():
    commands = [
        types.BotCommand("start", "Показать справку"),
        types.BotCommand("login", "Авторизация создателя (/login <код>)"),
        types.BotCommand("save", "Сохранить текущее состояние чата (админам)"),
        types.BotCommand("restore", "Восстановить сохраненное состояние (админам)"),
        types.BotCommand("chaos", "Хаос: настройки, аватарка и тэг (без смены названия) 💥")
    ]
    bot.set_my_commands(commands)


try:
    setup_bot_commands()
except Exception as e:
    print(f"Ошибка при установке меню команд: {e}")


def is_admin(message):
    if message.chat.type == "private":
        return False
    try:
        status = bot.get_chat_member(message.chat.id, message.from_user.id).status
        return status in ["administrator", "creator"]
    except Exception:
        return False


@bot.message_handler(commands=['start'])
def start_cmd(message):
    start_text = (
        "👋 **Привет! Я бот для управления настройками чата.**\n\n"
        "**Команды:**\n"
        "💾 `/save` — Сохранить текущие права и реакции чата.\n"
        "🔄 `/restore` — Вернуть сохраненные права и реакции.\n"
        "💥 `/chaos` — Включить хаос (права, аватарка, тэг).\n"
        "🔐 `/login <пароль>` — Вход в панель создателя (для загрузки фото).\n\n"
        "💡 *Сначала выполните `/save`, чтобы в любой момент отменить хаос!*"
    )
    bot.reply_to(message, start_text, parse_mode="Markdown")


# 1. Авторизация создателя
@bot.message_handler(commands=['login'])
def login_cmd(message):
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        bot.reply_to(message, "⚠️ Использование: `/login <секретный_код>`", parse_mode="Markdown")
        return

    code = text_parts[1].strip()
    if code == SECRET_CODE:
        creators.add(message.from_user.id)
        bot.reply_to(
            message,
            "🔓 **Доступ разрешен!** Теперь отправляйте мне фотографии — они будут сохранены для использования в `/chaos`.\n"
            "🗑 Чтобы очистить фото: `/clear_avatars`.",
            parse_mode="Markdown"
        )
    else:
        bot.reply_to(message, "❌ Неверный код доступа!")


# 2. Сохранение исходного состояния чата
@bot.message_handler(commands=['save'])
def save_cmd(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам.")
        return

    chat_id = message.chat.id
    try:
        chat_info = bot.get_chat(chat_id)
        saved_states[chat_id] = {
            "permissions": chat_info.permissions,
            "reactions": chat_info.available_reactions
        }
        bot.reply_to(
            message,
            "💾 **Начальное состояние чата сохранено!**\n\n"
            "После вызова `/chaos` вы сможите в любой момент вернуть все настройки командой `/restore`.",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при сохранении: {e}")


# 3. Восстановление исходного состояния чата
@bot.message_handler(commands=['restore'])
def restore_cmd(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам.")
        return

    chat_id = message.chat.id
    if chat_id not in saved_states:
        bot.reply_to(
            message,
            "⚠️ **Сохраненное состояние не найдено!**\nСначала выполните команду `/save`.",
            parse_mode="Markdown"
        )
        return

    state = saved_states[chat_id]
    errors = []

    # Восстановление прав
    if state.get("permissions"):
        try:
            bot.set_chat_permissions(chat_id, state["permissions"])
        except Exception as e:
            errors.append(f"Права: {e}")

    # Восстановление реакций
    try:
        bot.set_chat_available_reactions(chat_id, available_reactions=state.get("reactions"))
    except Exception as e:
        errors.append(f"Реакции: {e}")

    report = "🔄 **Начальное состояние чата успешно восстановлено!**"
    if errors:
        report += "\n\n⚠️ *Ошибки:* " + ", ".join(errors)

    bot.send_message(chat_id, report, parse_mode="Markdown")


# 4. Сохранение фото от создателя
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.from_user.id in creators:
        file_id = message.photo[-1].file_id
        AVATAR_FILE_IDS.append(file_id)
        bot.reply_to(
            message,
            f"✅ **Фотография сохранена!**\n📸 Всего аватарок: **{len(AVATAR_FILE_IDS)}**",
            parse_mode="Markdown"
        )


@bot.message_handler(commands=['clear_avatars'])
def clear_avatars_cmd(message):
    if message.from_user.id in creators:
        AVATAR_FILE_IDS.clear()
        bot.reply_to(message, "🗑 Список аватарок очищен!")


# 5. Режим Хаоса (без изменения названия)
@bot.message_handler(commands=['chaos'])
def chaos_cmd(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам.")
        return

    chat_id = message.chat.id
    errors = []

    # Выдача случайного тэга
    target_user = message.from_user
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user

    random_tag = generate_random_tag(8)

    try:
        bot.promote_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            can_manage_chat=True,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_promote_members=False,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False
        )
        bot.set_chat_administrator_custom_title(chat_id, target_user.id, random_tag)
    except Exception as e:
        errors.append(f"Тэг: {e}")

    # Случайная аватарка из загруженных
    if AVATAR_FILE_IDS:
        try:
            random_file_id = random.choice(AVATAR_FILE_IDS)
            file_info = bot.get_file(random_file_id)
            photo_bytes = bot.download_file(file_info.file_path)
            bot.set_chat_photo(chat_id, photo_bytes)
        except Exception as e:
            errors.append(f"Аватарка: {e}")

    # Случайные реакции
    try:
        chosen_reactions = random.choice(REACTION_SETS)
        bot.set_chat_available_reactions(chat_id, available_reactions=chosen_reactions)
    except Exception as e:
        errors.append(f"Реакции: {e}")

    # Случайные разрешения
    p_photos = random.choice([True, False])
    p_videos = random.choice([True, False])
    p_polls = random.choice([True, False])
    p_other = random.choice([True, False])
    p_invites = random.choice([True, False])

    try:
        new_permissions = types.ChatPermissions(
            can_send_messages=True,
            can_send_photos=p_photos,
            can_send_videos=p_videos,
            can_send_audios=p_photos,
            can_send_documents=p_videos,
            can_send_polls=p_polls,
            can_send_other_messages=p_other,
            can_invite_users=p_invites
        )
        bot.set_chat_permissions(chat_id, new_permissions)
    except Exception as e:
        errors.append(f"Разрешения: {e}")

    report = (
        f"💥 **РЕЖИМ ХАОСА АКТИВИРОВАН!** 💥\n\n"
        f"👤 **Тэг пользователю [{target_user.first_name}](tg://user?id={target_user.id}):** `{random_tag}`\n"
        f"🖼 **Аватарка:** Сменена\n"
        f"🎭 **Реакции:** Изменены\n\n"
        f"🔒 **Разрешения участников:**\n"
        f"- Фото: {'✅' if p_photos else '❌'}\n"
        f"- Видео/Файлы: {'✅' if p_videos else '❌'}\n"
        f"- Стикеры/GIF: {'✅' if p_other else '❌'}\n"
        f"- Опросы: {'✅' if p_polls else '❌'}\n"
        f"- Приглашения: {'✅' if p_invites else '❌'}\n\n"
        f"💡 *Вернуть исходное состояние: `/restore`*"
    )

    if errors:
        report += f"\n\n⚠️ *Ошибки:* " + ", ".join(errors)

    bot.send_message(chat_id, report, parse_mode="Markdown")


@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)

            if update and update.update_id:
                if update.update_id in processed_updates:
                    return 'ok', 200
                processed_updates.add(update.update_id)
                if len(processed_updates) > 100:
                    processed_updates.clear()

            bot.process_new_updates([update])
        except Exception as e:
            print(f"Webhook error: {e}")
        return 'ok', 200
    return 'Forbidden', 403


@app.route('/', methods=['GET'])
def index():
    return "Bot is running on Vercel!"
