import asyncio
import sys
import re
import random
from typing import Optional, Tuple, List

from datetime import datetime, timedelta
from pytz import timezone

import discord
from discord.ext import commands
from discord.ext.commands import errors

import description
from config import owner_role_id, admin_role_id, deputy_role_id, moder_role_id, GIVEAWAYS_CHANNEL


class Giveaway(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.giveaways = []
        self.gmt = timezone('GMT')
        self.error_color = discord.Colour.red()

    def return_prefix(self, message):
        return self._client.command_prefix(self._client, message)

    def return_time(self, pattern: Optional[str]) -> Tuple[datetime, float]:
        time_match = re.match(r'\d+[dhmsDHMS]', pattern)
        if time_match is None:
            raise errors.BadArgument('Введено некорректное время!')
        num_str, time_unit = time_match.group(0)
        num = int(num_str)
        dt, td = None, None
        if time_unit in ['d', 'D']:
            days = timedelta(days=num)
            dt = datetime.now(self.gmt) + days
            td = timedelta(days=num).total_seconds()
        elif time_unit in ['h', 'H']:
            hours = timedelta(hours=num)
            dt = datetime.now(self.gmt) + hours
            td = timedelta(hours=num).total_seconds()
        elif time_unit in ['m', 'M']:
            minutes = timedelta(minutes=num)
            dt = datetime.now(self.gmt) + minutes
            td = timedelta(minutes=num).total_seconds()
        elif time_unit in ['s', 'S']:
            seconds = timedelta(seconds=num)
            dt = datetime.now(self.gmt) + seconds
            td = timedelta(seconds=num).total_seconds()
        return dt, td

    @staticmethod
    def return_number_of_winners(pattern: Optional[str]) -> int:
        winners_match = re.match(r'\d[wW]', pattern)
        if winners_match is None:
            raise errors.BadArgument('Ведено некорректное кол-во победителей!')
        winners = int(winners_match.group(0)[0])
        return winners

    @commands.command(name='gcreate', aliases=['раздавать', 'giveaway'],
                      description=description.GIVEAWAY, help=description.GIVEAWAY)
    @commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id, moder_role_id)
    async def create_giveaway(self, ctx, time_string: Optional[str], num_of_winners: Optional[str], *, prize: Optional[str]):
        await ctx.message.delete()
        embed = discord.Embed(title=prize,
                              colour=discord.Colour.from_rgb(102, 153, 204))
        dt, td = self.return_time(time_string)
        time_ending = dt.strftime('%b %d, %Y %I:%M %p (%Z)')
        number_of_winners = self.return_number_of_winners(num_of_winners)
        embed.description = f'{"🎁":<2}Для участия нажать 🎉!\n' \
                            f'{"⏱":<2}Оставшееся время: {"**BETA**"}\n' \
                            f'{"🐱‍💻":<2}Розыгрыш от: {ctx.message.author.mention}\n' \
                            f'{"🏅":<2}Победителей: {number_of_winners}'
        embed.set_footer(text=f'Окончание: {time_ending}')
        giveaway = await ctx.send(embed=embed)
        await giveaway.edit(content=f'{"🎉":<3}**GIVEAWAY**{"🎉":>3}')
        await giveaway.add_reaction('🎉')
        await asyncio.sleep(td)
        self.giveaways.append((giveaway.id, time_ending, number_of_winners, prize, ctx.author))
        await self.complete_giveaway(giveaway.id, dt, number_of_winners, prize, ctx.author)

    @staticmethod
    async def return_champions(seq: List, num_of_winners: Optional[int]):
        sequence = [member.mention for member in seq]
        champions = random.choice(sequence) if num_of_winners == 1 else ', '.join(random.sample(sequence, k=num_of_winners))
        return champions

    async def complete_giveaway(self, message_id: Optional[int], end_time: Optional[datetime], num_of_winners: Optional[int], prize: Optional[str], author: Optional[discord.Member]):
        message = await self._client.get_channel(GIVEAWAYS_CHANNEL).fetch_message(message_id)
        if len(members := [u for u in await message.reactions[0].users().flatten() if not u.bot]) >= num_of_winners:
            champions = await self.return_champions(members, num_of_winners)
            await message.clear_reaction('🎉')
            await message.edit(content=f'{"🎊":<3}**GIVEAWAY ENDED**{"🎊":>3}',
                               embed=discord.Embed(title=prize,
                                                   description=f'{"🥇":<2} {champions}\n'
                                                               f'{"🐱‍💻":<2}Розыгрыш от: {author.mention}',
                                                   timestamp=end_time,
                                                   colour=discord.Colour.orange()
                                                   ).set_footer(text='Закончился'))
        else:
            await message.clear_reaction('🎉')
            await message.edit(content=f'{"❌":<3}**GIVEAWAY NOT TOOK PLACE**{"❌":>3}',
                               embed=discord.Embed(title=prize,
                                                   description=f'{"❌":<2}Не смог определить победителя!\n'
                                                               f'{"🐱‍💻":<2}Розыгрыш от: {author.mention}',
                                                   timestamp=datetime.utcnow(),
                                                   colour=discord.Colour.red()
                                                   ).set_footer(text='Закончился'))

    @create_giveaway.error
    async def create_giveaway_error(self, ctx, error):
        embed = discord.Embed(title='Ошибка',
                              colour=self.error_color)
        embed.set_footer(text=f'Воспользуйтесь командой {self.return_prefix(ctx.message)}help',
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
