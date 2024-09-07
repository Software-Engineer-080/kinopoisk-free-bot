from aiogram.fsm.state import State, StatesGroup


class Owner_state(StatesGroup):
    fill_all_photo = State()
    fill_new_photo = State()
    fill_add_photo = State()
    fill_photo_for = State()
    fill_photo_desc = State()

    fill_add_admin = State()
    fill_del_admin = State()
