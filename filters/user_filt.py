from aiogram.types import Message
from aiogram.filters import BaseFilter
from setting import load_config, Config


config: Config = load_config()

owner = int(config.tg_owner.token)


class IsUser(BaseFilter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id

        if user_id != owner:
            return True

        else:
            return False
