import telebot
from flask import Flask, request

BOT_TOKEN = "8797637018:AAEPb5IZ62NnXEp5hhbVFhzhI1gcVMW8fFg"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# Память для правил
chat_rules = {}


def is_admin(message):
    if message.chat.type == "private":
        return False
    status = bot.get_chat_member(message.chat.id, message.from_user.id).status
    return status in ["administrator", "creator"]


@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, "Привет! Добавь меня в группу и сделай администратором.")


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


# Прием Webhook от Telegram
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
