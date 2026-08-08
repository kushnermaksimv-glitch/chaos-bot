import telebot
from telebot import types
from flask import Flask, request
import urllib.request
import random

BOT_TOKEN = "8797637018:AAEPb5IZ62NnXEp5hhbVFhzhI1gcVMW8fFg"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

chat_rules = {}

# Варианты для случайного выбора
RANDOM_TITLES = [
    "🎪 БЕЗУМНЫЙ ЦИРК",
    "🛸 СЕКТА НЛО",
    "👾 КЛУБ АНОНИМНЫХ ГЕЙМЕРОВ",
    "🔥 ЧАТ НА ГРАНИ ВЗРЫВА",
    "🍕 ПОКЛОННИКИ ПИЦЦЫ С АНАНАСАМИ",
    "🤪 ДУРДОМ №13",
    "🤖 ВОССТАНИЕ МАШИН",
    "⚡ ОПАСНАЯ ЗОНА",
    "🗿 КЛУБ ГИГАЧАДОВ",
    "💃 ТАНЦЫ ДО УТРА",
    "🌋 ТЕРРИТОРИЯ ХАОСА"
]

RANDOM_RULES = [
    "1. Запрещено писать букву 'А'.\n2. Все сообщения отправлять только гифками.\n3. Админ всегда прав.",
    "1. Писать только капсом!\n2. Спамить смайликами в каждом сообщении.\n3. Не спорить с ботом.",
    "1. Говорить только загадками.\n2. Каждое сообщение должно начинаться со слова 'Ибо'.\n3. Никакой логики!",
    "1. Все должны хвалить пиццу.\n2. Ругаться запрещено, можно только мурчать.\n3. Правил нет!",
    "1. Сообщения без стикеров удаляются из памяти.\n2. Каждый час меняем тему.\n3. Полная анархия!"
]

RANDOM_DESCRIPTIONS = [
    "⚠️ Добро пожаловать в хаос. Удачи выжить!",
    "Здесь нет логики. Только чистый рандом.",
    "Если вы это читаете, значит бот опять переписал историю этой группы.",
    "Правила меняются при каждом вызове команды. Пристегните ремни!"
]


def setup_bot_commands():
    commands = [
        types.BotCommand("start", "Показать справку"),
        types.BotCommand("rules", "Посмотреть правила чата"),
        types.BotCommand("set_rules", "Установить правила (только админы)"),
        types.BotCommand("set_title", "Изменить название группы (только админы)"),
        types.BotCommand("chaos", "Активировать рандомный хаос 💥 (только админы)")
    ]
    bot.set_my_commands(commands)


try:
    setup_bot_commands()
except Exception as e:
    print(f"Ошибка при установке меню команд: {e}")


def is_admin(message):
    if message.chat.type == "private":
        return False
    status = bot.get_chat_member(message.chat.id, message.from_user.id).status
    return status in ["administrator", "creator"]


@bot.message_handler(commands=['start'])
def start_cmd(message):
    start_text = (
        "👋 **Привет! Я бот для управления настройками и правилами чата.**\n\n"
        "**Доступные команды:**\n"
        "📋 `/rules` — Посмотреть текущие правила группы.\n"
        "⚙️ `/set_rules <текст>` — Задать новые правила (админам).\n"
        "✏️ `/set_title <название>` — Изменить название группы (админам).\n"
        "💥 `/chaos` — Сгенерировать случайное название, правила и аватарку (админам).\n\n"
        "💡 *Для работы всех функций назначьте меня администратором!*"
    )
    bot.reply_to(message, start_text, parse_mode="Markdown")


# РАНДОМНЫЙ ХАОС
@bot.message_handler(commands=['chaos'])
def chaos_cmd(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам.")
        return

    chat_id = message.chat.id
    errors = []

    # Генерируем случайные параметры
    new_title = random.choice(RANDOM_TITLES)
    new_rules = random.choice(RANDOM_RULES)
    new_desc = random.choice(RANDOM_DESCRIPTIONS)

    # 1. Устанавливаем случайное название
    try:
        bot.set_chat_title(chat_id, new_title)
    except Exception as e:
        errors.append(f"Название: {e}")

    # 2. Устанавливаем случайное описание
    try:
        bot.set_chat_description(chat_id, new_desc)
    except Exception as e:
        errors.append(f"Описание: {e}")

    # 3. Сохраняем новые случайные правила в памяти бота
    chat_rules[chat_id] = new_rules

    # 4. Скачиваем и устанавливаем случайную аватарку
    try:
        random_seed = random.randint(1, 100000)
        img_url = f"https://picsum.photos/500/500?random={random_seed}"
        req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
        photo_bytes = urllib.request.urlopen(req, timeout=5).read()
        bot.set_chat_photo(chat_id, photo_bytes)
    except Exception as e:
        errors.append(f"Аватарка: {e}")

    # Отчет
    status_text = (
        f"💥 **РЕЖИМ ХАОСА АКТИВИРОВАН!** 💥\n\n"
        f"🏷 **Новое название:** {new_title}\n"
        f"📜 **Новые правила:**\n{new_rules}\n\n"
        f"🖼 *Установлена новая случайная аватарка!*"
    )

    if errors:
        status_text += "\n\n⚠️ *Ошибки выполнения (проверьте права бота):*\n"
        for err in errors:
            status_text += f"- {err}\n"

    bot.send_message(chat_id, status_text, parse_mode="Markdown")


@bot.message_handler(commands=['set_rules'])
def set_rules_cmd(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам.")
        return

    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        bot.reply_to(message, "Использование: `/set_rules Текст правил`", parse_mode="Markdown")
        return

    chat_rules[message.chat.id] = text_parts[1]
    bot.reply_to(message, "✅ Правила чата обновлены!")


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
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'ok', 200
    return 'Forbidden', 403


@app.route('/', methods=['GET'])
def index():
    return "Bot is running on Vercel!"
