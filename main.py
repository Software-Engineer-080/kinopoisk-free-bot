import os
import asyncio
import logging
from db import init_db
from datetime import datetime
from buttons import set_main_menu
from handlers import start_router
from aiogram import Bot, Dispatcher
from setting import Config, load_config
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from callbacks import user_call_router, owner_call_router


config: Config = load_config()

logger = logging.getLogger(__name__)

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode="HTML"))


# Основная функция
async def main() -> None:
    """
    Запускает логирование в файл, устанавливает меню команд бота,
    запускает асинхронный поток выполнения, инициализирует роутеры

    Parameters
    ----------
    Не принимает никаких параметров

    Returns
    -------
    None
    """
    log_dir = "loggers"

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        filename=f"{log_dir}/logging-{datetime.now()}.log",
        filemode="a+",
        level=logging.DEBUG,
        format="#{levelname:8} [{asctime}] {filename:20}: {lineno:6} - {name:18} - {funcName:30} - {message}",
        style="{"
    )

    logger.info("Starting bot")

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
