import asyncio
import re
import json

import discord
from discord.ext import commands
from discord.ext.commands import errors

import description
from config import owner_role_id, deputy_role_id, admin_role_id, moder_role_id
from db import Database


# FIXME сделать команду для создания, добавления и удаления ролей


class Admin(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.db = Database()
        self.error_color = discord.Colour.red()

    @commands.command(name='change-prefix', aliases=['new-prefix'])
    @commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id)
    async def change_the_prefix(self, ctx, prefix: str):
        with open('prefixes.json') as f:
            await ctx.message.add_reaction('✅')
            prefixes = json.load(f)

        prefixes[str(ctx.guild.id)] = prefix

        with open('prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)

    @commands.command(name='change-currency', aliases=['валюта', 'установить-валюту', 'изменить-валюту'],
                      description='', help='')
    @commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id)
    async def change_currency(self, emoji: discord.Emoji):
        pass

    @commands.command(name='ban-user', aliases=['ban', 'бан', 'block', 'заблокировать'],
                      description=description.BAN, help=description.BAN)
    @commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id)
    async def ban_member(self, ctx, member: discord.Member, *, reason: str):
        await ctx.message.delete()
        await member.ban(reason=reason)
        await ctx.send(f'{ctx.message.author.mention} забанил {member.mention} {reason}!')

    @ban_member.error
    async def ban_member_error(self, ctx, error):
        if isinstance(error, errors.MissingAnyRole):
            embed = discord.Embed(description='У вас нет соответствующих прав для использование этой команды!\n'
                                              'Необходимые права: `Банить участников`',
                                  colour=self.error_color)
            embed.set_author(name=ctx.message.author.name,
                             icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        if isinstance(error, errors.MissingRequiredArgument):
            embed = discord.Embed(description='Неправильный формат аргумента при вызове команды!\n'
                                              'Ожидался: `@member`, `reason: <строка>`,',
                                  colour=self.error_color)
            embed.set_author(name=ctx.message.author.name,
                             icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(name='unban-user', aliases=['unban', 'uu', 'разбан'],
                      description=description.UNBAN, help=description.UNBAN)
    @commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id)
    async def unban_member(self, ctx, *, member):
        await ctx.message.delete()

        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'{ctx.author.mention} разбанил {user.mention}!')

    @unban_member.error
    async def unban_member_error(self, ctx, error):
        if isinstance(error, errors.MissingAnyRole):
            embed = discord.Embed(description='У вас нет соответствующих прав для использование этой команды!\n'
                                              'Необходимые права: `Банить участников`',
                                  colour=self.error_color)
            embed.set_author(name=ctx.message.author.name,
                             icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        if isinstance(error, errors.MissingRequiredArgument):
            embed = discord.Embed(description='И кого я должен достать из ban list?\n'
                                              'Ожидался: `member#mention`,',
                                  colour=self.error_color)
            embed.set_author(name=ctx.message.author.name,
                             icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(name='kick-user', aliases=['kick', 'выгнать'], description=description.KICK,
                      help=description.KICK)
    @commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id, moder_role_id)
    async def kick_member(self, ctx, member: discord.Member, *, reason: str):
        await ctx.message.delete()
        await member.kick(reason=reason)
        await ctx.send(f'{ctx.author.mention} исключил {member.mention} из гильдии!')

    @kick_member.error
    async def kick_member_error(self, ctx, error):
        if isinstance(error, errors.MissingAnyRole):
            embed = discord.Embed(description='У вас нет соответствующих прав для использование этой команды!\n'
                                              'Необходимые права: `Выгонять участников`',
                                  colour=self.error_color)
            embed.set_author(name=ctx.message.author.name,
                             icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        if isinstance(error, errors.MissingRequiredArgument):
            embed = discord.Embed(description='Неправильный формат аргумента при вызове команды!\n'
                                              'Ожидались: `@member`, `reason: <строка>`,',
                                  colour=self.error_color)
            embed.set_author(name=ctx.message.author.name,
                             icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(name='cleans', aliases=['clear', 'очистка', 'очистить'], description=description.CLEAR,
                      help=description.CLEAR)
    @commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id, moder_role_id)
    async def cleans(self, ctx, *, limit: int):
        await ctx.message.delete()
        await ctx.channel.purge(limit=limit)

    @cleans.error
    async def cleans_error(self, ctx, error):
        if isinstance(error, errors.MissingAnyRole):
            embed = discord.Embed(description='У вас нет соответствующих прав для использование этой команды!\n'
                                              'Необходимые права: `Управлять сообщениями`',
                                  colour=self.error_color)
            embed.set_author(name=ctx.message.author.name,
                             icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        if isinstance(error, errors.BadArgument):
            embed = discord.Embed(description='Сбой при преобразовании в аргументе\n'
                                              'Ожидалось: `limit: <число>`,',
                                  colour=self.error_color)
            embed.set_author(name=ctx.message.author.name,
                             icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        if isinstance(error, errors.MissingRequiredArgument):
            embed = discord.Embed(description='Вы не указали количество сообщений к удалению\n'
                                              'Ожидался: `limit`,',
                                  colour=self.error_color)
            embed.set_author(name=ctx.message.author.name,
                             icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(name='mute-user', aliases=['mute', 'мут', 'замутить'],
                      description=description.MUTE, help=description.MUTE)
    @commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id, moder_role_id)
    async def mute_member(self, ctx, member: discord.Member, period: str, *, reason: str):  # FIXME reason будет храниться в БД
        muted = discord.utils.get(ctx.guild.roles, id=725300743749500959)
        # role = discord.utils.get(ctx.guild.roles, name='unknown')
        # await member.remove_roles(role)
        await member.add_roles(muted)
        await member.move_to(None)
        await ctx.message.add_reaction('✅')  # FIXME как разберусь с БД, начать делать проверку,
        # FIXME если все прошло успешно, то отправлять реакцию, иначе отправлять другую
        time = re.match(r'\d', period)[0]  # FIXME вытаскивать еще и буквы, делать проверку!
        await asyncio.sleep(int(time) * 60 * 60)
        await member.remove_roles(muted)
        # FIXME удалять все роли, потом выдавать роль muted

    @mute_member.error
    async def mute_member_error(self, ctx, error):
        if isinstance(error, errors.MissingAnyRole):
            embed = discord.Embed(description='У вас нет соответствующих прав для использование этой команды!\n'
                                              'Необходимые права: `Управлять ролями`',
                                  colour=self.error_color)
            embed.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
            await ctx.send(embed=embed)
        if isinstance(error, errors.MissingRequiredArgument):
            embed = discord.Embed(description='Неправильный формат аргумента при вызове команды!\n'
                                              'Ожидался: `member: @участник`, `period: <число><h>`, `reason: строка`',
                                  colour=self.error_color)
            embed.set_author(name=ctx.message.author.name,
                             icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    '''@commands.command(name='edit-role', aliases=['редактирование-роли'],
                      description=description.EDIT_ROLE, help=description.EDIT_ROLE)
    @commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id)
    async def edits_a_role(self, ctx, name, permissions, colour: Union[discord.Colour, int], position, reason):
        await self._client.edit(reason=reason, name=name, permissions=permissions, colour=colour, position=position)
    '''


    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Admin загружен.')


def setup(client):
    client.add_cog(Admin(client))



'''        embed = discord.Embed(title='Title',
                              description='Description',
                              colour=discord.Colour.greyple())
        embed.add_field(name='Name1', value='Value1', inline=True)  # ctx.message.author.name
        embed.add_field(name='Name2', value='Value2', inline=False)
        embed.add_field(name='Name3', value='Value3', inline=False)'''

"""    @commands.command()
    @commands.has_any_role(724727558847070379)  # FIXME добавить роли
    async def warn(self, ctx, member: discord.Member, *, reason: str):
        await ctx.channel.purge(limit=1)
        print('test')
        with open('reports.json', encoding='utf-8') as f:
            try:
                report = json.load(f)
                print(report)
            except ValueError:
                report = {'users': []}

        reason = ' '.join(reason)
        for current_user in report['users']:
            if current_user['name'] == member.name:
                return
            else:
                report['users'].append({
                    'name': member.name,
                    'reasons': [reason]
                })
        with open('reports.json', 'w+') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        # FIXME добавить embed, ctx.send(), придумать реализацию warn"""
