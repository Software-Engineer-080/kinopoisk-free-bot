from aiogram.fsm.state import State, StatesGroup


class User_state(StatesGroup):
    fill_name_film = State()
    fill_genres_film = State()
