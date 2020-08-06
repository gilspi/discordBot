import asyncio
import discord
from discord.ext import commands
from typing import Optional


class Paginator:

    def __init__(self, embeds: Optional[discord.Embed], msg: str = None):
        self.embeds = embeds
        self.msg = msg
