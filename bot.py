import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

TOKEN = "8436865710:AAE7y8-xJThk-MlkrfNaJt_EazxCJJn6KGw"

OWNER_ID = 8286170020  # ТВОЙ ID

# уровни админов
LEVEL_MOD = 1
LEVEL_ADMIN = 2
LEVEL_SENIOR = 3
LEVEL_OWNER = 4

# временное хранилище (для старта, потом можно БД)
admins = {
    OWNER_ID: LEVEL_OWNER
}

pending_actions = {}  # action_id -> data

bot = Bot(TOKEN)
dp = Dispatcher()


def get_level(user_id: int) -> int:
    return admins.get(user_id, 0)


def is_admin(user_id: int) -> bool:
    return get_level(user_id) > 0


async def is_chat_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
    except:
        return False


# ===== ДОБАВЛЕНИЕ АДМИНОВ =====
@dp.message(Command("addadmin"))
async def add_admin(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя")
        return

    level = int(message.text.split()[1])
    target_id = message.reply_to_message.from_user.id

    admins[target_id] = level
    await message.reply(f"✅ Админ добавлен. Уровень: {level}")


# ===== КИК =====
@dp.message(Command("kick"))
async def kick_user(message: Message):
    if not message.reply_to_message:
        return

    actor = message.from_user.id
    target = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    if not is_admin(actor):
        return

    if await is_chat_admin(chat_id, target):
        await message.reply("❌ Нельзя кикать администратора")
        return

    # овнер кикает сразу
    if actor == OWNER_ID:
        await bot.ban_chat_member(chat_id, target)
        await bot.unban_chat_member(chat_id, target)
        await message.reply("✅ Пользователь кикнут")
        return

    # запрос овнеру
    action_id = f"kick:{chat_id}:{target}"
    pending_actions[action_id] = {
        "chat_id": chat_id,
        "target": target
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Разрешить", callback_data=f"approve:{action_id}"),
            InlineKeyboardButton(text="❌ Запретить", callback_data=f"deny:{action_id}")
        ]
    ])

    await bot.send_message(
        OWNER_ID,
        f"⚠️ Запрос на КИК\n"
        f"От: {actor}\n"
        f"Кого: {target}",
        reply_markup=kb
    )

    await message.reply("⏳ Запрос отправлен владельцу")


# ===== БАН =====
@dp.message(Command("ban"))
async def ban_user(message: Message):
    if not message.reply_to_message:
        return

    actor = message.from_user.id
    target = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    if not is_admin(actor):
        return

    if await is_chat_admin(chat_id, target):
        await message.reply("❌ Нельзя банить администратора")
        return

    if actor == OWNER_ID:
        await bot.ban_chat_member(chat_id, target)
        await message.reply("✅ Пользователь забанен")
        return

    action_id = f"ban:{chat_id}:{target}"
    pending_actions[action_id] = {
        "chat_id": chat_id,
        "target": target
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Разрешить", callback_data=f"approve:{action_id}"),
            InlineKeyboardButton(text="❌ Запретить", callback_data=f"deny:{action_id}")
        ]
    ])

    await bot.send_message(
        OWNER_ID,
        f"⚠️ Запрос на БАН\n"
        f"От: {actor}\n"
        f"Кого: {target}",
        reply_markup=kb
    )

    await message.reply("⏳ Запрос отправлен владельцу")


# ===== CALLBACK =====
@dp.callback_query(F.data.startswith("approve"))
async def approve(cb: CallbackQuery):
    if cb.from_user.id != OWNER_ID:
        return

    action_id = cb.data.split("approve:")[1]
    data = pending_actions.pop(action_id, None)

    if not data:
        await cb.answer("❌ Уже обработано")
        return

    chat_id = data["chat_id"]
    target = data["target"]

    if action_id.startswith("kick"):
        await bot.ban_chat_member(chat_id, target)
        await bot.unban_chat_member(chat_id, target)
        text = "✅ Кик подтверждён"
    else:
        await bot.ban_chat_member(chat_id, target)
        text = "✅ Бан подтверждён"

    await cb.message.edit_text(text)


@dp.callback_query(F.data.startswith("deny"))
async def deny(cb: CallbackQuery):
    if cb.from_user.id != OWNER_ID:
        return

    action_id = cb.data.split("deny:")[1]
    pending_actions.pop(action_id, None)
    await cb.message.edit_text("❌ Действие отклонено")


# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

