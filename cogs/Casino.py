import discord
from discord.ext import commands
from db import Database
from discord.ext.commands import BucketType, errors
from config import desc_errors
from typing import Union
import description
import random


class Casino(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.db = Database()
        self._range = ['1-2', '3-4', '5-6', '7-8']
        self.error = discord.Colour.red()
        self.black = discord.Colour.from_rgb(0, 0, 0)
        self.arrows = {1: '↖',
                       2: '⬆',
                       3: '↗',
                       4: '➡',
                       5: '↘',
                       6: '⬇',
                       7: '↙',
                       8: '⬅'}

    async def displays_error(self, message, desc):
        embed = discord.Embed(description=desc,
                              colour=self.error)
        embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
        await message.channel.send(embed=embed)

    def create_embed(self, rate: int, is_win: bool, arrow, factor: float = None, winnings: float = None,
                     money: float = None):
        nums = {'1': '1️⃣',
                '2': '2️⃣',
                '3': '3️⃣',
                '4': '4️⃣',
                '5': '5️⃣',
                '6': '6️⃣',
                '7': '7️⃣',
                '8': '8️⃣'}
        embed = discord.Embed(title='Casino',
                              description='',
                              colour=self.black)
        data = [('**Ставка:**', rate, True),
                (f'{"**Остаток на счете:**" if factor is None else "**Множитель:**"}',
                 f'{money if factor is None else factor}', False),
                (f'{"**Выигрыш:**" if is_win else "**Проигрыш:**"}',
                 f'{"**Не везет, попробуй еще раз!**" if not is_win else winnings}', False),
                ('**Рулетка**',
                 f'{nums["1"]}{nums["2"]}{nums["3"]}\n{nums["8"]}{arrow}{nums["4"]}\n{nums["7"]}{nums["6"]}{nums["5"]}',
                 False)]
        for name, value, inline in data:
            embed.add_field(name=name, value=f'{value}', inline=inline)
        return embed

    @staticmethod
    def counts_zeros(num: Union[int, float]):
        after_comma = [int(n) for n in str(num).split('.')[-1]]
        return after_comma

    def returns_a_random_arrow(self):
        random.seed()
        key = random.randrange(1, len(self.arrows) + 1)
        arrow = self.arrows[key]
        return arrow

    def calculates(self, money, is_win: bool, arrow: str, rate: Union[int, float], factor: Union[int, float] = None):
        if is_win:
            winnings = rate * factor
            money += winnings
            embed = self.create_embed(rate, is_win, arrow, factor, winnings)
        else:
            money -= rate  # Текущий баланс, с учетом ставки.
            embed = self.create_embed(rate, is_win, arrow, money=money)
        return embed

    @commands.command(name='casino', aliases=['казино'],
                      description=description.CASINO, help=description.CASINO)
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 5, type=BucketType.user)
    async def show_casino(self, ctx, _range: str, rate: Union[int, float]):
        money = self.db.select_one('users',
                                   ('money',),
                                   {'gid': ctx.guild.id,
                                    'uid': ctx.author.id})[0]
        after_comma = self.counts_zeros(rate)
        if _range not in self._range:
            await self.displays_error(ctx.message,
                                      f'Введенный диапазон({_range}) не соответствует ни одному из возможных({self._range}).')
        if rate is None or not isinstance(rate, (int, float)) or rate < 0 or money < rate or len(after_comma) > 2:
            raise errors.BadArgument
        arrow = self.returns_a_random_arrow()
        if _range == '1-2' and (arrow == self.arrows[1] or arrow == self.arrows[2]):
            embed_ = self.calculates(money, True, arrow, rate, 1.5)
        elif _range == '3-4' and (arrow == self.arrows[3] or arrow == self.arrows[4]):
            embed_ = self.calculates(money, True, arrow, rate, 2)
        elif _range == '5-6' and (arrow == self.arrows[5] or arrow == self.arrows[6]):
            embed_ = self.calculates(money, True, arrow, rate, 3)
        elif _range == '7-8' and (arrow == self.arrows[7] or arrow == self.arrows[8]):
            embed_ = self.calculates(money, True, arrow, rate, 5)
        else:
            embed_ = self.calculates(money, False, arrow, rate)
        await ctx.send(embed=embed_)
        self.db.update('users',
                       {'money': money},
                       {'gid': ctx.guild.id,
                        'uid': ctx.author.id})
        self.db.commit()

    @show_casino.error
    async def show_casino_error(self, ctx, error):
        if isinstance(error, errors.MissingRequiredArgument):
            await self.displays_error(ctx.message, desc_errors['miss_req_arg'])
        if isinstance(error, errors.BadArgument):
            await self.displays_error(ctx.message, 'Укажите корректные данные.\n'
                                                   'Введена некорректная ставка(пример ставки: 100.15).\n'
                                                   'Ставка должна быть больше 0 или должна быть числом.', )

    @commands.Cog.listener()
    async def on_ready(self):
        print('Casino загружен')


def setup(client):
    client.add_cog(Casino(client))
