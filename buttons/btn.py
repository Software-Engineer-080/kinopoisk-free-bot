import logging
from aiogram import Bot
from aiogram.types import BotCommand
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


logger = logging.getLogger(__name__)


# Функция создания реплай клавиатуры
async def buttons(buttons_lst: list, width: int = 3) -> ReplyKeyboardMarkup:

    """
    Создаёт текстовую клавиатуру кнопок

    Parameters
    ----------
    buttons_lst : list
        Список строковых значений под кнопки

    width : int
        Количество кнопок в строке

    Returns
    -------
    keyboard : ReplyKeyboardMarkup
        Текстовая клавиатура кнопок
    """

    repl_list = []

    for i in range(0, len(buttons_lst), width):

        lst = []

        for j in range(width):

            if i + j < len(buttons_lst):

                if buttons_lst[i + j] is not None:

                    lst.append(KeyboardButton(text=buttons_lst[i + j]))

        repl_list.append(lst)

    keyboard = ReplyKeyboardMarkup(keyboard=repl_list, resize_keyboard=True)

    return keyboard


async def set_main_menu(bot: Bot):

    main_menu_commands = [

        BotCommand(command='/start', description='Запуск бота 🚀'),

        BotCommand(command='/help', description='Команды бота'),

        BotCommand(command='/history', description='История запросов'),

        BotCommand(command='/low', description='Минимальный поиск'),

        BotCommand(command='/high', description='Максимальный поиск')

    ]

    await bot.set_my_commands(main_menu_commands)


async def phone_btn():
    kb_builder = ReplyKeyboardBuilder()

    contact_btn = KeyboardButton(text='Мой номер', request_contact=True)

    kb_builder.row(contact_btn)

    key_phone = kb_builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

    return key_phone
