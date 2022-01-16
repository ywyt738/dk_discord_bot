import os
import random

import discord
from discord.ext import commands
from loguru import logger
from playhouse.shortcuts import model_to_dict

from db import CARD_MAPPING, Player, PlayerName, init_db

"""
如何获得抽贴：
1. 每个在dk的人都可免费获得一个字帖（初始），可随机抽一个，然后一起进入活动
指令：/虎年 加入
指令：/虎年 抽帖

3. 抽到字帖可赠送给别人
指令：/虎年 赠送字帖'与'to：@

活动指令：
使用 /虎年 加入    加入dk新年的狂欢
使用 /虎年 帮助   查看所有的指令
使用 /虎年 抽帖   可随机获得一个字帖
使用 /虎年 我的信息 可查看我所拥有的剩余抽帖数量和拥有的所有字帖
使用 /虎年 赠送字帖'与' @xxx
使用 /虎年 赠送字帖'D'  @xxx
使用 /虎年 赠送字帖'K'  @xxx
使用 /虎年 赠送字帖'共' @xxx
使用 /虎年 赠送字帖'同' @xxx
使用 /虎年 赠送字帖'迎' @xxx
使用 /虎年 赠送字帖'虎' @xxx
使用 /虎年 赠送字帖'年' @xxx

客服管理专用：
使用 /虎年 增加 @xxx 1
"""

PROXY = os.environ.get("HTTP_PROXY", None)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = commands.Bot(command_prefix="$", proxy=PROXY)


INIT_POOL = "与共同迎" * 375 + "K年" * 100
POOL = "与共同迎" * 375 + "K年" * 100 + "D虎" * 20


class IsNotPlayer(commands.CheckFailure):
    pass


class IsPlayer(commands.CheckFailure):
    pass


class CardNotExisit(commands.CommandError):
    pass


class PlayerNotExisit(commands.CommandError):
    pass


def draw(pool: str):
    """随机抽取一帖"""
    result = random.choice(pool)
    return result


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


def player_info(discord_id):
    """显示玩家信息"""
    player_info = model_to_dict(Player.get(Player.discord_id == discord_id))
    card_info = ""
    for card_name, card_sys_name in CARD_MAPPING.items():
        if c := player_info[card_sys_name]:
            card_info += f"{card_name}:{c} "

    return f"""{player_info['discord_id']['name']}玩家剩余抽帖次数：{player_info['draw_count']}\n已经获得帖：{card_info}"""


@bot.group(name="虎年")
async def tiger(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.reply("subcommand missed")


# 玩家指令
@tiger.command(name="帮助")
async def help(ctx):
    logger("command help")
    await ctx.reply("帮助")


@tiger.command(name="加入")
@is_not_player()
async def join(ctx):
    # 获取用户id
    discord_id = ctx.author.id
    name = ctx.author.name
    player_name = PlayerName.create(discord_id=discord_id, name=name)
    # 初始化卡获取
    init_card = draw(INIT_POOL)
    player = Player.create(discord_id=player_name)
    player.change_card(init_card, 1)
    await ctx.reply(player_info(player_name.discord_id))


@tiger.command(name="抽帖")
@is_player()
async def get(ctx):
    logger.info("Command get")
    player = Player.get(Player.discord_id == ctx.author.id)
    card = draw(POOL)
    if player.draw_count <= 0:  # 判断是否还有抽帖次数
        await ctx.reply("你的抽帖次数已经用完。")
        return
    player.draw_count -= 1  # 抽次数减少一次
    player.change_card(card, 1)
    await ctx.reply(f"抽到1张'{card}'\n{player_info(player)}")


@tiger.command(name="我的信息")
@is_player()
async def info(ctx):
    player = ctx.author.id
    await ctx.reply(player_info(player))


def send_card(owner: int, to: int, card: str, count: int = 1):
    if not PlayerName.exisit(to):
        raise PlayerNotExisit("你要赠送的玩家还没进入活动。")
    owner = Player.get(Player.discord_id == owner)
    if owner.get_card_count(card) < count:
        raise CardNotExisit(f"你的[{card}]帖不足。")
    target = Player.get(Player.discord_id == to)
    owner.change_card(card, count)
    target.change_card(card, count)


@tiger.command(name="赠送字帖'与'")
@is_player()
async def send_1(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "与")
    await ctx.reply("赠送字帖'与'")


@tiger.command(name="赠送字帖'D'")
@is_player()
async def send_2(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "D")
    await ctx.reply("赠送字帖'D'")


@tiger.command(name="赠送字帖'K'")
@is_player()
async def send_3(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "K")
    await ctx.reply("赠送字帖'K'")


@tiger.command(name="赠送字帖'共'")
@is_player()
async def send_4(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "共")
    await ctx.reply("赠送字帖'共'")


@tiger.command(name="赠送字帖'同'")
@is_player()
async def send_5(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "同")
    await ctx.reply("赠送字帖'同'")


@tiger.command(name="赠送字帖'迎'")
@is_player()
async def send_6(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "迎")
    await ctx.reply("赠送字帖'迎'")


@tiger.command(name="赠送字帖'虎'")
@is_player()
async def send_7(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "虎")
    await ctx.reply("赠送字帖'虎'")


@tiger.command(name="赠送字帖'年'")
@is_player()
async def send_8(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "年")
    await ctx.reply("赠送字帖'年'")


# 管理员指令
@tiger.command(name="增加")
async def add_count(ctx, user: discord.User, count: int):
    player = Player.get(Player.discord_id==user.id)
    player.draw_count += count
    player.save()
    await ctx.reply(f"给{player.discord_id.name}增加{count}次抽帖次数。")


########################
@bot.event
async def on_ready():
    """机器人ready"""
    logger.info("Bot have logged in as {0.user}".format(bot))


@bot.event
async def on_command_error(ctx, error):
    # 没有参加活动报错处理
    match type(error).__name__:
        case "IsNotPlayer"|"CardNotExisit"|"PlayerNotExisit"|"IsPlayer":
            await ctx.send(error)
        case _:
            logger.error(error)
########################

init_db()
bot.run(BOT_TOKEN)
