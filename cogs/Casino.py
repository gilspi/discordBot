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
        self.magenta = discord.Colour.dark_magenta()
        self.arrows = {1: '↖',
                       2: '⬆',
                       3: '↗',
                       4: '➡',
                       5: '↘',
                       6: '⬇',
                       7: '↙',
                       8: '⬅'}

    async def displays_error(self, ctx, description):
        embed = discord.Embed(description=description,
                              colour=self.error)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    def create_embed(self, rate: int, is_win: bool, arrow, factor: float = None, winnings: float = None,
                     money: float = None):
        nums = {'1': '1️⃣',
                '2': '2️⃣',
                '3': '3️⃣',
                '4': '4️⃣',
                '5': '5️⃣',
                '6': '6️⃣',
                '7': '7️⃣',
                '8': '9️⃣'}  # FIXME исправить на 8
        embed = discord.Embed(title='Casino',
                              description='',
                              colour=self.magenta)
        data = [('**Ставка:**', rate, True),
                (f'{"**Остаток на счете:**" if factor is None else "**Множитель:**"}',
                 f'{money if factor is None else factor}', False),
                (f'{"**Выигрыш:**" if is_win else "**Проигрыш:**"}',
                 f'{"**Не везет, попробуй еще раз!**" if winnings is None else winnings}', False),
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

    @commands.command(name='casino', aliases=['казино'],
                      description=description.CASINO, help=description.CASINO)
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 5, type=BucketType.user)
    async def show_casino(self, ctx, range_: str, rate: Union[int, float]):
        money = self.db.select_one('users',
                                   ('money',),
                                   {'gid': ctx.guild.id,
                                    'uid': ctx.author.id})[0]
        r = self.counts_zeros(rate)
        if rate is None or not isinstance(rate, (int, float)) or len(r) > 2 or rate < 0 or money < rate:
            raise errors.BadArgument
        if range_ not in self._range:
            embed = discord.Embed(title='Ошибка!',
                                  description=f'Введенный диапазон({range_}) не соответствует не одному из возможных({self._range}).',
                                  colour=self.error)
            await ctx.send(embed=embed)
        arrow = self.returns_a_random_arrow()
        print(arrow, 'AR')
        is_win = False
        if range_ == '1-2' and (arrow == self.arrows[1] or arrow == self.arrows[2]):
            is_win = True
            factor = 1.5
            winnings = rate * factor
            money += winnings
            embed = self.create_embed(rate, is_win, arrow, factor, winnings)
            print(f'Ставка-{rate}\nМножитель-{factor}\nВыигрыш-{winnings}.')
        elif range_ == '3-4' and (arrow == self.arrows[3] or arrow == self.arrows[4]):
            is_win = True
            factor = 2.0
            winnings = rate * factor
            money += winnings
            embed = self.create_embed(rate, is_win, arrow, factor, winnings)
            print(f'Ставка-{rate}\nМножитель-{factor}\nВыигрыш-{winnings}.')
        elif range_ == '5-6' and (arrow == self.arrows[5] or arrow == self.arrows[6]):
            is_win = True
            factor = 3.0
            winnings = rate * factor
            embed = self.create_embed(rate, is_win, arrow, factor, winnings)
            money += winnings
            print(f'Ставка-{rate}\nМножитель-{factor}\nВыигрыш-{winnings}.')
        elif range_ == '7-8' and (arrow == self.arrows[7] or arrow == self.arrows[8]):
            is_win = True
            factor = 5.0
            winnings = rate * factor
            money += winnings
            embed = self.create_embed(rate, is_win, arrow, factor, winnings)
            print(f'Ставка-{rate}\nМножитель-{factor}\nВыигрыш-{winnings}.')
        else:
            print(is_win, 'ELSE')
            print(money, 'MONEY BEFORE')
            money -= rate  # Текущий баланс, с учетом ставки.
            print(money, 'MONEY AFTER')
            embed = self.create_embed(rate, is_win, arrow, money=money)
            print(f'Ставка не сыграла\nВы проиграл {rate}!\nТекуший баланс {money}\n')
        print(is_win, 'OUTER')
        self.db.update('users',
                       {'money': money},
                       {'gid': ctx.guild.id,
                        'uid': ctx.author.id})
        self.db.commit()
        await ctx.send(embed=embed)

    @show_casino.error
    async def show_casino_error(self, ctx, error):
        if isinstance(error, errors.MissingRequiredArgument):
            await self.displays_error(ctx, desc_errors['miss_req_arg'])
        if isinstance(error, errors.BadArgument):
            await self.displays_error(ctx, 'Укажите корректные данные.\n'
                                           'Введена некорректная ставка(слишком много нулей).\n'
                                           'Ставка ДОЛЖНА БЫТЬ больше 0 или должна быть числом.', )

    @commands.Cog.listener()
    async def on_ready(self):
        print('Casino загружен')


def setup(client):
    client.add_cog(Casino(client))
