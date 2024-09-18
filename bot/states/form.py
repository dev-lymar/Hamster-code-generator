from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    language_selection = State()
    user_id_entry = State()


class FormSendToUser(StatesGroup):
    user_id_entry = State()
    message_text_entry = State()
    image_entry = State()


class DonationState(StatesGroup):
    amount_entry = State()
