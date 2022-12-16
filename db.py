from loguru import logger
from peewee import (
    BigIntegerField,
    BooleanField,
    CharField,
    ForeignKeyField,
    Model,
    SmallIntegerField,
    SqliteDatabase,
)
from playhouse.sqliteq import SqliteQueueDatabase

from config import DATABASE

database = SqliteDatabase(
    DATABASE,
    pragmas={
        "journal_mode": "wal",
        "cache_size": -1 * 64000,  # 64MB
        "foreign_keys": 1,
        "ignore_check_constraints": 0,
        "synchronous": 0,
    },
)
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

    def change_card(self, card_name, count):
        match card_name:
            case "蓝色袜子":
                self.card_1 += count
            case "绿色袜子":
                self.card_2 += count
            case "黄色袜子":
                self.card_3 += count
            case "紫色袜子":
                self.card_4 += count
            case "红色袜子":
                self.card_5 += count
        self.save()

    def get_card_count(self, card_name):
        cards = {
            "蓝色袜子": self.card_1,
            "绿色袜子": self.card_2,
            "黄色袜子": self.card_3,
            "紫色袜子": self.card_4,
            "红色袜子": self.card_5,
        }
        return cards[card_name]


CARD_MAPPING = {
    "蓝色袜子": "card_1",
    "绿色袜子": "card_2",
    "黄色袜子": "card_3",
    "紫色袜子": "card_4",
    "红色袜子": "card_5",
}


def load_init_data():
    """增加初始管理员"""
    staff_list = [
        330972159411224577,  # Omega
        616502749579837445,  # pinky
    ]
    for i in staff_list:
        Staff.create(discord_id=i, is_admin=True)


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
