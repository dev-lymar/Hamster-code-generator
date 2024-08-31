from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    choosing_language = State()
    waiting_for_user_id = State()
