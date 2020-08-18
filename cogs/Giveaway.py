import asyncio
import sys
import re
import json
import random
from typing import Optional, Tuple, List

from datetime import datetime, timedelta
from pytz import timezone

import discord
from discord.ext import commands
from discord.ext.commands import errors

import description
from config import GIVEAWAYS_CHANNEL

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger


class Giveaway(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.scheduler = AsyncIOScheduler()
        self._giveaways = []
        self._gmt = timezone('GMT')
        self.error_color = discord.Colour.red()

    @staticmethod
    def get_prefix(client, message):
        with open('prefixes.json') as f:
            prefixes = json.load(f)

        return prefixes[str(message.guild.id)]

    @staticmethod
    def returns_the_remaining_times(td: Optional[timedelta], _days=False, _hours=False, _minutes=False, _seconds=False):
        print(0)
        __days, __hours, __minutes, __seconds = None, None, None, None
        print(__days, __hours, __minutes, __seconds)
        if _days:
            __days = td.days
            print(__days, 'DAYS', type(__days))

        if _hours:
            __hours = td.seconds // 3600
            print(__hours, 'HOURS', type(__hours))

        if _minutes:
            __minutes = td.seconds // 60 % 60
            print(__minutes, 'MINUTES', type(__minutes))

        if _seconds:
            __seconds = td.seconds
            print(__seconds, 'SECONDS', type(__seconds))

        time_left = f'{f"**{__days}** days" if _days else ""}'\
                    f' {f"**{__hours}** hours" if _hours else ""}' \
                    f' {f"**{__minutes}** minutes" if _minutes else ""}' \
                    f' {f"**{__seconds}** seconds" if _seconds else ""}'
        return time_left

    def return_time_info(self, pattern: Optional[str]) -> Tuple[datetime, timedelta, float, dict]:
        time_match = re.match(r'\d{1,4}[dhmsDHMS]', pattern)
        if time_match is None:
            raise errors.BadArgument('Введено некорректное время!')
        *num_str, time_letter = time_match.group(0)
        num = int(''.join(num_str))

        __td, __time_units = None, {'days': False, 'hours': False, 'minutes': False, 'seconds': False}
        if time_letter in ['d', 'D']:
            __td = timedelta(days=num)
            __time_units['days'], __time_units['hours'], __time_units['minutes'] = True, True, True
        elif time_letter in ['h', 'H']:
            __td = timedelta(hours=num)
            __time_units['hours'], __time_units['minutes'], __time_units['seconds'] = True, True, True
            if len(num_str) > 3:
                __time_units['days'], __time_units['seconds'] = True, False
        elif time_letter in ['m', 'M']:
            __td = timedelta(minutes=num)
            __time_units['minutes'], __time_units['seconds'] = True, True
            if len(num_str) >= 3:
                __time_units['hours'], __time_units['seconds'] = True, False
        elif time_letter in ['s', 'S']:
            if num < 30:
                raise errors.BadArgument('Укажите значение больше, чем 30! **(Для секунд)**')
            if num < 3600:
                __time_units['minutes'] = True
            elif num < 86400:
                __time_units['hours'] = True
            elif num > 86400:
                __time_units['days'] = True
            __td = timedelta(seconds=num)
            __time_units['seconds'] = True

        __dt = datetime.now(self._gmt) + __td
        __seconds = __td.total_seconds()
        return __dt, __td, __seconds, __time_units

    @staticmethod
    def return_number_of_winners(pattern: Optional[str]) -> int:
        winners_match = re.match(r'\d+[wW]', pattern)
        if winners_match is None:
            raise errors.BadArgument('Введено некорректное кол-во победителей!')
        *winners, _ = winners_match.group(0)
        __champions = int(''.join(winners))
        return __champions

    async def updates_embed(self,
                            _message: Optional[discord.Message],
                            _prize: Optional[str],
                            _author: Optional[discord.Member],
                            _end_time: Optional[datetime],
                            _time_units: Optional[dict],
                            _num_of_winners: Optional[int]):
        __time_remaining = _end_time - datetime.now(self._gmt)
        print(__time_remaining, 'END_TIME', type(__time_remaining))
        print(datetime.now(self._gmt) + timedelta(seconds=0.99), 'NOW + TD', _end_time, 'END')
        if datetime.now(self._gmt) < _end_time > datetime.now(self._gmt) + timedelta(seconds=0.99):
            __end_time = _end_time.strftime('%b %d, %Y %I:%M %p (%Z)')
            print(__end_time, 'END_OF_TIME')
            time_left = self.returns_the_remaining_times(__time_remaining,
                                                         _days=_time_units['days'],
                                                         _hours=_time_units['hours'],
                                                         _minutes=_time_units['minutes'],
                                                         _seconds=_time_units['seconds'])
            print(time_left)
            await _message.edit(content=f'{"🎉":<3}**GIVEAWAY**{"🎉":>3}',
                                embed=discord.Embed(title=_prize,
                                                    description=f'{"🎁":<2}Для участия нажать 🎉!\n'
                                                                f'{"⏱":<2}Оставшееся время: {time_left}\n'
                                                                f'{"🐱‍💻":<2}Розыгрыш от: {_author.mention}\n'
                                                                f'{"🏅":<2}Победителей: {_num_of_winners}',
                                                    colour=discord.Colour.from_rgb(102, 153, 204)
                                                    ).set_footer(text=f'Окончание: {__end_time}'))
            print(_message.id, 'UPDATES_EMBED')
        else:
            await self.complete_giveaway(_message.id, _end_time, _num_of_winners, _prize, _author)
            self.scheduler.remove_job(str(_message.id))

    @commands.command(name='gcreate', aliases=['раздавать', 'giveaway'],
                      description=description.GIVEAWAY, help=description.GIVEAWAY)
    @commands.has_permissions(administrator=True)
    async def create_giveaway(self, ctx, time_string: Optional[str], num_of_winners: Optional[str], *, prize: Optional[str]):
        # await ctx.message.delete()
        embed = discord.Embed(title=prize,
                              colour=discord.Colour.from_rgb(102, 153, 204))
        dt, td, seconds, time_units = self.return_time_info(time_string)
        end_of_time = dt.strftime('%b %d, %Y %I:%M %p (%Z)')
        number_of_winners = self.return_number_of_winners(num_of_winners)
        time_remaining = self.returns_the_remaining_times(td,
                                                          _days=time_units["days"],
                                                          _hours=time_units["hours"],
                                                          _minutes=time_units["minutes"],
                                                          _seconds=time_units["seconds"])
        embed.description = f'{"🎁":<2}Для участия нажать 🎉!\n' \
                            f'{"⏱":<2}Оставшееся время: {time_remaining}\n' \
                            f'{"🐱‍💻":<2}Розыгрыш от: {ctx.message.author.mention}\n' \
                            f'{"🏅":<2}Победителей: {number_of_winners}'
        embed.set_footer(text=f'Окончание: {end_of_time}')
        giveaway = await ctx.send(embed=embed)
        await giveaway.edit(content=f'{"🎉":<3}**GIVEAWAY**{"🎉":>3}')
        await giveaway.add_reaction('🎉')
        print(ctx.author, 'CTX.AUTHOR')
        self._giveaways.append((giveaway.id, end_of_time, number_of_winners, prize, ctx.author))
        print(time_units)
        print(giveaway.id, 'BEFORE')
        self.scheduler.add_job(self.updates_embed, IntervalTrigger(seconds=30),
                               args=[giveaway, prize, ctx.author, dt, time_units, number_of_winners], id=str(giveaway.id))
        print(giveaway.id, 'AFTER')
        self.scheduler.start()
        await asyncio.sleep(seconds)

    @staticmethod
    async def return_champions(seq: List, num_of_winners: Optional[int]):
        sequence = [member.mention for member in seq]
        champions = random.choice(sequence) if num_of_winners == 1 else ', '.join(random.sample(sequence, k=num_of_winners))
        return champions

    async def complete_giveaway(self,
                                _message_id: Optional[int],
                                _end_time: Optional[datetime],
                                _num_of_winners: Optional[int],
                                _prize: Optional[str],
                                _author: Optional[discord.Member]):
        message = await self._client.get_channel(GIVEAWAYS_CHANNEL).fetch_message(_message_id)
        if len(members := [u for u in await message.reactions[0].users().flatten() if not u.bot]) >= _num_of_winners:
            champions = await self.return_champions(members, _num_of_winners)
            await message.clear_reaction('🎉')
            await message.edit(content=f'{"🎊":<3}**GIVEAWAY ENDED**{"🎊":>3}',
                               embed=discord.Embed(title=_prize,
                                                   description=f'{"🥇":<2} {champions}\n'
                                                               f'{"🐱‍💻":<2}Розыгрыш от: {_author.mention}',
                                                   timestamp=_end_time,
                                                   colour=discord.Colour.orange()
                                                   ).set_footer(text='Закончился'))
        else:
            await message.clear_reaction('🎉')
            await message.edit(content=f'{"❌":<3}**GIVEAWAY NOT TOOK PLACE**{"❌":>3}',
                               embed=discord.Embed(title=_prize,
                                                   description=f'{"❌":<2}Не смог определить победителя!\n'
                                                               f'{"🐱‍💻":<2}Розыгрыш от: {_author.mention}',
                                                   timestamp=datetime.utcnow(),
                                                   colour=discord.Colour.red()
                                                   ).set_footer(text='Закончился'))

    @create_giveaway.error
    async def create_giveaway_error(self, ctx, error):
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
            embed.description = f'{sys.exc_info()[1]}'
            await ctx.send(embed=embed, delete_after=10)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Giveaway загружен.')


def setup(client):
    client.add_cog(Giveaway(client))
