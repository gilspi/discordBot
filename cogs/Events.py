import datetime
import json

import discord
from discord.ext import commands
from discord.ext.commands import errors
from random import choice  # Для выбора случайного приветствия из списка
from db import Database
from phrases import greetings
from config import settings, WELCOME_CHANNEL


class Events(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.db = Database()

    async def changes_status(self, guild):
        await self._client.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f'за сервером |\nУчастников: {len(guild.members)}'),
            status=discord.Status.idle)

    @staticmethod
    async def sets_prefix(guild):
        with open('prefixes.json') as f:
            prefixes = json.load(f)

        prefixes[str(guild.id)] = str(settings['prefix'])

        with open('prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)

    @staticmethod
    async def remove_prefix(guild):
        with open('prefixes.json') as f:
            prefixes = json.load(f)

        prefixes.pop(str(guild.id))

        with open('prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Events загружен.')
        self.db.creates_tables()
        for guild in self._client.guilds:
            guild_on_the_table = self.db.select_one('guilds',
                                                    ('id',),
                                                    {'id': guild.id})
            await self.changes_status(guild)
            if not guild_on_the_table:
                await self.sets_prefix(guild)
                self.db.insert_many('guilds',
                                    {'id': guild.id,
                                     'name': guild.name,
                                     'owner_id': guild.owner_id,
                                     'owner_name': guild.owner.name})

            for member in guild.members:
                member_in_the_table = self.db.select_one('users',
                                                         ('uid',),
                                                         {'gid': guild.id,
                                                          'uid': member.id})
                if not member_in_the_table:
                    roles = ' '.join([role.name for role in member.roles][1:])
                    self.db.insert_many('users',
                                        {'gid': guild.id,
                                         'uid': member.id,
                                         'roles': str(roles)})
        self.db.commit()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, errors.CommandOnCooldown):
            date = '{:<8}'.format(str(datetime.timedelta(seconds=round(error.retry_after))))
            embed = discord.Embed(description='Вы еще не можете использовать эту команду!\n'
                                              f'Пожалуйста, подождите {date}c.')
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        result = self.db.select_one('guilds',
                                    ('id',),
                                    {'id': guild.id})
        if not result:
            await self.sets_prefix(guild)
            self.db.insert_many('guilds',
                                {'id': guild.id,
                                 'name': guild.name,
                                 'owner_id': guild.owner_id,
                                 'owner_name': guild.owner.name})
            self.db.commit()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.remove_prefix(guild)
        self.db.delete('guilds',
                       {'id': guild.id})  # FIXME удаляется только с определенной таблицы, а удалять нужно все
        self.db.commit()
        print('Покинул гильдию')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        result = self.db.select_one('users',
                                    ('uid',),
                                    {'gid': member.guild.id,
                                     'uid': member.id})
        if not result:
            channel = member.guild.get_channel(channel_id=WELCOME_CHANNEL)
            role = discord.utils.get(member.guild.roles, id=724366698827874396)
            self.db.insert_many('users',
                                {'gid': member.guild.id,
                                 'uid': member.id,
                                 'roles': str(role)})
            await channel.send(f'{member.mention}, {choice(greetings)}')
            await member.add_roles(role)
            self.db.commit()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        self.db.delete('users',
                       {'gid': member.guild.id,
                        'uid': member.id})
        self.db.commit()
        print(f'{member} покинул гильдию!')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        for guild in self._client.guilds:
            if after.channel.id == 732118857271083128:
                category = discord.utils.get(guild.categories, id=732118116733288499)
                room = await guild.create_voice_channel(name=member.name, category=category)
                await room.set_permissions(member, connect=True, move_members=True, manage_channels=True)
                await member.move_to(room)

                def check():
                    return len(room.members) == 0

                await self._client.wait_for('voice_state_update', check=check)
                await room.delete()


def setup(client):
    client.add_cog(Events(client))
