import json
import pathlib
import random
from collections import Counter

import discord
from discord.ext import commands
from loguru import logger
from playhouse.shortcuts import model_to_dict

from config import BOT_TOKEN, PROXY, POOL_JSON
from db import CARD_MAPPING, Player, PlayerName, Staff, init_db
from exception import CardNotExist, PlayerNotExist
from utils.checks import is_not_player, is_player, is_staff


PRIZE = {
    "与": 300,
    "共": 300,
    "同": 300,
    "迎": 300,
    "K": 120,
    "年": 120,
    "D": 40,
    "虎": 40,
    "充100返5 充值小福利": 15,
    "5.2rmb 祝福小红包": 20,
    "1.68rmb 祝福小红包": 40,
    "公会大鼎冠名1日": 1,
    "虎年自定义tag一个月": 3,
}
if pathlib.Path(POOL_JSON).exists():
    with open(POOL_JSON, "r") as f:
        POOL: list = json.load(f)
else:
    POOL = list()
    for prize, count in PRIZE.items():
        POOL = POOL + [prize] * count
    with open(POOL_JSON, "w") as f:
        json.dump(POOL, f)

bot = commands.Bot(command_prefix="$", proxy=PROXY)
HELP_STRING = """命令（括号内是快捷命令）:
$虎年 加入(join/j)\t参加活动
$虎年 抽帖(raffle/r)\t抽一次帖
$虎年 我的信息(info)\t查看现有获取帖到情况以及剩余抽帖次数
$虎年 赠送字帖(give)'与' @xxx\t将帖送给玩家xxx（引号为英文单引号）
$虎年 赠送字帖'D' @xxx
$虎年 赠送字帖'K' @xxx
$虎年 赠送字帖'共' @xxx
$虎年 赠送字帖'同' @xxx
$虎年 赠送字帖'迎' @xxx
$虎年 赠送字帖'虎' @xxx
$虎年 赠送字帖'年' @xxx"""


def draw(init=False):
    global POOL
    """随机抽取一帖"""
    if init:
        init_pool = list(
            filter(
                lambda x: x
                not in (
                    "D",
                    "虎",
                    "充100返5 充值小福利",
                    "5.2rmb 祝福小红包",
                    "1.68rmb 祝福小红包",
                    "公会大鼎冠名1日",
                    "虎年自定义tag一个月",
                ),
                POOL,
            )
        )
        result = random.choice(init_pool)
    else:
        result = random.choice(POOL)
    POOL.remove(result)
    with open(POOL_JSON, "w") as f:
        json.dump(POOL, f)
    return result


def player_info(discord_id):
    """显示玩家信息"""
    player_info = model_to_dict(Player.get(Player.discord_id == discord_id))
    card_info = ""
    for card_name, card_sys_name in CARD_MAPPING.items():
        if c := player_info[card_sys_name]:
            card_info += f"【{card_name}】:{c}  "
    return f"""{player_info['discord_id']['name']}玩家剩余抽帖次数：{player_info['draw_count']}\n已经获得：{card_info}"""


def send_card(owner: int, to: int, card: str, count: int = 1):
    if not PlayerName.exisit(to):
        raise PlayerNotExist("你要赠送的玩家还没进入活动。")
    owner = Player.get(Player.discord_id == owner)
    if owner.get_card_count(card) < count:
        raise CardNotExist(f"你的[{card}]帖不足。")
    target = Player.get(Player.discord_id == to)
    owner.change_card(card, count * -1)
    target.change_card(card, count)


@bot.group(name="虎年")
async def tiger(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.reply("subcommand missed")


# 玩家指令
# @tiger.command(name="帮助")
async def _help(ctx):
    await ctx.reply(HELP_STRING)


# @tiger.command(name="加入")
@is_not_player()
async def _join(ctx):
    # 获取用户id
    discord_id = ctx.author.id
    name = ctx.author.name
    player_name = PlayerName.create(discord_id=discord_id, name=name)
    # 初始化卡获取
    init_card = draw(init=True)
    player = Player.create(discord_id=player_name)
    player.change_card(init_card, 1)
    await ctx.reply(player_info(player_name.discord_id))


# @tiger.command(name="抽帖")
@is_player()
async def _raffle(ctx):
    logger.info("Command get")
    player = Player.get(Player.discord_id == ctx.author.id)
    card = draw()
    if player.draw_count <= 0:  # 判断是否还有抽帖次数
        await ctx.reply("你的抽帖次数已经用完。")
        return
    player.draw_count -= 1  # 抽次数减少一次
    player.change_card(card, 1)
    await ctx.reply(f"抽到1张'{card}'\n{player_info(player.discord_id)}")


# @tiger.command(name="我的信息")
@is_player()
async def _info(ctx):
    player = ctx.author.id
    await ctx.reply(player_info(player))


# @tiger.command(name="赠送字帖'与'")
@is_player()
async def _send_1(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "与")
    await ctx.reply(f"赠送字帖'与'给{user.name}")


# @tiger.command(name="赠送字帖'D'")
@is_player()
async def _send_2(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "D")
    await ctx.reply(f"赠送字帖'D'给{user.name}")


# @tiger.command(name="赠送字帖'K'")
@is_player()
async def _send_3(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "K")
    await ctx.reply(f"赠送字帖'K'给{user.name}")


# @tiger.command(name="赠送字帖'共'")
@is_player()
async def _send_4(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "共")
    await ctx.reply(f"赠送字帖'共'给{user.name}")


# @tiger.command(name="赠送字帖'同'")
@is_player()
async def _send_5(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "同")
    await ctx.reply(f"赠送字帖'同'给{user.name}")


# @tiger.command(name="赠送字帖'迎'")
@is_player()
async def _send_6(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "迎")
    await ctx.reply(f"赠送字帖'迎'给{user.name}")


# @tiger.command(name="赠送字帖'虎'")
@is_player()
async def _send_7(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "虎")
    await ctx.reply(f"赠送字帖'虎'给{user.name}")


# @tiger.command(name="赠送字帖'年'")
@is_player()
async def _send_8(ctx, user: discord.User):
    send_card(ctx.author.id, user.id, "年")
    await ctx.reply(f"赠送字帖'年'给{user.name}")


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
    await ctx.reply(f"给{player.discord_id.name}增加{count}次抽帖次数。")


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
        with open(POOL_JSON, 'w') as f:
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
    # 没有参加活动报错处理
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

bot.add_command(tiger.command(name="赠送字帖'与'")(_send_1))
bot.add_command(tiger.command(name="赠送字帖'D'")(_send_2))
bot.add_command(tiger.command(name="赠送字帖'K'")(_send_3))
bot.add_command(tiger.command(name="赠送字帖'共'")(_send_4))
bot.add_command(tiger.command(name="赠送字帖'同'")(_send_5))
bot.add_command(tiger.command(name="赠送字帖'迎'")(_send_6))
bot.add_command(tiger.command(name="赠送字帖'虎'")(_send_7))
bot.add_command(tiger.command(name="赠送字帖'年'")(_send_8))
bot.add_command(tiger.command(name="give'与'")(_send_1))
bot.add_command(tiger.command(name="give'D'")(_send_2))
bot.add_command(tiger.command(name="give'K'")(_send_3))
bot.add_command(tiger.command(name="give'共'")(_send_4))
bot.add_command(tiger.command(name="give'同'")(_send_5))
bot.add_command(tiger.command(name="give'迎'")(_send_6))
bot.add_command(tiger.command(name="give'虎'")(_send_7))
bot.add_command(tiger.command(name="give'年'")(_send_8))


init_db()
bot.run(BOT_TOKEN)
