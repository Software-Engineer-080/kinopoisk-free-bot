import peewee
import logging
from db import db
from storage import *
from datetime import datetime
from aiogram import F, Router, Bot
from filters import IsUser, throttle
from setting import Config, load_config
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import InlineKeyboardBuilder
from buttons import inline_buttons, InlineKeyboardButton
from peewee import Model, CharField, DateField, IntegerField, FloatField
from aiogram.types import CallbackQuery, ReplyKeyboardRemove, InputMediaPhoto, Message


# --------------------------------- CONFIGURATION ---------------------------------


user_stack_song = []

user_call_router = Router()

config: Config = load_config()

logger = logging.getLogger(__name__)

KINOPOISK_API_KEY = config.tg_kino.token

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode='HTML'))


class User(Model):
    id = IntegerField(primary_key=True)
    user_id = IntegerField()
    name = CharField()
    birthday = DateField()
    phone = CharField()

    class Meta:
        database = db


class Movie(Model):
    id = IntegerField(primary_key=True)
    title = CharField()
    rating = FloatField()
    budget = IntegerField()

    class Meta:
        database = db


class SearchHistory(Model):
    id = IntegerField(primary_key=True)
    user = peewee.ForeignKeyField(User, backref='search_history')
    search_term = CharField()
    timestamp = DateField(default=datetime.now)

    class Meta:
        database = db


async def init_db():
    with db:
        db.create_tables([User, Movie, SearchHistory])


# --------------------------------- COMMANDS ---------------------------------


# --------------------------------- PROFILE ---------------------------------


@user_call_router.callback_query(F.data == '👤Профиль')
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
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", [callback.message.chat.id])
        user = cursor.fetchone()
        cursor.close()

        await callback.message.edit_text(
            text=f"💁Ваш профиль:\n\n"
                 f"Имя: {user[2]}\n\n"
                 f"Фамилия: {user[3]}\n\n"
                 f"Пол: {user[12]}\n\n"
                 f"📅: {user[4]}\n\n"
                 f"☎️: {user[9]}",
            reply_markup=await inline_buttons(buttons_lst=main_menu_button))

    except TypeError:
        await callback.message.edit_text(text=sorry_reg_user)


# Функция создания пагинации и отправки фотографий
@throttle(2)
async def __sending_photo(message: Message, table_name: str, page_now: int = 1, prev_text: str = None) -> None:
    """
    Создает пагинацию и кнопки для всех видов меню

    Parameters
    ----------
    message : Message
        Кэлбэк-запрос при нажатии пользователем кнопки

    table_name : str
        Имя таблицы из Базы Данных из кэлбэк-запроса

    page_now : int
        Страница, которую нужно показать пользователю

    prev_text : str
        Описание для фотографии, если оно имеется в Базе данных

    Returns
    -------
    None
    """
    table_name = table_name.split("_")[-1]
    desc = ""
    new_photo = ""
    buttons_photo = InlineKeyboardBuilder()

    cursor = db.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM base_{table_name}")
    record_count = cursor.fetchone()
    record_count = record_count[0]
    cursor.close()

    if record_count > 1:
        btn_1 = InlineKeyboardButton(text="⬅️", callback_data=f"prev_{table_name}_{page_now}")
        btn_2 = InlineKeyboardButton(text=f"{page_now}/{record_count}", callback_data=" ")
        btn_3 = InlineKeyboardButton(text="➡️", callback_data=f"next_{table_name}_{page_now}")
        buttons_photo.row(btn_1, btn_2, btn_3)

        btn_4 = InlineKeyboardButton(text="Вернуться ⤴️", callback_data="Вернуться ⤴️")
        buttons_photo.row(btn_4)

    else:
        if table_name == "reg":
            buttons_photo = ReplyKeyboardRemove()

        else:
            btn_1 = InlineKeyboardButton(text="Вернуться ⤴️", callback_data=f"Вернуться ⤴️")
            buttons_photo.row(btn_1)

    if buttons_photo == ReplyKeyboardRemove():
        keyboard = buttons_photo

    else:
        keyboard = buttons_photo.as_markup(resize_keyboard=True, one_time_keyboard=True)

    cursor = db.cursor()
    cursor.execute(f"SELECT url, descript FROM base_{table_name} WHERE id = ?", (page_now,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        new_photo = result[0]
        desc = result[1]

    if new_photo:
        if table_name == 'reg':
            await bot.send_photo(chat_id=message.chat.id, photo=new_photo, caption=desc, protect_content=True,
                                 reply_markup=keyboard)

        else:
            if prev_text:
                await bot.send_photo(chat_id=message.chat.id, photo=new_photo, caption=desc, disable_notification=True,
                                     protect_content=True, reply_markup=keyboard)

            else:
                await bot.edit_message_media(chat_id=message.chat.id, message_id=message.message_id,
                                             media=InputMediaPhoto(media=new_photo, caption=desc),
                                             reply_markup=keyboard)

    else:
        if table_name == 'reg':
            await message.answer(text=desc, reply_markup=ReplyKeyboardRemove())

        else:
            await message.answer(text=sorry_desc_base, disable_notification=True,
                                 reply_markup=await inline_buttons(buttons_lst=main_menu_button))


# Функция получения количества записей в БД
async def __get_total_pages(table_name: str) -> int:
    """
    Получает количество записей в Базе Данных, для указанной таблицы

    Parameters
    ----------
    table_name : str
        Имя таблицы, в которой нужно посчитать количество записей

    Returns
    -------
    total_records : int
        Количество записей в БД, для указанной таблицы
    """
    cursor = db.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    total_records = cursor.fetchone()
    total_records = total_records[0]
    cursor.close()

    return total_records


@user_call_router.callback_query(F.data.startswith('prev_'))
@throttle(2)
async def prev_go(callback: CallbackQuery):
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
    page_now = int(callback.data.split("_")[-1]) - 1
    table_name = callback.data.split("_")[-2]

    if page_now < 1:
        page_now = await __get_total_pages(table_name=f"base_{table_name}")

    await __sending_photo(message=callback.message, table_name=f"base_{table_name}", page_now=page_now)


@user_call_router.callback_query(F.data.startswith('next_'))
@throttle(2)
async def go_next(callback: CallbackQuery):
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
    page_now = int(callback.data.split("_")[-1]) + 1
    table_name = callback.data.split("_")[-2]
    total_page = await __get_total_pages(table_name=f"base_{table_name}")

    if page_now > total_page:
        page_now = 1

    await __sending_photo(message=callback.message, table_name=f"base_{table_name}", page_now=page_now)


# --------------------------------- NEW ---------------------------------


@user_call_router.callback_query(F.data == 'Новинки 🔥', IsUser())
@throttle(2)
async def question_new(callback: CallbackQuery) -> None:
    """
    Позволяет посмотреть новинки заведения

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Raises
    ------
    TelegramBadRequest
        Ловит ошибку невозможности удаления сообщения

    BaseException
        Ловит оставшиеся ошибки

    Returns
    -------
    None
    """
    try:
        await callback.message.delete()

        await __sending_photo(message=callback.message, table_name="base_new", prev_text=callback.message.text)

    except TelegramBadRequest:
        await __sending_photo(message=callback.message, table_name="base_new", prev_text=callback.message.text)

    except BaseException:
        await __sending_photo(message=callback.message, table_name="base_new", prev_text=callback.message.text)


# --------------------------------- OTHER ---------------------------------


@user_call_router.callback_query(F.data == 'Главное меню', IsUser())
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


@user_call_router.callback_query(F.data == 'Вернуться ⤴️', IsUser())
@throttle(2)
async def comeback_menu(callback: CallbackQuery) -> None:
    """
    Позволяет вернуться в главное меню из эвента, акций и новинок

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

        await callback.message.answer(text=user_menu_desc, disable_notification=True,
                                      reply_markup=await inline_buttons(buttons_lst=user_menu))

    except TelegramBadRequest:
        await callback.message.answer(text=user_menu_desc, disable_notification=True,
                                      reply_markup=await inline_buttons(buttons_lst=user_menu))


@user_call_router.callback_query(F.data == ' ', IsUser())
@throttle(2)
async def empty_go(callback: CallbackQuery) -> None:
    """
    Заглушка

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос для дальнейшей обработки

    Returns
    -------
    None
    """
    await callback.answer()
