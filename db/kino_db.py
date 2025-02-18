import logging
from peewee import SqliteDatabase, Model, IntegerField, CharField, DateField, DateTimeField


logger = logging.getLogger(__name__)

db = SqliteDatabase("./db/kino.sqlite")


class User(Model):
    id = IntegerField(primary_key=True)
    user_id = IntegerField()
    name = CharField()
    birthday = DateField()
    phone = CharField()
    date_reg = DateTimeField()

    class Meta:
        database = db


class SearchMovie(Model):
    id = IntegerField(primary_key=True)
    user_id = IntegerField()
    search_go = CharField()
    search_team = CharField()
    search_time = DateTimeField()

    class Meta:
        database = db


class SearchHistory(Model):
    id = IntegerField(primary_key=True)
    user_id = IntegerField()

    search_go = CharField()
    search_team = CharField()

    search_time = DateTimeField()

    class Meta:
        database = db


async def init_db():
    with db:
        db.create_tables([User, SearchMovie, SearchHistory])
