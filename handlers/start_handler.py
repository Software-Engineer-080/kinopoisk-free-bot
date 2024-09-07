import asyncio
import logging
from db import db
from storage import *
from filters import throttle
from datetime import datetime
from aiogram import Router, Bot
from aiogram.types import Message
from callbacks import __sending_photo
from setting import load_config, Config
from buttons import inline_buttons, phone_btn
from aiogram.filters import StateFilter, CommandStart
from aiogram.client.default import DefaultBotProperties
from states import default_state, Start_state, FSMContext

# --------------------------------- CONFIGURATION ---------------------------------


user_stack_in = []

user_stack_out = []

start_router = Router()

config: Config = load_config()

logger = logging.getLogger(__name__)

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode='HTML'))


# --------------------------------- START AND REGISTRATION ---------------------------------


# Хэндлер реакции на стартовую команду
@start_router.message(CommandStart(), StateFilter(default_state))
@throttle(2)
async def start_command(message: Message, state: FSMContext):
    user_id = message.chat.id

    if user_id == owner:
        await message.answer(text=owner_menu_desc, reply_markup=await inline_buttons(buttons_lst=owner_menu))

    else:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", [user_id])
        user = cursor.fetchone()
        cursor.close()

        if user:
            if user[9]:
                user_name = user[2]

                await message.answer(text=start_user_desc.format(user_name),
                                     reply_markup=await inline_buttons(buttons_lst=user_menu))

            else:
                hello = await message.answer(text=start_desc)

                await asyncio.sleep(4)

                mess = await hello.edit_text(text=start_name_reg)

                await state.update_data(mess=mess.message_id)

                await state.set_state(state=Start_state.fill_name)

        else:
            hello = await message.answer(text=start_desc)

            await asyncio.sleep(4)

            mess = await hello.edit_text(text=start_name_reg)

            await state.update_data(mess=mess.message_id)

            await state.set_state(state=Start_state.fill_name)


# Функция регистрации имени пользователя
@start_router.message(StateFilter(Start_state.fill_name))
async def reg_name(message: Message, state: FSMContext) -> None:
    """
    Регистрирует имя пользователя при первом запуске бота

    Parameters
    ----------
    message : Message
        Значение сообщения для дальнейшей работы

    state : FSMContext
        Состояние пользователя для регистрации имени

    Raises
    ------
    AttributeError
        Ловит исключение, когда пользователь оправляет сообщение с типом, отличным от Message

    Returns
    -------
    None
    """
    await message.delete()

    data = await state.get_data()
    mess = int(data["mess"])

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=mess)

        user_id = message.from_user.id
        user_name = message.text.lower()

        num = __verify_name(user_name=user_name)

        if num == 3:
            user_stack_in.append(user_id)

            while user_stack_in:
                user_stack_in.pop(0)

                await state.update_data(name=user_name.capitalize())

            mess = await message.answer(text=start_birthday_reg.format(user_name.capitalize()),
                                        disable_notification=True)

            await state.update_data(mess=mess.message_id)

            await state.set_state(state=Start_state.fill_birthday)

        else:
            error_message = error_name.get(num, "Вы неверно ввели имя!")

            if error_message:
                mess = await message.answer(text=error_enter_name.format(error_message),
                                            disable_notification=True)

                await state.update_data(mess=mess.message_id)

                await state.set_state(state=Start_state.fill_name)

    except AttributeError:
        mess = await message.answer(text=attribute_error_name, disable_notification=True)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=Start_state.fill_name)

    except BaseException:
        mess = await message.answer(text=base_error_name, disable_notification=True)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=Start_state.fill_name)


# Функция регистрации даты рождения пользователя
@start_router.message(StateFilter(Start_state.fill_birthday))
async def reg_birthday(message: Message, state: FSMContext) -> None:
    """
    Регистрирует дату рождения пользователя при первом запуске бота

    Parameters
    ----------
    message : Message
        Значение сообщения для дальнейшей работы

    state : FSMContext
        Состояние пользователя для регистрации даты рождения

    Raises
    ------
    ValueError
        Ловит исключение, если в дату рождения будут написаны недопустимые символы

    AttributeError
        Ловит исключение, когда пользователь оправляет сообщение с типом, отличным от Message

    Returns
    -------
    None
    """
    user_birthday = message.text

    await message.delete()

    data = await state.get_data()
    mess = int(data["mess"])

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=mess)

        num = __verify_birthday(user_birthday=user_birthday)

        if num in errors_birthday:
            desc = errors_birthday[num]

            mess = await message.answer(text=error_dict_birthday.format(desc), disable_notification=True)

            await state.update_data(mess=mess.message_id)

            await state.set_state(state=Start_state.fill_birthday)

        elif num == 5:
            await message.answer(text=error_y_o, disable_notification=True)

            await state.clear()

        elif num == 6:
            mess = await message.answer(text=enter_real_date, disable_notification=True)

            await state.update_data(mess=mess.message_id)

            await state.set_state(state=Start_state.fill_birthday)

        else:
            user_birthday = user_birthday.split(".")
            user_birthday = f"{user_birthday[0].zfill(2)}.{user_birthday[1].zfill(2)}.{user_birthday[2]}"

            await state.update_data(birthday=user_birthday)

            mess = await message.answer(text=final_phone_desc, disable_notification=True,
                                        reply_markup=await phone_btn())

            await state.update_data(mess=mess.message_id)

            await state.set_state(state=Start_state.fill_phone)

    except ValueError:
        mess = await message.answer(text=value_error_birthday, disable_notification=True)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=Start_state.fill_birthday)

    except AttributeError:
        mess = await message.answer(text=attribute_error_birthday, disable_notification=True)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=Start_state.fill_birthday)

    except BaseException:
        mess = await message.answer(text=base_error_birthday, disable_notification=True)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=Start_state.fill_birthday)


# Функция регистрации номера телефона
@start_router.message(StateFilter(Start_state.fill_phone))
async def registration_phone(message: Message, state: FSMContext) -> None:
    """
    Регистрирует номер телефона пользователя при первом запуске бота

    Parameters
    ----------
    message : Message
        Значение сообщения для дальнейшей работы

    state : FSMContext
        Состояние пользователя для регистрации номера телефона

    Raises
    ------
    AttributeError
        Ловит исключение, когда пользователь оправляет сообщение с типом, отличным от Message

    Returns
    -------
    None
    """
    user_id = message.from_user.id

    await message.delete()

    data = await state.get_data()
    mess = int(data["mess"])
    name = data['name']
    birthday = data['birthday']

    keyboard = await phone_btn()

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=mess)

        if message.contact:
            user_reg_phone = message.contact.phone_number

            if user_reg_phone[0] == '+':
                user_reg_phone = (user_reg_phone[:2] + '-' + user_reg_phone[2:5] + '-' + user_reg_phone[5:8] + '-' +
                                  user_reg_phone[8:10] + '-' + user_reg_phone[10:])

            else:
                user_reg_phone = ('+' + user_reg_phone[:1] + '-' + user_reg_phone[1:4] + '-' + user_reg_phone[4:7] + '-'
                                  + user_reg_phone[7:9] + '-' + user_reg_phone[9:])

        else:
            user_reg_phone = message.text

        num = __verify_phone(user_phone=user_reg_phone)

        if num == 4:
            await state.clear()

            user_stack_out.append(user_id)

            while user_stack_out:
                user_stack_out.pop(0)

                # ----------------------------

                print(name, birthday, user_reg_phone)

                # ----------------------------

                throttled_sending_photo = throttle(0.001)(__sending_photo)

                await throttled_sending_photo(message=message, table_name='base_reg')

                await state.clear()

                await asyncio.sleep(5)

                await message.answer(text=user_menu_desc, disable_notification=True,
                                     reply_markup=await inline_buttons(buttons_lst=user_menu))

        else:
            mess = await message.answer(text=errors_phone[num], disable_notification=True, reply_markup=keyboard)

            await state.update_data(mess=mess.message_id)

            await state.set_state(state=Start_state.fill_phone)

    except AttributeError:
        mess = await message.answer(text=attribute_error_phone, disable_notification=True, reply_markup=keyboard)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=Start_state.fill_birthday)

    except BaseException:
        mess = await message.answer(text=base_error_phone, disable_notification=True, reply_markup=keyboard)

        await state.update_data(mess=mess.message_id)

        await state.set_state(state=Start_state.fill_birthday)


# --------------------------------- VERIFICATION REGISTRATION ---------------------------------


# Функция проверки имени пользователя на валидность
def __verify_name(user_name: str) -> int:
    """
    Проверяет имя пользователя на валидность

    Parameters
    ----------
    user_name : str
            Строка, которая должна содержать имя пользователя

    Returns
    -------
    int
        Номер ошибки в словаре ошибок имени
    """
    if len(user_name) < 2:
        return 0

    elif not user_name.isalpha():
        return 1

    elif len(user_name) > 12:
        return 2

    elif not all(char in alphabet for char in user_name):
        return 4

    else:
        return 3


# Функция проверки дня рождения пользователя на валидность
def __verify_birthday(user_birthday: str) -> int:
    """
    Проверяет дату рождения на валидность

    Parameters
    ----------
    user_birthday : str
            Строка, которая должна содержать день рождения пользователя

    Returns
    -------
    int
        Номер ошибки в словаре ошибок даты рождения
    """
    date = user_birthday.split(".")
    now = datetime.now().date().year - 18

    if len(date) != 3 or not all(part.isdigit() for part in date):
        return 1

    day, month, year = map(int, date)

    if day > 31 or month > 12:
        return 3

    if year > now:
        return 5

    elif year < (now - 100):
        return 6

    return 4


# Функция проверки номера телефона на валидность
def __verify_phone(user_phone: str) -> int:
    """
    Проверяет номер телефона на валидность

    Parameters
    ----------
    user_phone : str
            Строка, которая должна содержать номер телефона

    Returns
    -------
    int
        Номер ошибки в словаре ошибок номера телефона
    """
    phone = user_phone.split("-")

    if len(phone) != 5:
        return 1

    else:
        if phone[0] != "+7":
            return 2

        elif (len(phone[1]) != 3) or (not phone[1].isdigit()):
            return 3

        elif (len(phone[2]) != 3) or (not phone[2].isdigit()):
            return 3

        elif (len(phone[3]) != 2) or (not phone[3].isdigit()):
            return 3

        elif (len(phone[4]) != 2) or (not phone[4].isdigit()):
            return 3

        else:
            return 4
