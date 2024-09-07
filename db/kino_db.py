import peewee
import logging


logger = logging.getLogger(__name__)

db = peewee.SqliteDatabase('kino.sqlite')
