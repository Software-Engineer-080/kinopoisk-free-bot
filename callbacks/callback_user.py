import json
import random
import aiohttp
import logging
from typing import List, Any
from datetime import datetime
from aiogram import F, Router, Bot
from filters import IsUser, throttle
from aiogram.filters import StateFilter
from setting import Config, load_config
from db import SearchMovie, User, SearchHistory
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.default import DefaultBotProperties
from states import FSMContext, default_state, User_state
from aiogram.types import CallbackQuery, ReplyKeyboardRemove, InputMediaPhoto, Message
from buttons import inline_buttons, buttons, InlineKeyboardBuilder, genres_menu, InlineKeyboardButton
from storage import (budget_low, budget_high, help_text, main_menu_button, profile_info, sorry_reg_user,
                     menu_search_desc, search_menu, search_name_desc, congrat_film_name_desc, genres_menu_list,
                     sorry_name_film, search_process_desc, genres_dict, genres_not_in_lst, sorry_genres_film,
                     rating_menu_desc, rate_menu, rate_dict, budget_menu_desc, rate_money_menu, genres_menu_desc,
                     year_menu_desc, year_film_menu, back_search_desc, sorry_server_desc, search_teams, hist_not_desc,
                     if_budget, hist_date_desc, see_movie_desc, random_menu, user_menu_desc, user_menu,
                     search_menu_desc)


# --------------------------------- CONFIGURATION ---------------------------------


user_stack_song = []

user_call_router = Router()

config: Config = load_config()

logger = logging.getLogger(__name__)

KINOPOISK_API_KEY = config.tg_kino.token

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode="HTML"))


# --------------------------------- COMMANDS ---------------------------------


# Поиск фильма с низким бюджетом из команды
@user_call_router.message(F.text == "/low", StateFilter(default_state))
@throttle(2)
async def low_budget_movie(message: Message) -> None:
    """
    Переходит непосредственно к поиску Фильма / Сериала с низким бюджетом через команду

    Parameters
    ----------
    message : Message
        Сообщение-команда, отправленная пользователем

    Returns
    -------
    None
    """
    await pre_want_movie(message=message, category=budget_low, search_now=3, dl_msg=1)


# Поиск фильма с высоким бюджетом из команды
@user_call_router.message(F.text == "/high", StateFilter(default_state))
@throttle(2)
async def high_budget_movie(message: Message) -> None:
    """
    Переходит непосредственно к поиску Фильма / Сериала с высоким бюджетом через команду

    Parameters
    ----------
    message : Message
        Сообщение-команда, отправленная пользователем

    Returns
    -------
    None
    """
    await pre_want_movie(message=message, category=budget_high, search_now=3, dl_msg=1)


# История поиска из команды
@user_call_router.message(F.text == "/history", StateFilter(default_state))
@throttle(2)
async def history(message: Message) -> None:
    """
    Позволяет посмотреть историю поиска пользователя через команду

    Parameters
    ----------
    message : Message
        Сообщение-команда, отправленная пользователем

    Returns
    -------
    None
    """
    await sending_photo(message=message, table_name="names", go_class=1, prev_text=message.text)


# Помощь с командами бота
@user_call_router.message(F.text == "/help", StateFilter(default_state))
@throttle(2)
async def help_user(message: Message) -> None:
    """
    Позволяет выслать пользователю инструкцию по работе с командами бота

    Parameters
    ----------
    message : Message
        Сообщение-команда, отправленная пользователем

    Returns
    -------
    None
    """
    await message.answer(text=help_text, reply_markup=await inline_buttons(buttons_lst=main_menu_button))


# --------------------------------- PROFILE ---------------------------------


# Функция перехода к профилю пользователя
@user_call_router.callback_query(F.data == "👤Профиль", StateFilter(default_state))
@throttle(2)
async def get_user_data(callback: CallbackQuery) -> None:
    """
    Получает информацию о пользователе по его ID

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Raises
    ------
    TypeError
        Ловит исключение, если пользователя нет в базе данных, но имеет доступ к кнопкам

    Returns
    -------
    None
    """
    user_id = callback.message.chat.id

    try:
        person = User.get(User.user_id == user_id)

        await callback.message.edit_text(text=profile_info.format(person.name, person.birthday, person.phone),
                                         reply_markup=await inline_buttons(buttons_lst=main_menu_button))

    except TypeError:
        await callback.message.edit_text(text=sorry_reg_user)


# --------------------------------- NEW ---------------------------------


# Функция просмотра рандомного Фильма или Сериала
@user_call_router.callback_query(F.data == "Рандом 🎲", StateFilter(default_state))
@throttle(2)
async def question_new(callback: CallbackQuery) -> None:
    """
    Переходит непосредственно к выдаче рандомного фильма

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    await pre_want_movie(message=callback.message, search_now=6, msg_id=callback.message.message_id)


# --------------------------------- SEARCH ---------------------------------


# Функция перехода к основному меню выбора критериев поиска
@user_call_router.callback_query(F.data == "🔍 Поиск", StateFilter(default_state))
@throttle(2)
async def movie_search(callback: CallbackQuery) -> None:
    """
    Изменяет предыдущее сообщение и переходит в общее меню критериев поиска

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    await callback.message.edit_text(text=menu_search_desc, reply_markup=await inline_buttons(buttons_lst=search_menu))


# Функция начала процесса поиска Фильма / Сериала по названию
@user_call_router.callback_query(F.data == "🔖 Название", StateFilter(default_state))
@throttle(2)
async def movie_by_name_all(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Изменяет предыдущее сообщение и переходит к запросу от пользователя названия Фильма / Сериала

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    state : FSMContext
        Начальное состояние для процесса получения действия пользователя

    Returns
    -------
    None
    """
    mess = await callback.message.edit_text(text=search_name_desc)

    await state.update_data(mess=mess.message_id)

    await state.set_state(state=User_state.fill_name_film)


# Функция регистрации полученного названия и запроса жанра Фильма / Сериала
@user_call_router.message(StateFilter(User_state.fill_name_film))
async def movie_by_name_go(message: Message, state: FSMContext) -> None:
    """
    По возможности удаляет предыдущее сообщение и от бота и от пользователя; регистрирует название Фильма /
    Сериала и запрашивает у пользователя, переходя к следующему состоянию, жанр

    Parameters
    ----------
    message : Message
        Сущность сообщения, отправленного пользователем

    state : FSMContext
        Начальное состояние для процесса получения действия пользователя

    Raises
    ------
    TelegramBadRequest
        Ловит исключение невозможности удаления сообщения

    Returns
    -------
    None
    """
    user_id = message.chat.id

    data = await state.get_data()
    mess = int(data["mess"])

    try:
        await message.delete()

        await bot.delete_message(chat_id=user_id, message_id=mess)

    except TelegramBadRequest:
        pass

    if isinstance(film_name := message.text, str):
        mess = await message.answer(text=congrat_film_name_desc,
                                    reply_markup=await buttons(buttons_lst=genres_menu_list, width=2))

        await state.update_data(film_name=film_name)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=User_state.fill_genres_film)

    else:
        mess = await message.answer(text=sorry_name_film)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=User_state.fill_name_film)


# Функция регистрации полученного жанра и переход к непосредственному поиску Фильма / Сериала
@user_call_router.message(StateFilter(User_state.fill_genres_film))
@throttle(2)
async def movie_by_name_genre_go(message: Message, state: FSMContext) -> None:
    """
    По возможности удаляет предыдущее сообщение и от бота и от пользователя; регистрирует жанр Фильма /
    Сериала и переходит непосредственно к поиску по параметрам

    Parameters
    ----------
    message : Message
        Сущность сообщения, отправленного пользователем

    state : FSMContext
        Начальное состояние для процесса получения действия пользователя

    Raises
    ------
    TelegramBadRequest
        Ловит исключение невозможности удаления сообщения

    Returns
    -------
    None
    """
    user_id = message.chat.id

    data = await state.get_data()
    mess = int(data["mess"])
    film_name = data["film_name"]

    try:
        await message.delete()

        await bot.delete_message(chat_id=user_id, message_id=mess)

    except TelegramBadRequest:
        pass

    if isinstance(film_genre := message.text, str):
        if film_genre in genres_menu_list:
            await state.clear()

            mess = await message.answer(text=search_process_desc)

            film_genre = genres_dict[film_genre]

            await pre_want_movie(message=message, category=[film_name, film_genre], search_now=5,
                                 msg_id=mess.message_id)

        else:
            mess = await message.answer(text=genres_not_in_lst,
                                        reply_markup=await buttons(buttons_lst=genres_menu_list, width=2))

            await state.update_data(mess=mess.message_id)

            await state.set_state(state=User_state.fill_genres_film)

    else:
        mess = await message.answer(text=sorry_genres_film)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=User_state.fill_genres_film)


# Функция перехода к меню поиска Фильма / Сериала по рейтингу
@user_call_router.callback_query(F.data == "Рейтинг 🆒", StateFilter(default_state))
@throttle(2)
async def movie_by_rating_all(callback: CallbackQuery) -> None:
    """
    Изменяет предыдущее сообщение и переходит в меню поиска Фильма / Сериала по рейтингу

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    await callback.message.edit_text(text=rating_menu_desc,
                                     reply_markup=await inline_buttons(buttons_lst=rate_menu + ["🔙 НАЗАД"]))


# Функция перехода непосредственно к поиску Фильма / Сериала по рейтингу
@user_call_router.callback_query(F.data.in_(rate_dict), StateFilter(default_state))
@throttle(2)
async def movie_by_rating_one(callback: CallbackQuery) -> None:
    """
    Переходит непосредственно к поиску Фильма / Сериала по рейтингу

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    rating_now = rate_dict[callback.data]

    await pre_want_movie(message=callback.message, category=rating_now, search_now=1,
                         msg_id=callback.message.message_id)


# Функция перехода к меню поиска Фильма / Сериала по бюджету
@user_call_router.callback_query(F.data == "💰 Бюджет", StateFilter(default_state))
@throttle(2)
async def movie_search_budget(callback: CallbackQuery) -> None:
    """
    Изменяет предыдущее сообщение и переходит в меню поиска Фильма / Сериала по бюджету

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    await callback.message.edit_text(text=budget_menu_desc,
                                     reply_markup=await inline_buttons(buttons_lst=rate_money_menu + ["🔙 НАЗАД"],
                                                                       buttons_per_row=1))


# Функция перехода непосредственно к поиску Фильма / Сериала с высоким бюджетом
@user_call_router.callback_query(F.data == "⬆️ Высокий бюджет", StateFilter(default_state))
@throttle(2)
async def movie_by_budget_high(callback: CallbackQuery) -> None:
    """
    Переходит непосредственно к поиску Фильма / Сериала с высоким бюджетом

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    await pre_want_movie(message=callback.message, category=budget_high, search_now=3,
                         msg_id=callback.message.message_id)


# Функция перехода непосредственно к поиску Фильма / Сериала с низким бюджетом
@user_call_router.callback_query(F.data == "Низкий бюджет ⬇️", StateFilter(default_state))
@throttle(2)
async def movie_by_budget_low(callback: CallbackQuery) -> None:
    """
    Переходит непосредственно к поиску Фильма / Сериала с низким бюджетом

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    await pre_want_movie(message=callback.message, category=budget_low, search_now=3,
                         msg_id=callback.message.message_id)


# Функция перехода к меню поиска Фильма / Сериала по жанру
@user_call_router.callback_query(F.data == "Жанр 🎭", StateFilter(default_state))
@throttle(2)
async def movie_by_genres_all(callback: CallbackQuery) -> None:
    """
    Изменяет предыдущее сообщение и переходит в меню поиска Фильма / Сериала по жанру

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    await callback.message.edit_text(text=genres_menu_desc, reply_markup=await genres_menu())


# Функция перехода непосредственно к поиску Фильма / Сериала по жанру
@user_call_router.callback_query(F.data.in_(genres_dict), StateFilter(default_state))
@throttle(2)
async def movie_by_genres_one(callback: CallbackQuery) -> None:
    """
    Переходит непосредственно к поиску Фильма / Сериала по жанру

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    genres_now = genres_dict[callback.data]

    await pre_want_movie(message=callback.message, category=genres_now, search_now=2,
                         msg_id=callback.message.message_id)


# Функция перехода к меню поиска Фильма / Сериала по году выпуска
@user_call_router.callback_query(F.data == "🗓️ Год", StateFilter(default_state))
@throttle(2)
async def movie_by_year_all(callback: CallbackQuery) -> None:
    """
    Изменяет предыдущее сообщение и переходит в меню поиска Фильма / Сериала по году выпуска

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    await callback.message.edit_text(text=year_menu_desc,
                                     reply_markup=await inline_buttons(buttons_lst=year_film_menu + ["🔙 НАЗАД"],
                                                                       buttons_per_row=4))


# Функция перехода непосредственно к поиску Фильма / Сериала по году выпуска
@user_call_router.callback_query(F.data.in_(year_film_menu), StateFilter(default_state))
@throttle(2)
async def movie_by_year_one(callback: CallbackQuery) -> None:
    """
    Переходит непосредственно к поиску Фильма / Сериала по году выпуска

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    year_film_date = callback.data

    await pre_want_movie(message=callback.message, category=year_film_date, search_now=4,
                         msg_id=callback.message.message_id)


# Функция возврата к меню выбора критерия поиска Фильма / Сериала
@user_call_router.callback_query(F.data == "🔙 НАЗАД", StateFilter(default_state))
@throttle(2)
async def movie_search(callback: CallbackQuery) -> None:
    """
    Изменяет предыдущее сообщение и возвращает в общее меню критериев поиска

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    await callback.message.edit_text(text=back_search_desc,
                                     reply_markup=await inline_buttons(buttons_lst=search_menu))


# --------------------------------- SEARCH ENGINE ---------------------------------


# Функция, отвечающая за асинхронные запросы к серверу для получения фильмов по параметрам
async def movie(cat: Any = "0", num: int = 0):
    """
    Направляет асинхронный GET-запрос на сервер для получения фильмов по параметрам

    Parameters
    ----------
    cat : Any
        Объект, в который передаются динамические параметры поиска фильмов / сериалов

    num : int
        Число, которое определяет параметры поиска (в какой категории осуществляется поиск)

    Returns
    -------
    response
        Карутина-ответ сервера на запрос
    """
    page_now = random.randint(a=1, b=10)

    if num == 1:
        url = (f"https://api.kinopoisk.dev/v1.4/movie?page={page_now}&limit=25&selectFields=&rating.imdb={cat}"
               f"&selectFields=name&selectFields=description&selectFields=year&selectFields=genres"
               f"&selectFields=ageRating&selectFields=poster&selectFields=rating&notNullFields=name&"
               f"notNullFields=poster.url&notNullFields=genres.name")

    elif num == 2:
        url = (f"https://api.kinopoisk.dev/v1.4/movie?page={page_now}&limit=25&genres.name={cat}"
               f"&selectFields=name&selectFields=description&selectFields=year&selectFields=genres"
               f"&selectFields=ageRating&selectFields=poster&selectFields=rating&notNullFields=name&"
               f"notNullFields=poster.url&notNullFields=genres.name")

    elif num == 3:
        url = (f"https://api.kinopoisk.dev/v1.4/movie?page={page_now}&limit=25&selectFields=name&"
               f"selectFields=description&selectFields=rating&selectFields=year&selectFields=genres&"
               f"selectFields=ageRating&selectFields=poster&notNullFields=name&notNullFields=poster.url&"
               f"notNullFields=genres.name&selectFields=budget&notNullFields=budget.value&"
               f"budget.value={cat}")

    elif num == 4:
        url = (f"https://api.kinopoisk.dev/v1.4/movie?page={page_now}&limit=25&year={cat}"
               f"&selectFields=name&selectFields=description&selectFields=year&selectFields=genres"
               f"&selectFields=ageRating&selectFields=poster&selectFields=rating&notNullFields=name&"
               f"notNullFields=poster.url&notNullFields=genres.name")

    elif num == 5:
        url = (f"https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=1&query={cat[0]}&genres.name={cat[1]}&"
               f"notNullFields=name&notNullFields=poster.url&notNullFields=genres.name&selectFields=name&"
               f"selectFields=description&selectFields=rating&selectFields=year&selectFields=genres&"
               f"selectFields=ageRating&selectFields=poster")

    elif num == 6:
        url = ("https://api.kinopoisk.dev/v1.4/movie/random?notNullFields=name&notNullFields=genres.name&"
               "notNullFields=poster.url")

    else:
        url = (f"https://api.kinopoisk.dev/v1.4/movie?page={page_now}&limit=25&selectFields=name&"
               f"selectFields=description&selectFields=rating&selectFields=year&selectFields=genres&"
               f"selectFields=ageRating&selectFields=poster&notNullFields=name&notNullFields=poster.url&"
               f"notNullFields=genres.name")

    headers = {
        "accept": "application/json",
        "X-API-KEY": KINOPOISK_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers) as response:
            return await response.json()


# Функция вызова поиска и перехода к созданию пагинации
async def pre_want_movie(message: Message, category: Any = "0", search_now: int = 0,
                         dl_msg: int = 0, msg_id: int = 0, go_class: int = 0) -> None:
    """
    Вызывает функцию получения с сервера информации о фильмах и переходит к созданию пагинации

    Parameters
    ----------
    message : Message
        Сообщение, получаемое из кэлбэк-запроса при нажатии пользователем кнопки

    category : Any
        Объект, в который передаются динамические параметры поиска фильмов / сериалов

    search_now : int
        Число, которое определяет параметры поиска (в какой категории осуществляется поиск)

    dl_msg : int
        Число, которое указывает на необходимость удаления предыдущего сообщения, если значение == 0

    msg_id : int
        Число-номер предыдущего сообщения, которое должно быть удалено

    go_class : int
        Номер класса, который должен быть использован при выводе данных

    Raises
    ------
    TelegramBadRequest
        Ловит исключение невозможности удаления сообщения

    Returns
    -------
    None
    """
    result = await movie(cat=category, num=search_now)

    if result.get("statusCode") is not None:
        if dl_msg == 0:
            await message.answer(text=sorry_server_desc,
                                 reply_markup=await inline_buttons(buttons_lst=search_menu))

        else:
            await message.edit_text(text=sorry_server_desc,
                                    reply_markup=await inline_buttons(buttons_lst=search_menu))

    else:
        if dl_msg == 0:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)

            except TelegramBadRequest:
                pass

        else:
            pass

        user_id = message.chat.id
        team_now = search_teams[search_now]

        if team_now == "randoms":
            result_lst = [result]

        else:
            result_lst = result["docs"]

        time_now = datetime.now().replace(microsecond=0)
        result_all = json.dumps(result_lst, ensure_ascii=False)

        user = SearchMovie(user_id=user_id, search_go=result_all, search_team=team_now, search_time=time_now)
        user.save()

        if team_now == "names":
            movie_now = SearchHistory(user_id=user_id, search_go=result_all, search_team=team_now, search_time=time_now)
            movie_now.save()

        await sending_photo(message=message, table_name=team_now, prev_text=message.text, go_class=go_class)


# --------------------------------- HISTORY ---------------------------------


# Функция просмотра истории поиска Кино и Сериалов
@user_call_router.callback_query(F.data == "История 🗄️", StateFilter(default_state))
@throttle(2)
async def question_history(callback: CallbackQuery) -> None:
    """
    Позволяет посмотреть историю поиска пользователя

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

    await sending_photo(message=callback.message, table_name="names", prev_text=callback.message.text, go_class=1)


# --------------------------------- PAGINATION ---------------------------------


# Функция создания пагинации и отправки фотографий
@throttle(2)
async def sending_photo(message: Message, table_name: str, go_class: int, page_now: int = 1,
                        prev_text: str = None) -> None:
    """
    Создает пагинацию и кнопки

    Parameters
    ----------
    message : Message
        Кэлбэк-запрос при нажатии пользователем кнопки

    table_name : str
        Имя таблицы Базы Данных из кэлбэк-запроса

    go_class : int
        Номер класса, который должен быть использован при выводе данных

    page_now : int
        Страница, которую нужно показать пользователю

    prev_text : str
        Описание для фотографии, если оно имеется в Базе данных

    Returns
    -------
    None
    """
    user_id = message.chat.id

    buttons_photo = InlineKeyboardBuilder()

    now_list_film, how_many, time_search = await __get_total_pages(table_name=table_name, user_id=user_id,
                                                                   go_class=go_class)

    if how_many == 0:
        await message.answer(text=hist_not_desc, reply_markup=await inline_buttons(buttons_lst=main_menu_button))

    else:
        if how_many > 1:
            btn_1 = InlineKeyboardButton(text="⬅️", callback_data=f"prev_{go_class}_{table_name}_{page_now}")
            btn_2 = InlineKeyboardButton(text=f"{page_now}/{how_many}", callback_data=" ")
            btn_3 = InlineKeyboardButton(text="➡️", callback_data=f"next_{go_class}_{table_name}_{page_now}")
            buttons_photo.row(btn_1, btn_2, btn_3)

            if go_class == 0:
                btn_5 = InlineKeyboardButton(text="Вернуться ↘️", callback_data="Вернуться ↘️")

            else:
                btn_5 = InlineKeyboardButton(text="Выйти ⏏️", callback_data="Выйти ⏏️")

            buttons_photo.row(btn_5)

        else:
            if table_name == "reg":
                buttons_photo = ReplyKeyboardRemove()

            else:
                if go_class == 0:
                    if table_name == "randoms":
                        btn_0 = InlineKeyboardButton(text="Рандом 🎲", callback_data="Рандом 🎲")
                        btn_1 = InlineKeyboardButton(text="Выйти ⏏️", callback_data="Выйти ⏏️")

                    else:
                        btn_0 = None
                        btn_1 = InlineKeyboardButton(text="Вернуться ↘️", callback_data=f"Вернуться ↘️")

                else:
                    btn_0 = None
                    btn_1 = InlineKeyboardButton(text="Выйти ⏏️", callback_data="Выйти ⏏️")

                if btn_0 is not None:
                    buttons_photo.row(btn_0, btn_1)

                else:
                    buttons_photo.row(btn_1)

        if buttons_photo == ReplyKeyboardRemove():
            keyboard = buttons_photo

        else:
            keyboard = buttons_photo.as_markup(resize_keyboard=True, one_time_keyboard=True)

        now_see_film = now_list_film[page_now - 1]

        genres_now = ''

        for j in range(len(now_see_film["genres"])):
            genres_now = genres_now + now_see_film["genres"][j]["name"] + "; "

        film_name = now_see_film["name"]
        film_year = "Нет" if now_see_film["year"] is None else now_see_film["year"]
        film_desc = "Нет" if now_see_film["description"] is None else now_see_film["description"][:100] + "..."
        film_rating = now_see_film["rating"]["imdb"]
        film_age = "Не известно" if now_see_film["ageRating"] is None else now_see_film["ageRating"] + " +"
        poster = now_see_film["poster"]["previewUrl"]

        if table_name == "money":
            dop_desc = if_budget.format(now_see_film["budget"]["value"])

        elif table_name == "names":
            time_lst = time_search.split("_")
            dop_desc = hist_date_desc.format(time_lst[0], time_lst[1])

        else:
            dop_desc = ""

        desc = see_movie_desc.format(film_name, film_year, film_desc, film_rating, film_age, genres_now)
        desc += dop_desc

        if table_name == "reg":
            await bot.send_photo(chat_id=message.chat.id, photo=poster, caption=desc, protect_content=False,
                                 reply_markup=keyboard)

        else:
            if prev_text:
                await bot.send_photo(chat_id=message.chat.id, photo=poster, caption=desc, disable_notification=True,
                                     protect_content=False, reply_markup=keyboard)

            else:
                if table_name == "randoms":
                    try:
                        await bot.send_photo(chat_id=message.chat.id, photo=poster, caption=desc,
                                             disable_notification=True, protect_content=False,
                                             reply_markup=keyboard)

                    except TelegramBadRequest:
                        await message.answer(text=sorry_server_desc,
                                             reply_markup=await inline_buttons(buttons_lst=random_menu))

                else:
                    await bot.edit_message_media(chat_id=message.chat.id, message_id=message.message_id,
                                                 media=InputMediaPhoto(media=poster, caption=desc),
                                                 reply_markup=keyboard)


# Функция получения списка последнего поиска
async def __get_total_pages(table_name: str, user_id: int, go_class: int) -> tuple[List, int, str]:
    """
    Получает список, содержащий словари с данными фильмов

    Parameters
    ----------
    table_name : str
        Имя таблицы, из которой нужно достать список с фильмами

    user_id : int
        ID пользователя для извлечения поискового запроса с фильмами из БД

    go_class : int
        Номер класса, который должен быть использован при выводе данных

    Returns
    -------
    now_list_film : List
        Список с результатами последнего поиска фильмов

    how_many_film : int
        Количество фильмов извлеченных из запроса
    """
    if go_class == 0:
        conn = SearchMovie.select().where((SearchMovie.search_team == table_name) & (SearchMovie.user_id == user_id))

    else:
        conn = SearchHistory.select().where((SearchHistory.search_team == table_name) &
                                            (SearchHistory.user_id == user_id))

    new_conn = conn.dicts()
    how_many = len(list(new_conn))

    if how_many == 0:
        now_list_film = ""
        how_many_film = how_many
        time_search = ""

    else:
        now_see_result = new_conn[how_many - 1]
        now_list_film = json.loads(now_see_result["search_go"])
        time_search = now_see_result["search_time"].strftime("%d-%m-%Y_%H:%M:%S")
        how_many_film = len(now_list_film)

    return now_list_film, how_many_film, time_search


# Функция смены страницы пагинации влево
@user_call_router.callback_query(F.data.startswith("prev_"), StateFilter(default_state))
@throttle(2)
async def prev_go(callback: CallbackQuery) -> None:
    """
    Позволяет перелестнуть страницу пагинации назад

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    user_id = callback.message.chat.id

    page_now = int(callback.data.split("_")[-1]) - 1
    table_name = callback.data.split("_")[-2]
    go_class = int(callback.data.split("_")[-3])

    if page_now < 1:
        _, page_now, _ = await __get_total_pages(table_name=table_name, user_id=user_id, go_class=go_class)

    await sending_photo(message=callback.message, table_name=table_name, go_class=go_class, page_now=page_now)


# Функция смены страницы пагинации вправо
@user_call_router.callback_query(F.data.startswith("next_"), StateFilter(default_state))
@throttle(2)
async def go_next(callback: CallbackQuery) -> None:
    """
    Позволяет перелестнуть страницу пагинации вперёд

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    user_id = callback.message.chat.id

    page_now = int(callback.data.split("_")[-1]) + 1
    table_name = callback.data.split("_")[-2]
    go_class = int(callback.data.split("_")[-3])
    _, total_page, _ = await __get_total_pages(table_name=table_name, user_id=user_id, go_class=go_class)

    if page_now > total_page:
        page_now = 1

    await sending_photo(message=callback.message, table_name=table_name, go_class=go_class, page_now=page_now)


# --------------------------------- OTHER ---------------------------------


# Функция перехода в главное меню
@user_call_router.callback_query(F.data == "Главное меню", IsUser(), StateFilter(default_state))
@throttle(2)
async def go_main_menu(callback: CallbackQuery) -> None:
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
    await callback.message.edit_text(text=user_menu_desc, reply_markup=await inline_buttons(buttons_lst=user_menu))


# Функция возврата к критериям поиска из пагинации
@user_call_router.callback_query(F.data == "Вернуться ↘️", IsUser(), StateFilter(default_state))
@throttle(2)
async def comeback_menu(callback: CallbackQuery) -> None:
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


# Функция возврата в главное меню из пагинации
@user_call_router.callback_query(F.data == "Выйти ⏏️", IsUser(), StateFilter(default_state))
@throttle(2)
async def comeback_menu_now(callback: CallbackQuery) -> None:
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

    await callback.message.answer(text=user_menu_desc, disable_notification=True,
                                  reply_markup=await inline_buttons(buttons_lst=user_menu))
