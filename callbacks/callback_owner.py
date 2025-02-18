import logging
from db import User
from datetime import datetime
from states import default_state
from buttons import inline_buttons
from aiogram import Router, F, Bot
from filters import IsOwner, throttle
from setting import load_config, Config
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.default import DefaultBotProperties
from storage import menu_stats_desc, stat_menu, owner_menu_desc, owner_menu, search_menu_desc, search_menu


# --------------------------------- CONFIGURATION ---------------------------------


owner_call_router = Router()

config: Config = load_config()

logger = logging.getLogger(__name__)

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode="HTML"))


# --------------------------------- MENU ---------------------------------


# Функция просмотра статистики по пользователям
@owner_call_router.callback_query(F.data == "🔑 Пользователи 🔑", IsOwner(), StateFilter(default_state))
@throttle(2)
async def statistic_user(callback: CallbackQuery) -> None:
    """
    Позволяет вывести статистику по всем пользователям и сегодняшним

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    conn = User.select()
    new_conn = conn.dicts()
    all_user = len(list(new_conn))

    data_now = datetime.now().replace(microsecond=0)

    user_today = User.select().where(User.date_reg >= data_now.replace(hour=0, minute=0, second=0))
    new_user_today = user_today.dicts()
    all_user_today = len(list(new_user_today))

    await callback.message.edit_text(text=menu_stats_desc.format(all_user, all_user_today, data_now),
                                     reply_markup=await inline_buttons(buttons_lst=stat_menu))


# Функция обновления статистики по пользователям
@owner_call_router.callback_query(F.data == "Обновить 🔄", IsOwner(), StateFilter(default_state))
@throttle(2)
async def statistic_user_repeat(callback: CallbackQuery) -> None:
    """
    Позволяет обновить статистику по всем пользователям и сегодняшним

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    conn = User.select()
    new_conn = conn.dicts()
    all_user = len(list(new_conn))

    data_now = datetime.now().replace(microsecond=0)

    user_today = User.select().where(User.date_reg >= data_now.replace(hour=0, minute=0, second=0))
    new_user_today = user_today.dicts()
    all_user_today = len(list(new_user_today))

    await callback.message.edit_text(text=menu_stats_desc.format(all_user, all_user_today, data_now),
                                     reply_markup=await inline_buttons(buttons_lst=stat_menu))


# --------------------------------- OTHERS ---------------------------------


# Функция перехода в главное меню владельцем
@owner_call_router.callback_query(F.data == "Главное меню", IsOwner(), StateFilter(default_state))
@throttle(2)
async def go_main_menu_own(callback: CallbackQuery) -> None:
    """
    Позволяет вернуться в главное меню

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    await callback.message.edit_text(text=owner_menu_desc, reply_markup=await inline_buttons(buttons_lst=owner_menu))


# Функция возврата к критериям поиска из пагинации владельцем
@owner_call_router.callback_query(F.data == "Вернуться ↘️", IsOwner(), StateFilter(default_state))
@throttle(2)
async def comeback_menu_own(callback: CallbackQuery) -> None:
    """
    Позволяет вернуться в меню поиска из пагинации

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Raises
    ------
    TelegramBadRequest
        Ловит исключение невозможности удаления сообщения

    Returns
    -------
    None
    """
    try:
        await callback.message.delete()

    except TelegramBadRequest:
        pass

    await callback.message.answer(text=search_menu_desc, disable_notification=True,
                                  reply_markup=await inline_buttons(buttons_lst=search_menu))


# Функция возврата в главное меню из пагинации владельцем
@owner_call_router.callback_query(F.data == "Выйти ⏏️", IsOwner(), StateFilter(default_state))
@throttle(2)
async def comeback_menu_own_now(callback: CallbackQuery) -> None:
    """
    Позволяет вернуться в главное меню из пагинации

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Raises
    ------
    TelegramBadRequest
        Ловит исключение невозможности удаления сообщения

    Returns
    -------
    None
    """
    try:
        await callback.message.delete()

    except TelegramBadRequest:
        pass

    await callback.message.answer(text=owner_menu_desc, disable_notification=True,
                                  reply_markup=await inline_buttons(buttons_lst=owner_menu))
