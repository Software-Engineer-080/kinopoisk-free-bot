from aiogram.fsm.state import default_state, State, StatesGroup


class Start_state(StatesGroup):
    fill_name = State()
    fill_birthday = State()
    fill_phone = State()
