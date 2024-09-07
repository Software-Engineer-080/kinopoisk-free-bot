import asyncio
import logging
from buttons import set_main_menu
from aiogram import Bot, Dispatcher
from setting import Config, load_config
from handlers import start_router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from callbacks import user_call_router, owner_call_router, init_db


logger = logging.getLogger(__name__)

config: Config = load_config()

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode='HTML'))


async def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format='#{levelname:8} [{asctime}] {filename:14}: {lineno:4} - {name:18} - {funcName} - {message}',
        style='{'
    )

    logger.info('Starting bot')

    dp = Dispatcher(storage=MemoryStorage())

    await set_main_menu(bot)

    dp.include_router(start_router)
    dp.include_router(user_call_router)
    dp.include_router(owner_call_router)

    await bot.delete_webhook(drop_pending_updates=False)

    tasks = [
        init_db(),
        dp.start_polling(bot, polling_timeout=5)
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
