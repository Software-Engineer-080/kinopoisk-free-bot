import logging
from db import db
from storage import *
from buttons import inline_buttons
from aiogram import Router, F, Bot
from filters import IsOwner, throttle
from setting import load_config, Config
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.default import DefaultBotProperties
from states import FSMContext, default_state, Owner_state
from buttons import InlineKeyboardMarkup, InlineKeyboardButton

# --------------------------------- CONFIGURATION ---------------------------------


owner_call_router = Router()

config: Config = load_config()

logger = logging.getLogger(__name__)

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode='HTML'))


# --------------------------------- MENU ---------------------------------


# Функция удаления или добавления фотографий в выбранной категории
@throttle(2)
async def __opera_owner(callback: CallbackQuery, category_value: str) -> None:
    """
    Позволяет удалить или добавить фотографии в выбранной категории

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос при нажатии пользователем кнопки

    category_value : str
        Категория главного меню для удаления или добавления фотографий

    Returns
    -------
    None
    """
    btn1 = InlineKeyboardButton(text="Удалить все", callback_data=f"admDel_{category_value}")

    if (category_value == "reg") or (category_value == "birthday"):
        btn2 = InlineKeyboardButton(text="Главное меню", callback_data=f"Главное меню")

        my_but = [btn1, btn2]

        other_but = []

        admin_question_desc = "УДАЛЯЕМ ВСЕ фотографии в данной категории?\n\n" "или\n\n" "В главное меню?"

    else:
        btn2 = InlineKeyboardButton(text="Добавить ещё", callback_data=f"admAdd_{category_value}")
        btn3 = InlineKeyboardButton(text="Главное меню", callback_data=f"Главное меню")

        my_but = [btn1, btn2]

        other_but = [btn3]

        admin_question_desc = "УДАЛЯЕМ ВСЕ фотографии в данной категории?\n\n" "или\n\n" "ДОБАВЛЯЕМ новые?"

    adm_cat = InlineKeyboardMarkup(inline_keyboard=[my_but, other_but])

    await callback.message.edit_text(text=admin_question_desc, reply_markup=adm_cat)


@owner_call_router.callback_query(F.data.startswith('admDel_'), IsOwner(), StateFilter(default_state))
@throttle(2)
async def adm_del_res(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Позволяет удалить фотографии в выбранной категории

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос при нажатии пользователем кнопки

    state : FSMContext
        Состояние владельца для удаления всех фотографий

    Returns
    -------
    None
    """
    adm_menu = callback.data.split("_")[-1]

    await __all_photo(message=callback.message, category=adm_menu, state=state)


# Функция удаления всех фотографий в выбранной категории
async def __all_photo(message: Message, category: str, state: FSMContext) -> None:
    """
    Позволяет удалить все фотографии в выбранной категории

    Parameters
    ----------
    message : Message
        Значение сообщения из кэлбэк-запроса для дальнейшей работы

    category : str
        Категория, в которой будут удаленый фотографии

    state : FSMContext
        Состояние владельца для удаления всех фотографий

    Raises
    ------
    TelegramBadRequest
        Ловит исключение невозможности удаления сообщения

    Returns
    -------
    None
    """
    try:
        await message.delete()

        # conn = await create_conn()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM base_{category}")
        conn.commit()
        cursor.close()

        if (category == 'reg') or (category == "birthday"):
            mess = await message.answer(text=go_one_photo_desc_reg, disable_notification=True)

            await state.update_data(mess=mess.message_id)

            await state.update_data(current_photo_num=1)

            await state.update_data(total_photos=None)

            await state.update_data(category=category)

            await state.set_state(state=Owner_state.fill_photo_for)

        else:
            mess = await message.answer(text=quest_how_photo)

            await state.update_data(mess=mess.message_id)

            await state.update_data(category=category)

            await state.set_state(state=Owner_state.fill_add_photo)

    except TelegramBadRequest:
        # conn = await create_conn()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM base_{category}")
        conn.commit()
        cursor.close()

        if (category == 'reg') or (category == "birthday"):
            mess = await message.answer(text=go_one_photo_desc_reg, disable_notification=True)

            await state.update_data(mess=mess.message_id)

            await state.update_data(current_photo_num=1)

            await state.update_data(total_photos=None)

            await state.update_data(category=category)

            await state.set_state(state=Owner_state.fill_photo_for)

        else:
            mess = await message.answer(text=quest_how_photo)

            await state.update_data(mess=mess.message_id)

            await state.update_data(category=category)

            await state.set_state(state=Owner_state.fill_add_photo)


@owner_call_router.callback_query(F.data.startswith('admAdd_'), IsOwner(), StateFilter(default_state))
@throttle(2)
async def adm_add_res(callback: CallbackQuery, state: FSMContext):
    """
    Позволяет добавить фотографии в выбранной категории

    Parameters
    ----------
    callback : CallbackQuery
        Кэлбэк-запрос при нажатии пользователем кнопки

    state : FSMContext
        Состояние владельца для добавления фотографий

    Returns
    -------
    None
    """
    adm_menu = callback.data.split("_")[-1]

    await state.update_data(category=adm_menu)

    await __new_photo(message=callback.message, state=state)


# Функция указания количества добавляемых фотографий
async def __new_photo(message: Message, state: FSMContext) -> None:
    """
    Позволяет указать количество фотографий, которое будет загружено в выбранную категорию

    Parameters
    ----------
    message : Message
        Значение сообщения из кэлбэк-запроса для дальнейшей работы

    state : FSMContext
        Состояние владельца для указания количества добавляемых фотографий

    Returns
    -------
    None
    """
    mess = await message.edit_text(text=quest_how_photo)

    await state.update_data(mess=mess.message_id)

    await state.set_state(state=Owner_state.fill_add_photo)


# Функция добавления одной фотографии в категорию
@owner_call_router.message(StateFilter(Owner_state.fill_add_photo))
async def __add_photo(message: Message, state: FSMContext) -> None:
    """
    Позволяет добавить 1 фотографию в выбранную категорию

    Parameters
    ----------
    message : Message
        Значение сообщения из кэлбэк-запроса для дальнейшей работы

    state : FSMContext
        Состояние владельца для добавления одной фотографии

    Raises
    ------
    ValueError
        Ловит исключение, если количество загружаемых фотографий введено не цифрами

    TypeError
        Ловит исключение, если отправлено сообщение типа, отличного от Message

    Returns
    -------
    None
    """
    await message.delete()

    data = await state.get_data()
    mess = int(data["mess"])
    category = data['category']

    await bot.delete_message(chat_id=message.chat.id, message_id=mess)

    try:
        if message.text is not None:
            if message.text.startswith('/0'):
                await state.clear()

                await message.answer(text=not_new_photo_desc, disable_notification=True,
                                     reply_markup=await inline_buttons(buttons_lst=main_menu_button))

                return

            else:
                num = int(message.text)

                if num < 0:
                    mess = await message.answer(text=warn_photo_zero, disable_notification=True)

                    await state.update_data(mess=mess.message_id)

                    await state.set_state(state=Owner_state.fill_add_photo)

                elif num == 0:
                    await state.clear()

                    await message.answer(text=not_new_photo_desc, disable_notification=True,
                                         reply_markup=await inline_buttons(buttons_lst=main_menu_button))

                    return

                if ((category != 'bar') and (category != 'cocktails') and
                        (category != 'kitchen') and (category != 'desert') and (category != 'roll')):

                    mess = await message.answer(text=go_one_photo_desc_reg, disable_notification=True)

                else:
                    mess = await message.answer(text=go_one_photo_desc, disable_notification=True)

                await state.update_data(mess=mess.message_id)

                await state.update_data(current_photo_num=1)

                await state.update_data(total_photos=num)

                await state.set_state(state=Owner_state.fill_photo_for)

        else:
            mess = await message.answer(text=value_err_num_photo, disable_notification=True)

            await state.update_data(mess=mess.message_id)

            await state.set_state(state=Owner_state.fill_add_photo)

    except ValueError:
        mess = await message.answer(text=value_err_num_photo, disable_notification=True)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=Owner_state.fill_add_photo)

    except TypeError:
        mess = await message.answer(text=value_err_num_photo, disable_notification=True)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=Owner_state.fill_add_photo)

    except BaseException:
        mess = await message.answer(text=value_err_num_photo, disable_notification=True)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=Owner_state.fill_add_photo)


# Функция добавления фотографий, если их больше одной
@owner_call_router.message(StateFilter(Owner_state.fill_photo_for))
async def __handle_photo_for(message: Message, state: FSMContext) -> None:
    """
    Позволяет добавить остальные фотографии, если их больше 1

    Parameters
    ----------
    message : Message
        Значение сообщения из кэлбэк-запроса для дальнейшей работы

    state : FSMContext
        Состояние владельца для добавления остальных фотографий

    Returns
    -------
    None
    """
    await message.delete()

    data = await state.get_data()
    category = data['category']
    current_photo_num = int(data['current_photo_num'])

    if (category == "reg") or (category == "birthday"):
        total_photos = 1
    else:
        total_photos = int(data['total_photos'])

    mess = int(data["mess"])

    await bot.delete_message(chat_id=message.chat.id, message_id=mess)

    if message.photo:
        photo = max(message.photo, key=lambda x: x.height)
        file_id = photo.file_id
        desc = message.caption

        if desc is not None:
            await state.update_data(file_id=file_id)

            if ((category != 'bar') and (category != 'cocktails') and
                    (category != 'kitchen') and (category != 'desert') and (category != 'roll')):
                # conn = await create_conn()
                cursors = conn.cursor()
                cursors.execute(f"INSERT INTO base_{category} (url, descript) VALUES (?, ?)", (file_id, desc,))
                # conn.commit()
                cursors.close()

            else:
                # conn = await create_conn()
                cursors = conn.cursor()
                cursors.execute(f"INSERT INTO base_{category} (url) VALUES (?)", (file_id,))
                # conn.commit()
                cursors.close()

            if (category == 'reg') or (category == "birthday"):
                await state.clear()

                # conn = await create_conn()
                cursors = conn.cursor()
                conn.commit()
                cursors.close()

                await message.answer(text=congrat_photo_desc, disable_notification=True,
                                     reply_markup=await inline_buttons(buttons_lst=main_menu_button))

            else:
                current_photo_num += 1

                if current_photo_num <= total_photos:

                    if ((category != 'bar') and (category != 'cocktails') and (category != 'kitchen') and
                            (category != 'desert') and (category != 'roll')):
                        mess = await message.answer(text=f"Отправьте {current_photo_num} фото "
                                                         f"(можно с подписью под ним)\n\n"
                                                         f"‼️Если передумали, то просто отправьте число 0 👇",
                                                    disable_notification=True)

                    else:
                        mess = await message.answer(text=f"Отправьте {current_photo_num} фото\n\n"
                                                         f"‼️Если передумали, то просто отправьте число 0 👇",
                                                    disable_notification=True)

                    await state.update_data(current_photo_num=current_photo_num)

                    await state.update_data(mess=mess.message_id)

                    await state.set_state(state=Owner_state.fill_photo_for)

                else:
                    await state.clear()

                    # conn = await create_conn()
                    cursors = conn.cursor()
                    conn.commit()
                    cursors.close()

                    await message.answer(text=congrat_photo_desc, disable_notification=True,
                                         reply_markup=await inline_buttons(buttons_lst=main_menu_button))

        else:
            await state.update_data(file_id=file_id)

            # conn = await create_conn()
            cursors = conn.cursor()
            cursors.execute(f"INSERT INTO base_{category} (url) VALUES (?)", (file_id,))
            # conn.commit()
            cursors.close()

            if (category == "new") or (category == 'reg') or (category == "birthday") or (category == "sale"):
                mess = await message.answer(text=f"Введите описание для фотографии {current_photo_num} 👇",
                                            disable_notification=True)

                await state.update_data(mess=mess.message_id)

                await state.set_state(state=Owner_state.fill_photo_desc)

            else:
                current_photo_num += 1

                if current_photo_num <= total_photos:

                    if category != 'event':
                        mess = await message.answer(text=f"Отправьте {current_photo_num} фото\n\n"
                                                         f"‼️Если передумали, то просто отправьте число 0 👇",
                                                    disable_notification=True)
                    else:
                        mess = await message.answer(text=f"Отправьте {current_photo_num} фото "
                                                         f"(можно с подписью под ним)\n\n"
                                                         f"‼️Если передумали, то просто отправьте число 0 👇",
                                                    disable_notification=True)

                    await state.update_data(current_photo_num=current_photo_num)

                    await state.update_data(mess=mess.message_id)

                    await state.set_state(state=Owner_state.fill_photo_for)

                else:
                    await state.clear()

                    # conn = await create_conn()
                    cursors = conn.cursor()
                    conn.commit()
                    cursors.close()

                    await message.answer(text=congrat_photo_desc, disable_notification=True,
                                         reply_markup=await inline_buttons(buttons_lst=main_menu_button))

    elif message.text.startswith('/0') or message.text.startswith('0'):
        await state.clear()

        if current_photo_num > 1:
            # conn = await create_conn()
            cursor = conn.cursor()

            subquery = f"SELECT id FROM base_{category} ORDER BY id DESC LIMIT {current_photo_num - 1}"

            cursor.execute(f"DELETE FROM base_{category} WHERE id IN ({subquery})")
            conn.commit()
            cursor.close()

        await message.answer(text=not_new_photo_desc, disable_notification=True,
                             reply_markup=await inline_buttons(buttons_lst=main_menu_button))

        return

    else:
        mess = await message.answer(text=pleas_send_pick_desc, disable_notification=True)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=Owner_state.fill_photo_for)


# Функция добавления описания к каждой фотографии
@owner_call_router.message(StateFilter(Owner_state.fill_photo_desc))
async def __handle_photo_description(message: Message, state: FSMContext) -> None:
    """
    Позволяет добавить описание к фотографиям в выбранной категории

    Parameters
    ----------
    message : Message
        Значение сообщения из кэлбэк-запроса для дальнейшей работы

    state : FSMContext
        Состояние владельца для добавления описания к фотографиям

    Returns
    -------
    None
    """
    await message.delete()

    data = await state.get_data()
    category = data['category']
    current_photo_num = int(data['current_photo_num'])

    if (category == "reg") or (category == "birthday"):
        total_photos = 1

    else:
        total_photos = int(data['total_photos'])

    file_id = data['file_id']
    mess = int(data["mess"])

    await bot.delete_message(chat_id=message.chat.id, message_id=mess)

    if message.text is not None:
        desc = message.text

        # conn = await create_conn()
        cursors = conn.cursor()
        cursors.execute(f"UPDATE base_{category} SET descript = ? WHERE url = ?", (desc, file_id,))
        # conn.commit()
        cursors.close()

        current_photo_num += 1

        if (category == 'reg') or (category == "birthday"):
            await state.clear()

            # conn = await create_conn()
            cursors = conn.cursor()
            conn.commit()
            cursors.close()

            await message.answer(text=congrat_photo_desc, disable_notification=True,
                                 reply_markup=await inline_buttons(buttons_lst=main_menu_button))

        elif current_photo_num <= total_photos:
            mess = await message.answer(text=f"Отправьте {current_photo_num} фото (можно с подписью под ним)\n\n"
                                             f"‼️Если передумали, то просто отправьте число 0 👇",
                                        disable_notification=True)

            await state.update_data(current_photo_num=current_photo_num)

            await state.update_data(mess=mess.message_id)

            await state.set_state(state=Owner_state.fill_photo_for)

        else:
            await state.clear()

            # conn = await create_conn()
            cursors = conn.cursor()
            conn.commit()
            cursors.close()

            await message.answer(text=congrat_photo_desc, disable_notification=True,
                                 reply_markup=await inline_buttons(buttons_lst=main_menu_button))

    else:
        mess = await message.answer(text=f"Введите описание для фото 👇", disable_notification=True)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=Owner_state.fill_photo_desc)

# --------------------------------- NEW ---------------------------------


@owner_call_router.callback_query(F.data == 'Новинки 🔥', IsOwner())
@throttle(2)
async def question_new_own(callback: CallbackQuery) -> None:
    """
    Функция по смене фотографии категории Новинки

    Parameters
    ----------
    callback : CallbackQuery
        Значение сообщения из кэлбэк-запроса для дальнейшей работы

    Returns
    -------
    None
    """
    await __opera_owner(callback=callback, category_value="new")


# --------------------------------- REGISTRATION ---------------------------------


@owner_call_router.callback_query(F.data == 'Регистрация', IsOwner())
@throttle(2)
async def question_event_own(callback: CallbackQuery) -> None:
    """
    Функция по смене фотографии и описания рассылки при регистрации

    Parameters
    ----------
    callback : CallbackQuery
        Значение сообщения из кэлбэк-запроса для дальнейшей работы

    Returns
    -------
    None
    """
    await __opera_owner(callback=callback, category_value='reg')


# --------------------------------- BIRTHDAY ---------------------------------


@owner_call_router.callback_query(F.data == '🎉 ДР', IsOwner())
@throttle(2)
async def question_sale_own(callback: CallbackQuery) -> None:
    """
    Функция по смене фотографии и описания рассылки дня рождения

    Parameters
    ----------
    callback : CallbackQuery
        Значение сообщения из кэлбэк-запроса для дальнейшей работы

    Returns
    -------
    None
    """
    await __opera_owner(callback=callback, category_value="birthday")


# --------------------------------- OTHERS ---------------------------------


@owner_call_router.callback_query(F.data == 'Главное меню', IsOwner())
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
