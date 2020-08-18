import json
import re
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import errors

from config import ROLES_CHANNEL, CHATEAU_COMMON_COLOR_ROLES_WEBHOOK_ID, COMMON_COLOR_ROLES_MESSAGE
from description import WEBHOOK_REACTIONS


class Reactions(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.roles = {'💚': 731621014902931616,  # green
                      '💛': 744310420713504859,  # yellow
                      '💜': 731620872401453077,  # purple
                      '💙': 731620746341777458,  # blue
                      '🤍': 731620625772445717}  # white
        self.messages_ids = {COMMON_COLOR_ROLES_MESSAGE}
        self.error_color = discord.Colour.red()

    @staticmethod
    def get_prefix(client, message):
        with open('prefixes.json') as f:
            prefixes = json.load(f)

        return prefixes[str(message.guild.id)]

    @commands.command(name='adds-reactions', aliases=['добавить-реакции'],
                      description=WEBHOOK_REACTIONS, help=WEBHOOK_REACTIONS)
    @commands.has_permissions(administrator=True)
    async def adds_webhook_reactions(self, ctx, message_id: Optional[int], *, emojis_and_roles_ids: str):
        message = await self._client.get_channel(ROLES_CHANNEL).fetch_message(message_id)
        clean_data = emojis_and_roles_ids.strip()
        bd = re.findall(r'([\u263a-\U0001F947]\s*:\s*\d+)|(<:\w+:\d+>\s*:\s*\d+)', clean_data)
        data = [''.join([element for element in elements if len(element) > 0]) for elements in bd]
        emoji = None
        for elements in data:
            dirty_str = ' '.join([element.strip() for element in elements.split(':')])
            if elements.startswith('<:'):
                emoji_name, str_emoji_id, str_role_id = [element.strip() for element in
                                                         re.sub(r'[<>]', ' ', dirty_str).strip().split()]
                emoji_id, role_id = int(str_emoji_id), int(str_role_id)
                emoji = self._client.get_emoji(emoji_id)
                self.roles[emoji_name] = role_id
            else:
                emoji, *_nums = dirty_str
                role_id = int(''.join(_nums).strip())
                self.roles[emoji] = role_id

        await message.add_reaction(emoji)

        self.messages_ids.add(message_id)
        await ctx.send('**Реакции добавлены!**', delete_after=10)

    @adds_webhook_reactions.error
    async def adds_webhook_reactions_error(self, ctx, error):
        embed = discord.Embed(title='Ошибка',
                              colour=self.error_color)
        embed.set_footer(text=f'Воспользуйтесь командой {self.get_prefix(self._client, ctx.message)}help',
                         icon_url=ctx.message.author.avatar_url)
        if isinstance(error, errors.MissingPermissions):
            embed.description = 'У вас нет соответствующих разрешений для использование этой команды!\n' \
                                'Необходимые разрешения: `Администратор`.'
            await ctx.send(embed=embed, delete_after=10)
        if isinstance(error, errors.MissingRequiredArgument):
            embed.description = 'Вы не определили необходимые аргументы.'
            await ctx.send(embed=embed, delete_after=10)
        if isinstance(error, errors.BadArgument):
            embed.description = f'Вы ввели некорректные аргументы.\n' \
                                f'Message_id - целое число(**id сообщения**, к которому хотите добавить **роли по смайликам**).' \
                                f'Emoji_and_role_id - **(`без \`)emoji** **:** **role_id**, с которым будет связан смайлик.'
            await ctx.send(embed=embed, delete_after=10)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        for guild in self._client.guilds:
            if payload.message_id in self.messages_ids:
                role = discord.utils.get(guild.roles, id=self.roles[payload.emoji.name])
                unknown_role = discord.utils.get(guild.roles, id=724366698827874396)
                await payload.member.remove_roles(unknown_role)
                await payload.member.add_roles(role, reason='Роль по реакции.', atomic=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        for guild in self._client.guilds:
            if payload.message_id in self.messages_ids:
                role = discord.utils.get(guild.roles, id=self.roles[payload.emoji.name])
                default_role = discord.utils.get(guild.roles, id=724366698827874396)
                await payload.member.remove_roles(role, reason='Реакция для получения роли.', atomic=True)
                await payload.member.add_roles(default_role)

    @staticmethod
    async def return_users(message: Optional[discord.Message]):
        users = []
        for reaction in message.reactions:
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)
        return users

    # FIXME занести все данные в БД (роли)!

    async def addReaction(self, message: Optional[discord.Message]):
        for emoji in self.roles:
            await message.add_reaction(emoji)

    async def removeRole(self, message: Optional[discord.Message]):
        default_role = discord.utils.get(message.guild.roles, id=724366698827874396)
        for member in message.guild.members:
            for reaction in message.reactions:
                new_role = discord.utils.get(message.guild.roles, id=self.roles[reaction.emoji])
                async for user in reaction.users():
                    if not member.bot and (member is not user) and (member in new_role.members):
                        await member.add_roles(default_role)
                        await member.remove_roles(new_role)

    async def addRoles(self, message: Optional[discord.Message]):
        default_role = discord.utils.get(message.guild.roles, id=724366698827874396)
        for member in message.guild.members:
            for reaction in message.reactions:
                new_role = discord.utils.get(message.guild.roles, id=self.roles[reaction.emoji])
                async for user in reaction.users():
                    if not member.bot and (member is user) and (member not in new_role.members):
                        await user.remove_roles(default_role)
                        await user.add_roles(new_role)
                    if not member.bot and (member is not user) and (member in new_role.members):
                        # await member.send(f'Зайди в канал {message.channel.name} и получи роль!\n**Bug** fixed.')
                        await member.remove_roles(new_role)
                        await member.add_roles(default_role)

    async def processesData(self, channel: Optional[discord.TextChannel]):
        async for message in channel.history():
            if message.author.id == CHATEAU_COMMON_COLOR_ROLES_WEBHOOK_ID and self.roles:
                if len(message.reactions) == 0:
                    await self.addReaction(message)
                elif len(await self.return_users(message)):
                    await self.addRoles(message)
                else:
                    await self.removeRole(message)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self._client.guilds:
            for channel in guild.channels:
                role_channel = re.match(r'[\u263a-\U0001F947]*.*\w+.*((roles|role)|(роли|ролей))|роль', str(channel))
                if role_channel is not None:
                    channel = discord.utils.get(guild.channels, name=role_channel.group(0))
                    await self.processesData(channel)
        print(f'Reactions загружен.')


def setup(client):
    client.add_cog(Reactions(client))
