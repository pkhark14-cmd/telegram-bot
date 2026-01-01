import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ChatPermissions

TOKEN = "8436865710:AAE7y8-xJThk-MlkrfNaJt_EazxCJJn6KGw"
OWNER_ID = 8286170020  # твой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def is_admin(chat_id, user_id):
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in ("administrator", "creator")


@dp.message(CommandStart())
async def start(m: types.Message):
    await m.reply("🤖 Бот запущен и работает")


@dp.message()
async def handler(m: types.Message):
    if not m.text:
        return

    text = m.text.lower().strip()

    # 📌 ПРАВИЛА — ДОСТУПНО ВСЕМ
    if text == "!правила":
        await m.reply(
            "📌 ПРАВИЛА ГРУППЫ\n"
            "1️⃣ Без спама\n"
            "2️⃣ Без оскорблений\n"
            "3️⃣ Без флуда\n"
            "4️⃣ Слушать админов\n\n"
            "❗ Нарушение = мут / кик / бан"
        )
        return

    # 👮 СПИСОК АДМИНОВ
    if text in ("!админы", "админы"):
        admins = await bot.get_chat_administrators(m.chat.id)
        msg = "👮 Администраторы группы:\n"
        for admin in admins:
            user = admin.user
            if user.username:
                msg += f"• {user.first_name} (@{user.username})\n"
            else:
                msg += f"• {user.first_name}\n"
        await m.reply(msg)
        return

    # дальше — ТОЛЬКО ответом на сообщение
    if not m.reply_to_message:
        return

    # проверка админа
    if not await is_admin(m.chat.id, m.from_user.id):
        return

    target = m.reply_to_message.from_user

    # если пользователь уже вышел
    member = await bot.get_chat_member(m.chat.id, target.id)
    if member.status == "left":
        await m.reply("❌ Пользователь уже покинул чат")
        return

    # 🔨 КИК
    if text in ("!кик", "кик"):
        await bot.kick_chat_member(m.chat.id, target.id)
        await m.reply(f"👢 {target.first_name} кикнут")

    # ⛔ БАН
    elif text in ("!бан", "бан"):
        await bot.ban_chat_member(m.chat.id, target.id)
        await m.reply(f"⛔ {target.first_name} забанен")

    # 🔇 МУТ
    elif text in ("!мут", "мут"):
        await bot.restrict_chat_member(
            m.chat.id,
            target.id,
            ChatPermissions(can_send_messages=False)
        )
        await m.reply(f"🔇 {target.first_name} замучен")

    # 🔊 РАЗМУТ
    elif text in ("!размут", "размут"):
        await bot.restrict_chat_member(
            m.chat.id,
            target.id,
            ChatPermissions(can_send_messages=True)
        )
        await m.reply(f"🔊 {target.first_name} размучен")

    # 👑 ВЫДАТЬ АДМИНА
    elif text in ("+админ", "повысить"):
        await bot.promote_chat_member(
            m.chat.id,
            target.id,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True
        )
        await m.reply(f"👑 {target.first_name} повышен до админа")

    # ⬇️ СНЯТЬ АДМИНА
    elif text in ("-админ", "разжаловать"):
        await bot.promote_chat_member(
            m.chat.id,
            target.id,
            can_delete_messages=False,
            can_restrict_members=False,
            can_invite_users=False
        )
        await m.reply(f"⬇️ {target.first_name} разжалован")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

