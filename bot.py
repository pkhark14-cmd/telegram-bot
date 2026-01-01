import asyncio
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ====== ENV ======
TOKEN = os.getenv("Token")  # берём из Railway
OWNER_ID = 8286170020       # твой Telegram ID

if not TOKEN:
    raise RuntimeError("TOKEN не найден в переменных окружения")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# -------------------------
# Хранилище админов
# уровни: 3 — владелец, 2 — админ, 1 — мод
# -------------------------
ADMINS = {
    OWNER_ID: 3
}

def get_level(user_id: int) -> int:
    return ADMINS.get(user_id, 0)

# -------------------------
# /addadmin <id> <level>
# -------------------------
@dp.message(Command("addadmin"))
async def add_admin(message: types.Message):
    if get_level(message.from_user.id) < 3:
        return

    args = message.text.split()
    if len(args) != 3:
        await message.answer("Использование: /addadmin <id> <1|2>")
        return

    uid = int(args[1])
    lvl = int(args[2])

    if lvl not in (1, 2):
        await message.answer("Уровень может быть только 1 или 2")
        return

    ADMINS[uid] = lvl
    await message.answer(f"✅ Админ {uid} добавлен (уровень {lvl})")

# -------------------------
# /kick (ответом)
# -------------------------
@dp.message(Command("kick"))
async def kick_request(message: types.Message):
    if not message.reply_to_message:
        await message.answer("Нужно ответить на сообщение пользователя")
        return

    if get_level(message.from_user.id) == 0:
        return

    target = message.reply_to_message.from_user

    # владелец — кик сразу
    if message.from_user.id == OWNER_ID:
        await bot.ban_chat_member(message.chat.id, target.id)
        await message.answer("👢 Пользователь кикнут")
        return

    # запрос владельцу
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Разрешить",
            callback_data=f"kick_yes:{message.chat.id}:{target.id}"
        ),
        InlineKeyboardButton(
            text="❌ Запретить",
            callback_data="kick_no"
        )
    ]])

    await bot.send_message(
        OWNER_ID,
        f"🔔 Запрос на кик\n"
        f"От: {message.from_user.id}\n"
        f"Кого: {target.id}\n"
        f"Чат: {message.chat.id}",
        reply_markup=kb
    )

    await message.answer("⏳ Запрос отправлен владельцу")

# -------------------------
# Callback
# -------------------------
@dp.callback_query(F.data.startswith("kick_yes"))
async def kick_yes(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return

    _, chat_id, user_id = call.data.split(":")
    await bot.ban_chat_member(int(chat_id), int(user_id))
    await call.message.edit_text("✅ Кик выполнен")

@dp.callback_query(F.data == "kick_no")
async def kick_no(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    await call.message.edit_text("❌ Кик отклонён")

# -------------------------
# Запуск
# -------------------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


