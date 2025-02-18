import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


logger = logging.getLogger(__name__)


# Функция создания инлайн клавиатуры
async def inline_buttons(buttons_lst: list, buttons_per_row: int = 2) -> InlineKeyboardMarkup:
    """
    Создаёт инлайн клавиатуру кнопок под текстом

    Parameters
    ----------
    buttons_lst : list
        Список строковых значений под кнопки

    buttons_per_row : int
        Количество кнопок в строке

    Returns
    -------
    markup : InlineKeyboardMarkup
        Инлайновая клавиатура кнопок
    """
    button_row = []

    for i in range(0, len(buttons_lst), buttons_per_row):

        button_new = []

        for j in range(buttons_per_row):

            if i + j < len(buttons_lst):

                if buttons_lst[i + j] is not None:

                    button_new.append(InlineKeyboardButton(text=buttons_lst[i + j], callback_data=buttons_lst[i + j]))

        button_row.append(button_new)

    markup = InlineKeyboardMarkup(inline_keyboard=button_row)

    return markup


# Функция создания инлайн клавиатуры для жанрового поиска
async def genres_menu() -> InlineKeyboardMarkup:
    """
    Создаёт красивую и читаемую инлайн клавиатуру кнопок под текстом для выбора жанра

    Parameters
    ----------
    Не принимает никаких аргументов

    Returns
    -------
    genres_menu_button : InlineKeyboardMarkup
        Инлайновая клавиатура кнопок
    """
    genres_menu_button = InlineKeyboardBuilder()

    btn_1 = InlineKeyboardButton(text="Аниме", callback_data="Аниме")
    btn_2 = InlineKeyboardButton(text="Биография", callback_data="Биография")
    btn_3 = InlineKeyboardButton(text="Боевик", callback_data="Боевик")
    btn_4 = InlineKeyboardButton(text="Вестерн", callback_data="Вестерн")
    btn_5 = InlineKeyboardButton(text="Военный", callback_data="Военный")
    btn_6 = InlineKeyboardButton(text="Детектив", callback_data="Детектив")
    btn_7 = InlineKeyboardButton(text="Детский", callback_data="Детский")
    btn_8 = InlineKeyboardButton(text="18 +", callback_data="18 +")
    btn_9 = InlineKeyboardButton(text="Документалка", callback_data="Документальный")
    btn_10 = InlineKeyboardButton(text="Драма", callback_data="Драма")
    btn_11 = InlineKeyboardButton(text="Игра", callback_data="Игра")
    btn_12 = InlineKeyboardButton(text="История", callback_data="История")
    btn_13 = InlineKeyboardButton(text="Комедия", callback_data="Комедия")
    btn_14 = InlineKeyboardButton(text="Концерт", callback_data="Концерт")
    btn_15 = InlineKeyboardButton(text="Короткометражка", callback_data="Короткометражка")
    btn_16 = InlineKeyboardButton(text="Криминал", callback_data="Криминал")
    btn_17 = InlineKeyboardButton(text="Мелодрама", callback_data="Мелодрама")
    btn_18 = InlineKeyboardButton(text="Музыка", callback_data="Музыка")
    btn_19 = InlineKeyboardButton(text="Мультфильм", callback_data="Мультфильм")
    btn_20 = InlineKeyboardButton(text="Мюзикл", callback_data="Мюзикл")
    btn_21 = InlineKeyboardButton(text="Новости", callback_data="Новости")
    btn_22 = InlineKeyboardButton(text="Приключения", callback_data="Приключения")
    btn_23 = InlineKeyboardButton(text="Реальное ТВ", callback_data="Реальное ТВ")
    btn_24 = InlineKeyboardButton(text="Семейное", callback_data="Семейное")
    btn_25 = InlineKeyboardButton(text="Спорт", callback_data="Спорт")
    btn_26 = InlineKeyboardButton(text="Ток-Шоу", callback_data="Ток-Шоу")
    btn_27 = InlineKeyboardButton(text="Триллер", callback_data="Триллер")
    btn_28 = InlineKeyboardButton(text="Ужасы", callback_data="Ужасы")
    btn_29 = InlineKeyboardButton(text="Фантастика", callback_data="Фантастика")
    btn_30 = InlineKeyboardButton(text="Нуар", callback_data="Нуар")
    btn_31 = InlineKeyboardButton(text="Фэнтези", callback_data="Фэнтези")
    btn_32 = InlineKeyboardButton(text="Церемония", callback_data="Церемония")

    main = InlineKeyboardButton(text="🔙 НАЗАД", callback_data="🔙 НАЗАД")

    genres_menu_button.row(btn_1, btn_3, btn_4)
    genres_menu_button.row(btn_5, btn_6, btn_7)
    genres_menu_button.row(btn_2, btn_9)
    genres_menu_button.row(btn_8, btn_10, btn_11)
    genres_menu_button.row(btn_12, btn_13, btn_14)
    genres_menu_button.row(btn_15)
    genres_menu_button.row(btn_16, btn_17)
    genres_menu_button.row(btn_18, btn_20, btn_21)
    genres_menu_button.row(btn_19, btn_22)
    genres_menu_button.row(btn_23, btn_24)
    genres_menu_button.row(btn_25, btn_26, btn_27)
    genres_menu_button.row(btn_29, btn_32)
    genres_menu_button.row(btn_28, btn_30, btn_31)

    genres_menu_button.row(main)

    genres_menu_button = genres_menu_button.as_markup(resize_keyboard=True, one_time_keyboard=True)

    return genres_menu_button
