from environs import Env
from dataclasses import dataclass


@dataclass
class TgBot:
    token: str


@dataclass
class KinoBot:
    token: str


@dataclass
class Owner:
    token: int


@dataclass
class Config:
    tg_bot: TgBot
    tg_owner: Owner
    tg_kino: KinoBot


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(tg_bot=TgBot(token=env("BOT_TOKEN")), tg_kino=KinoBot(token=env("KINO_TOKEN")),
                  tg_owner=Owner(token=env("OWNER_ID")))
