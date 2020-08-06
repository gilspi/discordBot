import asyncio
import sys
import re
from random import choice
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord.ext import commands, tasks
from discord.ext.commands import errors

import description
from config import owner_role_id, admin_role_id, deputy_role_id, moder_role_id, WINNERS_CHANNEL, GIVEAWAYS_CHANNEL


class Giveaway(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.giveaways = []
        self.error_color = discord.Colour.red()

    @staticmethod
    def return_time(pattern: str) -> datetime:
        # assert isinstance(pattern, str), 'Шаблон должен быть строкой.'
        time_string = re.match(r'(((0[0-9]|1[0-9])|2[0-4])\:([0-5][0-9]|00))', pattern)  # (?:AM|PM|am|pm)
        print(time_string, 'TIME_STRING')
        if time_string is None:
            raise errors.BadArgument('Было введено некорректное время!')
        time = datetime.strptime(time_string.group(0), '%H:%M')
        print(time)
        return time

    @staticmethod
    def return_date(pattern: str) -> datetime:
        # assert isinstance(pattern, str), 'Шаблон должен быть строкой.'
        date_string = re.match(r'^((([1-9]|0[1-9])|1[0-9])|(2[0-9]|3[0-1]))(.|-)(([1-9]|0[1-9])|1[0-2])(.|-)20[0-9][0-9]$', pattern)
        print(date_string, 'DATE_STRING')
        if date_string is None:
            raise errors.BadArgument('Была введена некорректная дата!')
        date = datetime.strptime(date_string.group(0), '%d.%m.%Y') or datetime.strptime(date_string.group(0), '%d:%m:%Y')
        print(date, 'DATE')
        return date

    @staticmethod
    def return_seconds_in_time(time: Optional[datetime]) -> float:
        return float((time.hour * 60 + time.minute) * 60 + time.second)

    '''@staticmethod
    def return_timedelta_to_seconds(date: datetime):
        return '''

    @commands.command(name='gcreate', aliases=['раздавать', 'giveaway'],
                      description=description.GIVEAWAY, help=description.GIVEAWAY)
    @commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id, moder_role_id)
    async def create_giveaway(self, ctx, time_string: str, date_string: str, *, title: str = 'GIVEAWAY'):  # = datetime.now().strftime("%d-%m-%Y")
        embed = discord.Embed(title=title,  # FIXME добавить смайлы
                              colour=discord.Colour.blue())
        time = self.return_time(time_string)
        date = self.return_date(date_string)
        td = (date.date() - datetime.now().date()).total_seconds() + self.return_seconds_in_time(time)
        print(td, type(td), (time.hour * 60 + time.minute) * 60 + time.second)
        time_remaining = ':'.join(str(timedelta(seconds=round(td))).split(':')[:2])
        print(time_remaining, type(time_remaining), 'TIME_REMAINING')
        embed.description = 'Для участия нажать ✅!\n' \
                            f'Оставшееся время: {time_remaining}\n' \
                            f'Розыгрыш от: {ctx.message.author.mention}'
        print(embed.description, 'DESCRIPTION')
        embed.set_footer(text=f'Конец через | {time_remaining}')
        print('OK initialize embed')
        giveaway = await ctx.send(embed=embed)
        print('OK, init giveaway')
        await giveaway.add_reaction('✅')
        await asyncio.sleep(.5 * 60)  # round(delta)
        self.giveaways.append(ctx.message.id)
        await self.complete_giveaway(ctx.message.id)

    async def complete_giveaway(self, message_id):
        message = await self._client.get_channel(GIVEAWAYS_CHANNEL).fetch_message(message_id)
        print(message)
        channel = self._client.get_channel(WINNERS_CHANNEL)
        print(channel)
        print(await message.reactions[0].users().flatten())
        if len(members := [u for u in await message.reactions[0].users().flatten() if not u.bot]) > 0:
            winner = choice(members)
            print(winner)
            await channel.send(f'Победитель в розыгрыше - {winner.mention}! Поздравляем!')
        else:
            await channel.send('Розыгрыш не состоялся!')

    @create_giveaway.error
    async def create_giveaway_error(self, ctx, error):
        embed = discord.Embed(title='Ошибка',
                              colour=self.error_color)
        embed.set_footer(
            text=f'Воспользуйтесь командой {self._client.command_prefix(self._client, ctx.message)}help',
            icon_url=ctx.message.author.avatar_url)
        if isinstance(error, errors.MissingAnyRole):
            embed.description = 'У вас нет соответствующих прав для использование этой команды!\n' \
                                'Необходимые права: `Управлять ролями`'
            await ctx.send(embed=embed, delete_after=10)
        if isinstance(error, errors.BadArgument):
            embed.description = f'{sys.exc_info()[1]}'
            await ctx.send(embed=embed, delete_after=10)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Giveaway загружен.')


def setup(client):
    client.add_cog(Giveaway(client))
