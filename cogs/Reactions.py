import discord
from discord.ext import commands
from config import REACTION_MESSAGE


class Reactions(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.roles = {
            '🤍': 731620625772445717,  # white
            '💙': 731620746341777458,  # blue
            '💜': 731620872401453077,  # purple
            '💚': 731621014902931616  # green
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Reactions загружен.')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id == REACTION_MESSAGE:
            for guild in self._client.guilds:
                role = discord.utils.get(guild.roles, id=self.roles[payload.emoji.name])
                await payload.member.add_roles(role, reason='Реакция для получения роли.')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        for guild in self._client.guilds:
            member = guild.get_member(payload.user_id)
            role = discord.utils.get(guild.roles, id=self.roles[payload.emoji.name])
            await member.remove_roles(role, reason='Реакция для получения роли.', atomic=True)


def setup(client):
    client.add_cog(Reactions(client))
