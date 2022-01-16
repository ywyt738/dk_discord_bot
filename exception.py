from discord.ext import commands


class IsNotPlayer(commands.CheckFailure):
    pass


class IsPlayer(commands.CheckFailure):
    pass


class IsNotStaff(commands.CheckFailure):
    pass


class CardNotExisit(commands.CommandError):
    pass


class PlayerNotExisit(commands.CommandError):
    pass
