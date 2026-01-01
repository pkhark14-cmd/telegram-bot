import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

TOKEN = "8436865710:AAE7y8-xJThk-MlkrfNaJt_EazxCJJn6KGw"

OWNER_ID = 8286170020  # 👑 ВЛАДЕЛЕЦ

# admin_id: level
ADMINS = {
    OWNER_ID: 999
}

bot = Bot(TOKEN)
dp = Dispatcher()


# ---------- HELPERS ----------

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


def admin_level(user_id: int) -> int:
    return ADMINS.get(user_id, 0)


async def get_chat_admin_ids(chat_id: int) -> set[int]:
    admins = await bot.get_chat_administrators(chat_id)
    return {a.user.id for a in admins}


# ---------- COMMANDS ----------

@dp.message(Command("start"))
async def start(m: Message):
    await m.reply("✅ Бот онлайн")


# ➕ +админ <level> (reply)
@dp.message(F.text.startswith("+админ"))
async def add_admin(m: Message):
    if not is_owner(m.from_user.id):
        return

    if not m.reply_to_message:
        return await m.reply("Ответь на сообщение пользователя")

    try:
        level = int(m.text.split()[1])
    except:
        return await m.reply("Формат: +админ <level>")

    target = m.reply_to_message.from_user
    ADMINS[target.id] = level

    await m.reply(f"✅ {target.full_name} теперь админ уровня {level}")


# ➖ -админ (reply)
@dp.message(F.text == "-админ")
async def remove_admin(m: Message):
    if not is_owner(m.from_user.id):
        return

    if not m.reply_to_message:
        return

    target = m.reply_to_message.from_user
    if target.id == OWNER_ID:
        return await m.reply("Нельзя удалить owner")

    ADMINS.pop(target.id, None)
    await m.reply("❌ Админ удалён")


# 👢 /kick (reply)
@dp.message(Command("kick"))
async def kick(m: Message):
    if not m.reply_to_message:
        return

    sender = m.from_user
    target = m.reply_to_message.from_user

    if not is_admin(sender.id):
        return

    if is_admin(target.id):
        return await m.reply("❌ Нельзя кикнуть админа")

    chat_admins = await get_chat_admin_ids(m.chat.id)
    if target.id in chat_admins:
        return await m.reply("❌ Сначала убери админку в Telegram")

    try:
        await bot.ban_chat_member(m.chat.id, target.id)
        await bot.unban_chat_member(m.chat.id, target.id)
        await m.reply("👢 Пользователь кикнут")
    except TelegramBadRequest as e:
        await m.reply(f"Ошибка: {e.message}")


# 📩 если админа кикнули
@dp.message(F.new_chat_members)
async def admin_kicked_notice(m: Message):
    for user in m.new_chat_members:
        if is_admin(user.id):
            await bot.send_message(
                OWNER_ID,
                f"⚠️ Админа {user.full_name} добавили обратно в чат"
            )


# ---------- START ----------

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
