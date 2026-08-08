import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Update

BOT_TOKEN = "8797637018:AAEPb5IZ62NnXEp5hhbVFhzhI1gcVMW8fFg"

app = Flask(__name__)
chat_rules = {}


async def is_admin(bot: Bot, message: types.Message) -> bool:
    if message.chat.type == "private":
        return False
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in ["administrator", "creator"]


async def process_update(update_data):
    # Создаем сессию бота внутри каждого запроса Vercel
    async with Bot(token=BOT_TOKEN) as bot:
        dp = Dispatcher()

        @dp.message(Command("start"))
        async def start_cmd(message: types.Message):
            await message.reply("Привет! Добавь меня в группу и сделай администратором.")

        @dp.message(Command("set_rules"))
        async def set_rules_cmd(message: types.Message):
            if not await is_admin(bot, message):
                await message.reply("❌ Эта команда доступна только администраторам.")
                return
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply("Использование: `/set_rules Текст правил`")
                return
            chat_rules[message.chat.id] = args[1]
            await message.reply("✅ Правила чата обновлены!")

        @dp.message(Command("rules"))
        async def get_rules_cmd(message: types.Message):
            rules = chat_rules.get(message.chat.id, "Правила еще не установлены.")
            await message.reply(f"📋 **Правила чата:**\n\n{rules}")

        @dp.message(Command("set_title"))
        async def set_title_cmd(message: types.Message):
            if not await is_admin(bot, message):
                await message.reply("❌ Эта команда доступна только администраторам.")
                return
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply("Использование: `/set_title Новое название`")
                return
            try:
                await bot.set_chat_title(chat_id=message.chat.id, title=args[1])
                await message.reply("✅ Название группы изменено!")
            except Exception as e:
                await message.reply(f"❌ Ошибка: {e}")

        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)


@app.route("/", methods=["POST"])
def webhook():
    if request.method == "POST":
        data = request.get_json(force=True)
        asyncio.run(process_update(data))
        return "ok", 200
    return "Bot is running!", 200


@app.route("/", methods=["GET"])
def index():
    return "Bot status: OK"
