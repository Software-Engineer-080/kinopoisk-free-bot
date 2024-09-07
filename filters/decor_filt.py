from time import time
from aiogram import Bot
from typing import Callable
from functools import wraps
from setting import load_config, Config
from aiogram.client.default import DefaultBotProperties


last_call_by_user = {}

config: Config = load_config()

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode='HTML'))


def throttle(seconds: int) -> Callable:
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = None

            callback_query_id = None

            if len(args) > 0:
                if hasattr(args[0], 'from_user'):
                    user_id = args[0].from_user.id

                if hasattr(args[0], 'id'):
                    callback_query_id = args[0].id

                elif hasattr(args[0], 'message'):
                    user_id = args[0].message.from_user.id

            if user_id is None:
                return await func(*args, **kwargs)

            now = time()

            if user_id not in last_call_by_user:
                last_call_by_user[user_id] = {}

            last_call = last_call_by_user[user_id].get(func.__name__, 0)

            if now - last_call < seconds:
                try:
                    if callback_query_id:
                        await bot.answer_callback_query(callback_query_id=callback_query_id,
                                                        text='Подождите 2 секунды❗️')

                    return

                except Exception as e:
                    print(f"Error answering callback query: {e}")

                    return

            last_call_by_user[user_id][func.__name__] = now

            return await func(*args, **kwargs)

        return wrapper

    return decorator
