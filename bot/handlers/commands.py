from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from config import BOT_ID, bot
from database.database import get_session
from filters.admin_filter import AdminFilter
from handlers.admin_handlers import handle_admin_command_handler
from handlers.handlers import change_language_logic_handler, set_user_commands, welcome_command_handler

router = Router()


@router.message(Command('start'))
async def command_start(message: Message):
    async with await get_session() as session:
        user = message.from_user
        user_id = user.id if user.id != BOT_ID else message.chat.id
        chat_id = message.chat.id

        await set_user_commands(bot, user_id)
        await welcome_command_handler(session, message, user_id, chat_id, user)


@router.message(Command("change_lang"))
async def command_change_lang(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await change_language_logic_handler(message, user_id, state)

    await set_user_commands(bot, user_id)


@router.message(Command('admin'), AdminFilter())
async def command_admin(message: Message):
    async with await get_session() as session:
        user = message.from_user
        user_id = user.id if user.id != BOT_ID else message.chat.id

        await handle_admin_command_handler(session, message, user_id)


def register_commands_handler(dp):
    dp.include_router(router)
