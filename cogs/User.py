import random
import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from discord.ext.commands import errors
from config import WHITELIST
from db import Database
import description


class User(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.db = Database()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'User загружен.')

    @commands.command(name='personal-info', aliases=['pi', 'личная-информация', 'лс'],
                      description=description.PERSONAL_INFO, help=description.PERSONAL_INFO)
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 30, type=BucketType.user)
    async def personal_info(self, ctx):
        await ctx.message.delete()
        # Подключение происходит автоматически при импорте всех данных из database
        voice_min, messages, money = self.db.select_one('users',
                                                        ('voice_min', 'messages', 'money'),
                                                        {'gid': ctx.guild.id,
                                                         'uid': ctx.author.id})
        embed = discord.Embed(title='Личная информация',
                              description='',
                              timestamp=ctx.message.created_at,
                              colour=discord.Colour.from_rgb(255, 154, 0))
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.add_field(name='Voice minutes:', value=f'``{voice_min}``', inline=False)
        embed.add_field(name='Messages:', value=f'``{messages}``', inline=False)
        embed.add_field(name='Money:', value=f'``{money}💵``', inline=False)
        await ctx.author.send(embed=embed)

    @personal_info.after_invoke
    async def reset_personal_info_cd(self, ctx):
        for role_id in WHITELIST:
            if role_id in [role.id for role in ctx.author.roles]:
                self.personal_info.reset_cooldown(ctx)

    @commands.command(name='level', aliases=['show-level'], description=description.USER_LEVEL,
                      help=description.USER_LEVEL)
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 30, type=BucketType.user)
    async def display_level(self, ctx, member: discord.Member = None):
        await ctx.message.delete()
        user = member or ctx.author
        exp, lvl = self.db.select_one('users',
                                      ('exp', 'lvl'),
                                      {'gid': ctx.guild.id,
                                       'uid': user.id})
        if lvl:
            await ctx.send(f'{user.display_name.mention} имеет {lvl} уровень с {exp}XP.')
        else:
            await ctx.send('У этого пользователя нет уровня.')

    @display_level.after_invoke
    async def reset_display_level_cd(self, ctx):
        for role_id in WHITELIST:
            if role_id in [role.id for role in ctx.author.roles]:
                self.display_level.reset_cooldown(ctx)

    @commands.command(aliases=['balance', 'баланс'], description=description.BALANCE, help=description.BALANCE)
    @commands.has_permissions(send_messages=True)
    async def _balance(self, ctx, member: discord.Member = None):
        await ctx.message.delete()
        user = member or ctx.author
        money, lvl, exp = self.db.select_one('users',
                                             ('money', 'lvl', 'exp'),
                                             {'gid': ctx.guild.id,
                                              'uid': user.id})
        embed = discord.Embed(description=f'**{user.display_name}**',
                              colour=ctx.author.colour)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name='**💰Money Bag:**', value=f'``{money}💵``', inline=False)
        embed.add_field(name='**Уровень:**', value=f'``{lvl}``', inline=False)
        embed.add_field(name='**Опыт:**', value=f'``{exp}``', inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['daily', 'bonus', 'бонус'], description=description.BONUS, help=description.BONUS)
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 86400, type=BucketType.user)
    async def gives_out_a_bonus(self, ctx):
        money = self.db.select_one('users',
                                   ('money',),
                                   {'gid': ctx.guild.id,
                                    'uid': ctx.author.id})[0]
        bonus = random.randint(10, 30)
        money += bonus
        self.db.update('users',
                       {'money': money},
                       {'gid': ctx.guild.id,
                        'uid': ctx.author.id})
        self.db.commit()
        await ctx.message.add_reaction('💸')

    @commands.command(aliases=['transfer', 'перевести', 'перевод'],
                      description=description.TRANSFER, help=description.TRANSFER)
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 30, type=BucketType.user)
    async def transfers_money(self, ctx, member: discord.Member, amount: int):
        await ctx.messsage.delete()
        user_money = self.db.select_one('users',
                                        ('money',),
                                        {'gid': ctx.guild.id,
                                         'uid': ctx.author.id})[0]  # Кто переводит
        client_money = self.db.select_one('users',
                                          ('money',),
                                          {'gid': member.guild.id,
                                           'uid': member.id})[0]  # Кому переводят
        if amount < 0:
            raise errors.BadArgument
        else:
            user_money -= amount
            client_money += amount
            self.db.update('users',
                           {'money': user_money},
                           {'gid': ctx.guild.id,
                            'uid': ctx.author.id})
            self.db.update('users',
                           {'money': client_money},
                           {'gid': member.guild.id,
                            'uid': member.id})
            self.db.commit()

    @transfers_money.error
    async def transfer_error(self, ctx, error):
        if isinstance(error, errors.MissingRequiredArgument):
            embed = discord.Embed(description='Вы не определили необходимые аргументы.',
                                  colour=discord.Colour.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        if isinstance(error, errors.BadArgument):
            embed = discord.Embed(description='Укажите корректные данные.\n'
                                              'Кол-во валюты должно быть больше 0 или должно быть числом.',
                                  colour=discord.Colour.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @transfers_money.after_invoke
    async def reset_transfer_cd(self, ctx):
        for role_id in WHITELIST:
            if role_id in [role.id for role in ctx.author.roles]:
                self.transfers_money.reset_cooldown(ctx)


def setup(client):
    client.add_cog(User(client))
