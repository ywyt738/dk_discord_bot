from db import PlayerName, Staff
from discord.ext import commands
from exception import IsNotPlayer, IsNotStaff, IsPlayer


def is_player():
    """已加入玩家校验"""

    async def predicate(ctx):
        if not PlayerName.exisit(ctx.author.id):
            raise IsNotPlayer("你还没有加入活动。")
        return True

    return commands.check(predicate)


def is_not_player():
    """新玩家校验"""

    async def predicate(ctx):
        if PlayerName.exisit(ctx.author.id):
            raise IsPlayer("你已经加入活动。")
        return True

    return commands.check(predicate)


def is_staff():
    async def predicate(ctx):
        staff = Staff.get_or_none(Staff.discord_id == ctx.author.id)
        if not staff:
            raise IsNotStaff("你不是工作人员。")
        return True

    return commands.check(predicate)