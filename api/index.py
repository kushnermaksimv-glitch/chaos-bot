import telebot
from telebot import types
from flask import Flask, request
import random
import string

BOT_TOKEN = "8797637018:AAEPb5IZ62NnXEp5hhbVFhzhI1gcVMW8fFg"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

chat_rules = {}
processed_updates = set()  # Защита от повторных вызовов Telegram

RANDOM_TITLES = [
    "🎪 БЕЗУМНЫЙ ЦИРК", "🛸 СЕКТА НЛО", "👾 КЛУБ АНОНИМНЫХ ГЕЙМЕРОВ",
    "🔥 ЧАТ НА ГРАНИ ВЗРЫВА", "🍕 ПОКЛОННИКИ ПИЦЦЫ С АНАНАСАМИ",
    "🤪 ДУРДОМ №13", "🤖 ВОССТАНИЕ МАШИН", "⚡ ОПАСНАЯ ЗОНА",
    "🗿 КЛУБ ГИГАЧАДОВ", "🌋 ТЕРРИТОРИЯ ХАОСА"
]

RANDOM_RULES = [
    "1. Запрещено писать букву 'А'.\n2. Все сообщения отправлять только гифками.\n3. Админ всегда прав.",
    "1. Писать только капсом!\n2. Спамить смайликами в каждом сообщении.\n3. Не спорить с ботом.",
    "1. Говорить только загадками.\n2. Каждое сообщение начинать со слова 'Ибо'.\n3. Никакой логики!",
    "1. Все должны хвалить пиццу.\n2. Ругаться запрещено, можно только мурчать.\n3. Правил нет!",
    "1. Сообщения без стикеров удаляются из памяти.\n2. Каждый час меняем тему.\n3. Полная анархия!"
]

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
        types.BotCommand("rules", "Посмотреть правила чата"),
        types.BotCommand("set_rules", "Установить и закрепить правила (админам)"),
        types.BotCommand("set_title", "Изменить название группы (админам)"),
        types.BotCommand("chaos", "Абсолютный хаос: настройки, правила и тэг 💥")
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
        "**Доступные команды:**\n"
        "📋 `/rules` — Посмотреть текущие правила группы.\n"
        "⚙️ `/set_rules <текст>` — Задать и закрепить правила.\n"
        "✏️ `/set_title <название>` — Изменить название группы.\n"
        "💥 `/chaos` — Изменить настройки и выдать случайный тэг.\n\n"
        "💡 *Для работы выдайте боту все права администратора!*"
    )
    bot.reply_to(message, start_text, parse_mode="Markdown")


@bot.message_handler(commands=['chaos'])
def chaos_cmd(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам.")
        return

    chat_id = message.chat.id
    errors = []

    # 1. Выдача случайного тэга
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

    # 2. Набор реакций
    try:
        chosen_reactions = random.choice(REACTION_SETS)
        bot.set_chat_available_reactions(chat_id, available_reactions=chosen_reactions)
    except Exception as e:
        errors.append(f"Реакции: {e}")

    # 3. Разрешения участников
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

    # 4. Название группы
    new_title = random.choice(RANDOM_TITLES)
    try:
        bot.set_chat_title(chat_id, new_title)
    except Exception as e:
        errors.append(f"Название: {e}")

    # 5. Описание и правила
    new_rules = random.choice(RANDOM_RULES)
    chat_rules[chat_id] = new_rules

    try:
        bot.set_chat_description(chat_id, f"🔥 ХАОС! Правила:\n{new_rules[:200]}")
        pinned_msg = bot.send_message(
            chat_id, 
            f"💥 **РЕЖИМ ХАОСА! НОВЫЕ ПРАВИЛА:**\n\n{new_rules}", 
            parse_mode="Markdown"
        )
        bot.pin_chat_message(chat_id, pinned_msg.message_id)
    except Exception as e:
        errors.append(f"Правила: {e}")

    report = (
        f"💥 **РЕЖИМ ХАОСА АКТИВИРОВАН!** 💥\n\n"
        f"🏷 **Новое название:** {new_title}\n"
        f"👤 **Тэг пользователю [{target_user.first_name}](tg://user?id={target_user.id}):** `{random_tag}`\n"
        f"🎭 **Реакции:** Обновлены\n"
        f"📌 **Правила:** Закреплены\n\n"
        f"🔒 **Разрешения участников:**\n"
        f"- Фото: {'✅' if p_photos else '❌'}\n"
        f"- Видео/Файлы: {'✅' if p_videos else '❌'}\n"
        f"- Стикеры/GIF: {'✅' if p_other else '❌'}\n"
        f"- Опросы: {'✅' if p_polls else '❌'}\n"
        f"- Приглашения: {'✅' if p_invites else '❌'}"
    )

    if errors:
        report += f"\n\n⚠️ *Ошибки:* " + ", ".join(errors)

    bot.send_message(chat_id, report, parse_mode="Markdown")


@bot.message_handler(commands=['set_rules'])
def set_rules_cmd(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам.")
        return

    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        bot.reply_to(message, "Использование: `/set_rules Текст правил`", parse_mode="Markdown")
        return

    new_rules = text_parts[1]
    chat_rules[message.chat.id] = new_rules

    try:
        pinned_msg = bot.send_message(
            message.chat.id, 
            f"📌 **ОФИЦИАЛЬНЫЕ ПРАВИЛА ЧАТА:**\n\n{new_rules}", 
            parse_mode="Markdown"
        )
        bot.pin_chat_message(message.chat.id, pinned_msg.message_id)
        bot.reply_to(message, "✅ Правила установлены и закреплены!")
    except Exception as e:
        bot.reply_to(message, f"✅ Правила сохранены. Ошибка закрепления: {e}")


@bot.message_handler(commands=['rules'])
def get_rules_cmd(message):
    rules = chat_rules.get(message.chat.id, "Правила в этом чате еще не установлены.")
    bot.reply_to(message, f"📋 *Правила чата:*\n\n{rules}", parse_mode="Markdown")


@bot.message_handler(commands=['set_title'])
def set_title_cmd(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам.")
        return

    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        bot.reply_to(message, "Использование: `/set_title Новое название`", parse_mode="Markdown")
        return

    try:
        bot.set_chat_title(message.chat.id, text_parts[1])
        bot.reply_to(message, "✅ Название группы изменено!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)

            # Блокировка бесконечных повторов от Telegram
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
