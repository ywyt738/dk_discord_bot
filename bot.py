"""discord bot"""
import json
import pathlib
import random
from collections import Counter

import discord
from discord.ext import commands
from loguru import logger
from playhouse.shortcuts import model_to_dict

from config import BOT_TOKEN, POOL_JSON, PROXY
from db import CARD_MAPPING, Player, PlayerName, Staff, init_db
from exception import CardNotExist, PlayerNotExist
from utils.checks import is_not_player, is_player, is_staff

PRIZE = {
    "蓝色袜子": 300,
    "绿色袜子": 200,
    "黄色袜子": 100,
    "紫色袜子": 50,
    "红色袜子": 10,
}
if pathlib.Path(POOL_JSON).exists():
    with open(POOL_JSON, "r", encoding="utf-8") as f:
        POOL: list = json.load(f)
else:
    POOL = list()
    for _prize, prize_count in PRIZE.items():
        POOL = POOL + [_prize] * prize_count
    with open(POOL_JSON, "w", encoding="utf-8") as f:
        json.dump(POOL, f)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents, proxy=PROXY)

HELP_STRING = """命令（括号内是快捷命令）:
$圣诞 加入(join/j)\t参加活动
$圣诞 抽袜子(raffle/r)\t抽一次帖
$圣诞 我的信息(info)\t查看现有获取袜子的情况以及剩余抽袜子次数"""


def draw(init=False):
    """随机抽取一次"""
    global POOL
    if init:
        init_pool = list(
            filter(
                lambda x: x not in PRIZE,
                POOL,
            )
        )
        result = random.choice(init_pool)
    else:
        result = random.choice(POOL)
    POOL.remove(result)
    with open(POOL_JSON, "w", encoding="utf-8") as f:
        json.dump(POOL, f)
    return result


def player_info(discord_id):
    """显示玩家信息"""
    _player_info = model_to_dict(Player.get(Player.discord_id == discord_id))
    card_info = ""
    for card_name, card_sys_name in CARD_MAPPING.items():
        if c := _player_info[card_sys_name]:
            card_info += f"【{card_name}】:{c}  "
    return f"""{_player_info['discord_id']['name']}玩家剩余抽袜子次数: {_player_info['draw_count']}\n已经获得: {card_info}"""


def send_card(owner: int, to: int, card: str, count: int = 1):
    if not PlayerName.exisit(to):
        raise PlayerNotExist("你要赠送的玩家还没进入活动。")
    owner = Player.get(Player.discord_id == owner)
    if owner.get_card_count(card) < count:
        raise CardNotExist(f"你的[{card}]帖不足。")
    target = Player.get(Player.discord_id == to)
    owner.change_card(card, count * -1)
    target.change_card(card, count)


@bot.group(name="圣诞")
async def tiger(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.reply("subcommand missed")


# 玩家指令
async def _help(ctx):
    await ctx.reply(HELP_STRING)


@is_not_player()
async def _join(ctx):
    # 获取用户id
    discord_id = ctx.author.id
    name = ctx.author.name
    player_name = PlayerName.create(discord_id=discord_id, name=name)
    # 初始化卡获取
    Player.create(discord_id=player_name, draw_count=1)
    await ctx.reply(player_info(player_name.discord_id))


@is_player()
async def _raffle(ctx):
    player = Player.get(Player.discord_id == ctx.author.id)
    card = draw()
    if player.draw_count <= 0:  # 判断是否还有抽帖次数
        await ctx.reply("你的抽袜子次数已经用完。")
        return
    player.draw_count -= 1  # 抽次数减少一次
    player.change_card(card, 1)
    await ctx.reply(f"抽到1双<{card}>\n{player_info(player.discord_id)}")


@is_player()
async def _info(ctx):
    player = ctx.author.id
    await ctx.reply(player_info(player))


# 管理员指令
@tiger.command(name="管理员")
@is_staff()
async def add_admin(ctx, user: discord.User):
    Staff.create(discord_id=user.id)
    await ctx.reply(f"已经任命{user.name}为管理员")


@tiger.command(name="增加")
@is_staff()
async def add_count(ctx, user: discord.User, count: int):
    player = Player.get(Player.discord_id == user.id)
    player.draw_count += count
    player.save()
    await ctx.reply(f"给{player.discord_id.name}增加{count}次抽袜子次数。")


@tiger.command(name="兑换")
@is_staff
async def exchange(ctx, user: discord.User, prize: str):
    player = Player.get(Player.discord_id == user.id)
    match prize:
        case "绿":
            if player.card_1 >= 2:
                player.card_1 = player.card_1 - 2
                player.card_2 = player.card_1 + 1
                player.save()
            else:
                ctx.reply(f"f{player.discord_id.name}的蓝色袜子不足2双")
        case "黄":
            if player.card_2 >= 4:
                player.card_2 = player.card_1 - 4
                player.card_3 = player.card_1 + 1
                player.save()
            else:
                ctx.reply(f"f{player.discord_id.name}的绿色袜子不足4双")
        case "紫":
            if player.card_3 >= 6:
                player.card_3 = player.card_1 - 6
                player.card_4 = player.card_1 + 1
                player.save()
            else:
                ctx.reply(f"{player.discord_id.name}的黄色袜子不足6双")
    await ctx.reply("兑换成功")


@tiger.command(name="奖池情况")
@is_staff()
async def prize_pool_info(ctx):
    c = Counter(POOL)
    s = " | ".join([f"{i}: {c}" for i, c in c.items()])
    await ctx.author.send(s)


@tiger.command(name="奖池增加")
@is_staff()
async def add_prize(ctx, prize: str, count: int):
    global POOL
    c1 = Counter(POOL)
    orgin = " | ".join([f"{i}: {c}" for i, c in c1.items()])
    if prize not in PRIZE.keys():
        await ctx.reply(f"【{prize}】不是正确的奖品。\n奖品只能是如下几种: {PRIZE.keys()}")
    else:
        POOL = POOL + [prize] * count
        c2 = Counter(POOL)
        with open(POOL_JSON, "w", encoding="utf-8") as f:
            json.dump(POOL, f)
        after = " | ".join([f"{i}: {c}" for i, c in c2.items()])
        await ctx.reply(f"原: {orgin}\n后: {after}")


# 事件处理
@bot.event
async def on_ready():
    """机器人ready"""
    logger.info("Bot have logged in as {0.user}".format(bot))


@bot.event
async def on_command_error(ctx, error):
    """没有参加活动报错处理"""
    match type(error).__name__:
        case "IsNotPlayer" | "CardNotExist" | "PlayerNotExist" | "IsPlayer" | "IsNotStaff":
            await ctx.send(error)
        case _:
            logger.error(error)


bot.add_command(tiger.command(name="帮助")(_help))
bot.add_command(tiger.command(name="h")(_help))

bot.add_command(tiger.command(name="加入")(_join))
bot.add_command(tiger.command(name="join")(_join))
bot.add_command(tiger.command(name="j")(_join))

bot.add_command(tiger.command(name="抽帖")(_raffle))
bot.add_command(tiger.command(name="raffle")(_raffle))
bot.add_command(tiger.command(name="r")(_raffle))

bot.add_command(tiger.command(name="我的信息")(_info))
bot.add_command(tiger.command(name="info")(_info))


init_db()
bot.run(BOT_TOKEN)
