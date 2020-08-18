import json

import discord
from discord.ext import commands
from discord.ext.commands import BucketType

import description
from config import COMMAND_CHANNEL


class Info(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.patterns = ['server', 'me', 'text-channel', 'voice-channel', 'role']
        self.error = discord.Colour.red()
        self.blue = discord.Colour.from_rgb(0, 174, 255)
        self.orange = discord.Colour.orange()

    @staticmethod
    def get_prefix(client, message):
        with open('prefixes.json') as f:
            prefixes = json.load(f)

        return prefixes[str(message.guild.id)]

    @staticmethod
    def create_embed(title, description, timestamp, colour=discord.Colour.red()):
        embed_ = discord.Embed(title=title,
                               description=description,
                               timestamp=timestamp,
                               colour=colour)
        return embed_

    async def show_error(self, title, description, message, channel):
        embed_ = self.create_embed(title,
                                   description,
                                   message.created_at)
        await channel.send(embed=embed_)

    @commands.group(name='info', aliases=['about', 'инфо'], description=description.INFO, help=description.INFO)
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 10, type=BucketType.user)
    async def info(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid displays command passed...')

    @info.command(name='user', aliases=['me', 'i', 'я'],
                  description=description.USER_INFO, help=description.USER_INFO)
    async def receives_user_info(self, ctx, member: discord.Member = None):
        await ctx.message.delete()
        if ctx.channel.id != COMMAND_CHANNEL:
            await ctx.message.delete()
            await self.show_error('Ошибка',
                                  'Использование этой команды здесь запрещенно\n'
                                  f'Ты можешь использовать эту команду в #{self._client.get_channel(COMMAND_CHANNEL)}',
                                  ctx.message,
                                  ctx.channel)
            self.receives_user_info.reset_cooldown(ctx)
            return
        user = member or ctx.author
        embed = self.create_embed(title=f'Информация о {user}',
                                  description='',
                                  timestamp=ctx.message.created_at,
                                  colour=self.blue)

        roles = [role.mention for role in user.roles][1:][::-1]
        embed.set_thumbnail(url=user.avatar_url)
        data = [('ID:', user.id, True),
                ('Имя:', user.name, True),
                ('Имя на сервере:', user.display_name, True),
                ('Роли:', f'{" ".join(roles)}', True),
                ('Вступил на сервер:', f'{user.joined_at.strftime("%Y.%m.%d в %H:%M")}', True),
                ('Создал аккаунт:', f'*{user.created_at.strftime("%Y.%m.%d в %H:%M")}*', True)]
        for name, value, inline in data:
            embed.add_field(name=name, value=value, inline=inline)
        embed.set_footer(text=f'Посмотри {self.get_prefix(self._client, ctx.message)}help',
                         icon_url=user.avatar_url)
        await ctx.send(embed=embed)

    @info.command(name='guild', aliases=['server', 'сервер', 'гильдия'],
                  description=description.GUILD_INFO, help=description.GUILD_INFO)
    async def receives_guild_info(self, ctx):
        await ctx.message.delete()
        if ctx.channel.id != COMMAND_CHANNEL:
            await ctx.message.delete()
            await self.show_error('Ошибка',
                                  'Использование этой команды здесь запрещенно\n'
                                  f'Ты можешь использовать эту команду в #{self._client.get_channel(COMMAND_CHANNEL)}',
                                  ctx.message,
                                  ctx.channel)
            self.receives_guild_info.reset_cooldown(self)
            return
        embed = self.create_embed(title=f'Информация о сервере {ctx.guild.name}:',
                                  description='',
                                  timestamp=ctx.message.created_at,
                                  colour=self.orange)

        statuses = [len(list(filter(lambda m: str(m.status) == 'online', ctx.guild.members))),
                    len(list(filter(lambda m: str(m.status) == 'offline', ctx.guild.members))),
                    len(list(filter(lambda m: str(m.status) == 'idle', ctx.guild.members))),
                    len(list(filter(lambda m: str(m.status) == 'dnd', ctx.guild.members))),
                    len(list(filter(lambda m: str(m.status) == 'invisible', ctx.guild.members)))]

        members = [f'Всего: **{len(ctx.guild.members)}**',
                   f'Людей: **{len(list(filter(lambda m: not m.bot, ctx.guild.members)))}**',
                   f'Ботов: **{len(list(filter(lambda m: m.bot, ctx.guild.members)))}**']

        channels = [f'Всего: **{len(ctx.guild.channels)}**',
                    f'Текстовых: **{len(ctx.guild.voice_channels)}**',
                    f'Голосовых: **{len(ctx.guild.text_channels)}**']

        data = [('**Участники:**', f'{members[0]}\n{members[1]}\n{members[2]}', True),
                ('**По статусам:**',
                 f'В сети: **{statuses[0]}**\nНе в сети: **{statuses[1]}**\nНе активен: **{statuses[2]}**\n'
                 f'Не беспокоить: **{statuses[3]}**\nНевидимый: **{statuses[4]}**', True),
                ('**Каналы:**', f'{channels[0]}\n{channels[1]}\n{channels[2]}', True),
                ('**Владелец:**', f'{ctx.guild.owner.name}', True),
                ('**Регион:**', f'{ctx.guild.region}', True),
                ('**Уровень проверки:**', f'{ctx.guild.verification_level}', True),
                ('**Дата создания:**', f'{ctx.guild.created_at.strftime("%Y.%m.%d в %H:%M")}', True)]
        for name, value, inline in data:
            embed.add_field(name=name, value=value, inline=inline)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @info.command(name='role', aliases=['роль'], description=description.ROLE_INFO, help=description.ROLE_INFO)
    async def receives_role_info(self, ctx, role: discord.Role):
        await ctx.message.delete()
        embed = self.create_embed(title=f'Информация о роли: {role}',
                                  description='',
                                  timestamp=ctx.message.created_at,
                                  colour=self.orange)
        data = [(f'**Идентификатор роли:**', f'{role.id}', True),
                (f'**Название роли:**', f'{role.name}', True),
                (f'**Отображается ли роль отдельно от других участников:**', f'{"Да" if role.hoist else "Нет"}', True),
                (f'**Позиция роли:**', f'{role.position}', True),
                (f'**Интеграции:**', f'{"Да" if role.managed else "Нет"}', True),
                (f'**Могут ли пользователи упоминать эту роль:**', f'{"Да" if role.mentionable else "Нет"}', True)]
        for name, value, inline in data:
            embed.add_field(name=name, value=value, inline=inline)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Info загружен.')


def setup(client):
    client.add_cog(Info(client))
