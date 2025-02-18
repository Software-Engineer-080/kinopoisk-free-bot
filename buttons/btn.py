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


# Функция установки меню команд бота
async def set_main_menu(bot: Bot) -> None:
    """
    Создаёт и устанавливает меню команд для телеграмм бота всех пользователей

    Parameters
    ----------
    bot : Bot
        Объект телеграмм бота для оперативной работы с ним

    Returns
    -------
    None
    """
    main_menu_commands = [

        BotCommand(command="/start", description="Запуск бота 🚀"),

        BotCommand(command="/help", description="Команды бота ℹ️"),

        BotCommand(command="/history", description="История запросов 📜"),

        BotCommand(command="/low", description="Фильмы с малым бюджетом ⬇️"),

        BotCommand(command="/high", description="Фильмы с большим бюджетом ⬆️"),

    ]

    await bot.set_my_commands(main_menu_commands)


# Функция создания реплай клавиатуры для получения номера телефона
async def phone_btn() -> ReplyKeyboardMarkup:
    """
    Создаёт текстовую клавиатуру кнопки для передачи номера телефона пользователя

    Parameters
    ----------
    Не принимает никаких аргументов

    Returns
    -------
    key_phone : ReplyKeyboardMarkup
        Текстовая клавиатура кнопки передачи номера телефона
    """
    kb_builder = ReplyKeyboardBuilder()

    contact_btn = KeyboardButton(text="Мой номер", request_contact=True)

    kb_builder.row(contact_btn)

    key_phone = kb_builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

    return key_phone
