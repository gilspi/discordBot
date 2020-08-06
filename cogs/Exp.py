import discord
import description
from discord.ext import tasks, commands
from discord.ext.commands import BucketType
from db import Database
from config import WHITELIST, CHAT_CHANNEL, COMMAND_CHANNEL, GIVEAWAYS_CHANNEL
import random
import re


def adds_a_field(embed, pos, user, smile: str, money, voice_min, messages, lvl):
    embed.add_field(name=f'#{pos} - {user}',
                    value=f'{smile} Деньги: **{money}** ; Войс|Чат: ``{voice_min}, {messages}`` ; Уровень: **{lvl}**,',
                    inline=False)


def gives_out_coins():
    result = random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    return random.randint(1, 3) if not result else 0


class Exp(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.db = Database()
        self.regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([" \
                     r"^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        self.adds_time_for_voice_min.start()
        self.places = ["🥇", "🥈", "🥉", "🏅"]
        self.patterns = ['messages', 'voice_min', 'money', 'lvl']

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Exp загружен.')

    async def adds_data(self, guild, user):
        user_in_the_table = self.db.select_one('users',
                                               ('uid',),
                                               {'gid': guild.id,
                                                'uid': user.id})
        if not user_in_the_table:
            role = discord.utils.get(user.guild.roles, id=724366698827874396)
            self.db.insert_many('users',
                                {'gid': guild.id,
                                 'uid': user.id,
                                 'roles': str(role)})
            self.db.commit()

    async def add_experience(self, guild, user, exp):
        if not user.bot:
            user_exp = self.db.select_one('users',
                                          ('exp',),
                                          {'gid': guild.id,
                                           'uid': user.id})[0]
            user_exp += exp
            self.db.update('users',
                           {'exp': user_exp},
                           {'gid': guild.id,
                            'uid': user.id})
            self.db.commit()

    async def level_up(self, guild, user, channel):
        if not user.bot:
            exp = self.db.select_one('users',
                                     ('exp',),
                                     {'gid': guild.id,
                                      'uid': user.id})[0]
            current_lvl = self.db.select_one('users',
                                             ('lvl',),
                                             {'gid': guild.id,
                                              'uid': user.id})[0]
            next_lvl = int(exp ** (1 / 4))

            if current_lvl < next_lvl:
                await channel.send(f'{user.mention} поднялся! Теперь у него {next_lvl} уровень!', delete_after=10)
                self.db.update('users',
                               {'lvl': next_lvl},
                               {'gid': guild.id,
                                'uid': user.id})
                self.db.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id not in [CHAT_CHANNEL, GIVEAWAYS_CHANNEL] and re.search(self.regex, message.content):
            await message.delete()
            await message.channel.send('Ты не можешь отправлять ссылки в этом канале.', delete_after=10)

        if message.channel.id not in [COMMAND_CHANNEL, GIVEAWAYS_CHANNEL]:
            count_of_msg, money = self.db.select_one('users',
                                                     ('messages', 'money'),
                                                     {'gid': message.guild.id,
                                                      'uid': message.author.id})
            count_of_msg += 1
            money += gives_out_coins()
            self.db.update('users',
                           {'money': money,
                            'messages': count_of_msg},
                           {'gid': message.guild.id,
                            'uid': message.author.id})
            self.db.commit()

            await self.adds_data(message.guild, message.author)
            await self.add_experience(message.guild, message.author, 1)
            await self.level_up(message.guild, message.author, message.channel)

        if message.channel.id not in [CHAT_CHANNEL, GIVEAWAYS_CHANNEL] and any([hasattr(attach, 'width') for attach in message.attachments]):
            await message.delete()

    def cog_unload(self):
        self.adds_time_for_voice_min.cancel()

    @tasks.loop(minutes=1)
    async def adds_time_for_voice_min(self):
        if len(self._client.guilds) == 0:
            return
        for guild in self._client.guilds:
            for voice_channel in guild.voice_channels:
                # FIXME исправить на 1 для того, чтобы не было накрутки монет
                if voice_channel.id != 723635991646306306 and len(voice_channel.members) > 0:
                    for member in voice_channel.members:
                        voice_min, money = self.db.select_one('users',
                                                              ('voice_min', 'money'),
                                                              {'gid': member.guild.id,
                                                               'uid': member.id})
                        voice_min += 1
                        money += gives_out_coins()
                        await self.add_experience(member.guild.id, member.id, 1)
                        self.db.update('users',
                                       {'money': money,
                                        'voice_min': voice_min},
                                       {'gid': member.guild.id,
                                        'uid': member.author.id})
                        self.db.commit()

    @adds_time_for_voice_min.before_loop
    async def before_talk(self):
        print('waiting...')
        await self._client.wait_until_ready()

    @commands.command(aliases=['top'], descripition=description.LEADERS, help='``Выводит лучших пользователей.``')
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 30, type=BucketType.user)
    async def shows_leaders(self, ctx, pattern: str = 'messages'):
        user = ctx.author
        if pattern in self.patterns:
            top_users = self.db.select_many('users',
                                            ('user_id', 'money', 'lvl', 'messages', 'voice_min'),
                                            {'gid': user.guild.id},
                                            f'ORDER BY {pattern} DESC')[:10]
            embed = discord.Embed(title='Leaders',
                                  description='',
                                  colour=user.colour)
            for pos, writer in enumerate(top_users, 1):
                user_id, money, lvl, messages, voice_min = writer
                user = self._client.get_user(user_id)
                if pos < 4:
                    adds_a_field(embed, pos, user, self.places[pos], money, voice_min, messages, lvl)
                else:
                    adds_a_field(embed, pos, user, self.places[-1], money, voice_min, messages, lvl)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f'{self.patterns}')
            await ctx.send('Укажите корректный тип сортировки')
            await ctx.send(embed=embed)

    @shows_leaders.after_invoke
    async def reset_shows_top_msg(self, ctx):
        for role_id in WHITELIST:
            if role_id in [role.id for role in ctx.author.roles]:
                self.shows_leaders.reset_cooldown(ctx)


def setup(client):
    client.add_cog(Exp(client))


"""
if message.content.startswith('$greet'):
    # greet = choice(constant.GREETINGS)
    channel = message.channel
    await channel.send(f'{choice(GREETINGS)}')

    def check(m):
        return m.content.lower() in GREETINGS and m.channel == channel

    msg = await self.client.wait_for('message', check=check)
    await channel.send('{} {.author.mention}!'.format(choice(GREETINGS), msg))
"""
