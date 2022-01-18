import pathlib

from peewee import (BigIntegerField, BooleanField, CharField, ForeignKeyField,
                    Model, SmallIntegerField, SqliteDatabase)
from playhouse.sqliteq import SqliteQueueDatabase

from config import DATABASE
from loguru import logger

database = SqliteDatabase(DATABASE,pragmas={
    'journal_mode': 'wal',
    'cache_size': -1 * 64000,  # 64MB
    'foreign_keys': 1,
    'ignore_check_constraints': 0,
    'synchronous': 0})
# database = SqliteQueueDatabase(DATABASE, autostart=False, queue_max_size=64, results_timeout=5)

class BaseModel(Model):
    class Meta:
        database = database


class PlayerName(BaseModel):
    discord_id = BigIntegerField(primary_key=True, unique=True)
    name = CharField()

    @staticmethod
    def exisit(discord_id):
        player = PlayerName.get_or_none(PlayerName.discord_id == discord_id)
        if player:
            return True
        else:
            return False


class Staff(BaseModel):
    discord_id = BigIntegerField(primary_key=True, unique=True)
    is_admin = BooleanField(default=False)


class Player(BaseModel):
    discord_id = ForeignKeyField(PlayerName, field="discord_id")
    draw_count = SmallIntegerField(default=0)
    card_1 = SmallIntegerField(default=0)
    card_2 = SmallIntegerField(default=0)
    card_3 = SmallIntegerField(default=0)
    card_4 = SmallIntegerField(default=0)
    card_5 = SmallIntegerField(default=0)
    card_6 = SmallIntegerField(default=0)
    card_7 = SmallIntegerField(default=0)
    card_8 = SmallIntegerField(default=0)


    def change_card(self, card_name, count):
        match card_name:
            case "与":
                self.card_1 += count
            case "D":
                self.card_2 += count
            case "K":
                self.card_3 += count
            case "共":
                self.card_4 += count
            case "同":
                self.card_5 += count
            case "迎":
                self.card_6 += count
            case "虎":
                self.card_7 += count
            case "年" :
                self.card_8 += count
        self.save()

    def get_card_count(self, card_name):
        cards = {
            "与": self.card_1,
            "D": self.card_2,
            "K": self.card_3,
            "共": self.card_4,
            "同": self.card_5,
            "迎": self.card_6,
            "虎": self.card_7,
            "年": self.card_8,
        }
        return cards[card_name]

CARD_MAPPING = {
    "与": "card_1",
    "D": "card_2",
    "K": "card_3",
    "共": "card_4",
    "同": "card_5",
    "迎": "card_6",
    "虎": "card_7",
    "年": "card_8",
}


def load_init_data():
    staff_list = [
        330972159411224577,  # Omega
        616502749579837445,  # pinky
        912103315800735764,  # luna
        433004236175835138,  # 喵子兮
        708571256508645409,  # 卡文
    ]
    for i in staff_list:
        Staff.create(discord_id=i)

def init_db():
    if not database.get_tables():
        logger.info("创建数据库")
        # database.start()
        database.create_tables([Player, PlayerName, Staff])
        # database.stop()
        logger.info(database.get_tables())
        # database.start()
        load_init_data()
    else:
        database.connect(reuse_if_open=True)
