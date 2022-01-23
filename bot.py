import os
import random

import discord
from discord.ext import commands
from loguru import logger
from playhouse.shortcuts import model_to_dict

from config import BOT_TOKEN, INIT_POOL, POOL, PROXY
from db import CARD_MAPPING, Player, PlayerName, Staff, init_db
from exception import CardNotExist, PlayerNotExist
from utils.checks import is_not_player, is_player, is_staff


bot = commands.Bot(command_prefix="$", proxy=PROXY)


def draw(pool: str):
    """随机抽取一帖"""
    result = random.choice(pool)
    return result


def player_info(discord_id):
    """显示玩家信息"""
    player_info = model_to_dict(Player.get(Player.discord_id == discord_id))
    card_info = ""
    for card_name, card_sys_name in CARD_MAPPING.items():
        if c := player_info[card_sys_name]:
            card_info += f"{card_name}:{c} "
    return f"""{player_info['discord_id']['name']}玩家剩余抽帖次数：{player_info['draw_count']}\n已经获得帖：{card_info}"""


def send_card(owner: int, to: int, card: str, count: int = 1):
    if not PlayerName.Exist(to):
        raise PlayerNotExist("你要赠送的玩家还没进入活动。")
    owner = Player.get(Player.discord_id == owner)
    if owner.get_card_count(card) < count:
        raise CardNotExist(f"你的[{card}]帖不足。")
    target = Player.get(Player.discord_id == to)
    owner.change_card(card, count)
    target.change_card(card, count)


@bot.group(name="虎年")
async def tiger(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.reply("subcommand missed")


# 玩家指令
@tiger.command(name="帮助")
async def help(ctx):
    logger("command help")
    await ctx.reply("""命令:
    $虎年 加入                 参加活动
    $虎年 抽帖                 抽一次帖
    $虎年 我的信息             查看现有获取帖到情况以及剩余抽帖次数
    $虎年 赠送字帖'与' @xxx    将帖送给玩家xxx（引号为英文单引号）
    $虎年 赠送字帖'D' @xxx
    $虎年 赠送字帖'K' @xxx
    $虎年 赠送字帖'共' @xxx
    $虎年 赠送字帖'同' @xxx
    $虎年 赠送字帖'迎' @xxx
    $虎年 赠送字帖'虎' @xxx
    $虎年 赠送字帖'年' @xxx""")


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
    await ctx.reply(f"抽到1张'{card}'\n{player_info(player.discord_id)}")


@tiger.command(name="我的信息")
@is_player()
async def info(ctx):
    player = ctx.author.id
    await ctx.reply(player_info(player))


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
@tiger.command(name="管理员")
@is_staff()
async def add_admin(ctx, user:discord.User):
    Staff.create(discord_id=user.id)
    await ctx.reply(f"已经任命{user.name}为管理员")


@tiger.command(name="增加")
@is_staff()
async def add_count(ctx, user: discord.User, count: int):
    player = Player.get(Player.discord_id==user.id)
    player.draw_count += count
    player.save()
    await ctx.reply(f"给{player.discord_id.name}增加{count}次抽帖次数。")


# 事件处理
@bot.event
async def on_ready():
    """机器人ready"""
    logger.info("Bot have logged in as {0.user}".format(bot))


@bot.event
async def on_command_error(ctx, error):
    # 没有参加活动报错处理
    match type(error).__name__:
        case "IsNotPlayer"|"CardNotExist"|"PlayerNotExist"|"IsPlayer"|"IsNotStaff":
            await ctx.send(error)
        case _:
            logger.error(error)


init_db()
bot.run(BOT_TOKEN)
