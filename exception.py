from discord.ext import commands


class IsNotPlayer(commands.CheckFailure):
    pass


class IsPlayer(commands.CheckFailure):
    pass


class IsNotStaff(commands.CheckFailure):
    pass


class CardNotExist(commands.CommandError):
    pass


class PlayerNotExist(commands.CommandError):
    pass
