import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from discord.ext.commands import errors
import description
from config import COMMAND_CHANNEL


class Info(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.patterns = ['server', 'me', 'text-channel', 'voice-channel', 'role']
        self.error = discord.Colour.red()
        self.blue = discord.Colour.from_rgb(0, 174, 255)
        self.orange = discord.Colour.orange()

    def create_embed(self, title, description, timestamp, colour=discord.Colour.red()):
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

    @commands.group(name='info', aliases=['about', 'инфо'])
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 10, type=BucketType.user)
    async def info(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid displays command passed...')

    @info.command(name='user', aliases=['me', 'i', 'я'],
                  description=description.USER_INFO, help=description.USER_INFO)
    async def receives_user_info(self, ctx, member: discord.Member = None):
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
        embed = self.create_embed(title='',
                                  description='',
                                  timestamp=ctx.message.created_at,
                                  colour=self.blue)

        # FIXME создать список кортежей и итерироваться по ним.
        roles = [role.mention for role in user.roles][1:][::-1]
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name='ID:', value=user.id, inline=False)
        embed.add_field(name='Имя:', value=user.name, inline=False)
        embed.add_field(name='Имя на сервере:', value=user.display_name, inline=False)
        embed.add_field(name='Роли:', value=f'{" ".join(roles)}')
        embed.add_field(name='Вступил на сервер:',
                        value=f'{user.joined_at.strftime("%Y.%m.%d в %H:%M")}',
                        inline=False)
        embed.add_field(name='Создал аккаунт:',
                        value=f'*{user.created_at.strftime("%Y.%m.%d в %H:%M")}*',
                        inline=False)
        embed.set_footer(text='Посмотри $help',
                         icon_url=user.avatar_url)
        await ctx.send(embed=embed)

    @info.command(name='guild', aliases=['server', 'сервер', 'гильдия'],
                  description=description.GUILD_INFO, help=description.GUILD_INFO)
    async def receives_guild_info(self, ctx):
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
                 f':online:{statuses[0]}\n:status_offline:{statuses[1]}\n:Idle_Status:{statuses[2]}\n:DND_Status:{statuses[3]}\n:invisible:{statuses[4]}',
                 False),
                ('**Каналы:**', f'{channels[0]}\n{channels[1]}\n{channels[2]}', False),
                ('**Владелец:**', f'{ctx.guild.owner.name}', False),
                ('**Регион:**', f'{ctx.guild.region}', False),
                ('**Уровень проверки:**', f'{ctx.guild.verification_level}', False),
                ('**Дата создания:**', f'{ctx.guild.created_at.strftime("%Y.%m.%d в %H:%M")}', False)]
        for name, value, inline in data:
            embed.add_field(name=name, value=value, inline=inline)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @info.command(name='roles', aliases=['роли'], description=description.ROLE_INFO, help=description.ROLE_INFO)
    async def receives_role_info(self, ctx):
        embed = self.create_embed(title=f'Роли сервера {ctx.guild.name}',
                                  description='',
                                  timestamp=ctx.message.created_at,
                                  colour=self.orange)
        roles = '\n'.join([role.mention for role in ctx.guild.roles][::-1])
        data = [(f'**Всего:**', f'{len(ctx.guild.roles)}', True),
                (f'**Дерево ролей:**', f'{roles}', False)]
        for name, value, inline in data:
            embed.add_field(name=name, value=value, inline=inline)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Info загружен.')


def setup(client):
    client.add_cog(Info(client))
