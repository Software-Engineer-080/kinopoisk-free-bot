from aiogram.fsm.state import State, StatesGroup


class Start_state(StatesGroup):
    fill_name = State()
    fill_birthday = State()
    fill_phone = State()
