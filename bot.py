import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ChatMemberStatus

TOKEN = "Token"
OWNER_ID = 8286170020  # твой айди (овнер)

bot = Bot(TOKEN)
dp = Dispatcher()

# -------------------------
# Хранилище админов
# owner > admin1 > admin2
# -------------------------
ADMINS = {
    OWNER_ID: 3  # уровень 3 — создатель
}

def get_level(user_id: int) -> int:
    return ADMINS.get(user_id, 0)

# -------------------------
# Команда /addadmin <id> <level>
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

    ADMINS[uid] = lvl
    await message.answer(f"✅ Админ {uid} добавлен (уровень {lvl})")

# -------------------------
# КИК с подтверждением
# -------------------------
@dp.message(Command("kick"))
async def kick_request(message: types.Message):
    if not message.reply_to_message:
        return await message.answer("Ответь на сообщение пользователя")

    sender_lvl = get_level(message.from_user.id)
    if sender_lvl == 0:
        return

    target = message.reply_to_message.from_user

    # если овнер — сразу кик
    if message.from_user.id == OWNER_ID:
        await bot.ban_chat_member(message.chat.id, target.id)
        await message.answer("👢 Пользователь кикнут")
        return

    # запрос овнеру
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Разрешить",
                callback_data=f"kick_yes:{message.chat.id}:{target.id}"
            ),
            InlineKeyboardButton(
                text="❌ Запретить",
                callback_data="kick_no"
            )
        ]
    ])

    await bot.send_message(
        OWNER_ID,
        f"🔔 Запрос на КИК\n"
        f"От: {message.from_user.id}\n"
        f"Кого: {target.id}\n"
        f"Чат: {message.chat.id}",
        reply_markup=kb
    )

    await message.answer("⏳ Запрос отправлен владельцу")

# -------------------------
# Callback кнопки
# -------------------------
@dp.callback_query(F.data.startswith("kick_yes"))
async def kick_yes(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return

    _, chat_id, user_id = call.data.split(":")
    await bot.ban_chat_member(int(chat_id), int(user_id))
    await call.message.edit_text("✅ Кик разрешён и выполнен")

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

