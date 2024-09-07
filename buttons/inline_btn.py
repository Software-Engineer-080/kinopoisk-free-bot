import logging
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
