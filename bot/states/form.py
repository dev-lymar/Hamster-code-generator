from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    choosing_language = State()
    waiting_for_user_id = State()


class FormSendToUser(StatesGroup):
    waiting_for_user_id_for_message = State()
    waiting_for_message_text = State()
    waiting_for_image = State()
