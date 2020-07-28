import discord
import description
from discord.ext import commands
from discord.ext.commands import BucketType
from config import settings, WHITELIST


def syntax(command):
    cmd = settings['prefix'] + str(command.aliases[0])  # команда
    aliases = ' '.join([f'``{alias}``' for alias in command.aliases])  # псевдонимы
    params = []
    for key, value in command.params.items():
        if key not in ['self', 'ctx']:
            params.append(f'[{key}]' if 'NoneType' in str(value) else f'<{key}>')
    return cmd, aliases, params


class Help(commands.Cog):

    def __init__(self, client):
        self._client = client
        self._client.remove_command('help')

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Help загружен.')

    async def custom(self, ctx, command):
        cmd, aliases, params = syntax(command)
        params = ' '.join(param for param in params)
        embed = discord.Embed(title=f'Команда {command.aliases[0]}',
                              description='',
                              colour=ctx.author.colour)
        embed.set_thumbnail(url=self._client.user.avatar_url)
        embed.add_field(name='🔔Псевдонимы:', value=aliases, inline=True)
        embed.add_field(name='📜Права:', value='command.permissions', inline=False)
        if params:
            embed.add_field(name='📄Пример:', value=f'{cmd} ``{params}``', inline=False)
        else:
            embed.add_field(name='📄Пример:', value=f'{cmd}')
        if command.description:
            embed.add_field(name='📃Описание:', value=command.description, inline=False)
        else:
            embed.add_field(name='📃Описание:', value='None', inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='help', aliases=['помощь', 'помогите', 'commands', 'хелп', 'команды'],
                      description=description.HELP, help='``Показывает основную информацию о команде.``')
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 30, type=BucketType.user)
    async def display_help(self, ctx, command: str = None):
        if command is None:
            embed = discord.Embed(title='Help(BETA)',
                                  description='***Добро пожаловать в Hydrargyrum help dialog***!',
                                  colour=discord.Colour.from_rgb(44, 47, 51))
            embed.set_thumbnail(url=self._client.user.avatar_url)
            cmds = list(self._client.commands)
            for cmd in cmds:
                if not cmd.hidden:
                    embed.add_field(name=cmd, value='cmd.help', inline=True)
            embed.set_footer(text=f'Команды {self._client.user.name}', icon_url=self._client.user.avatar_url)
            await ctx.send(embed=embed)
        else:
            if cmd := self._client.get_command(command):
                await self.custom(ctx, cmd)
            else:
                await ctx.send('Такой команды не существует')

    @display_help.after_invoke
    async def reset_help_cd(self, ctx):
        for role_id in WHITELIST:
            if role_id in [role.id for role in ctx.author.roles]:
                self.display_help.reset_cooldown(ctx)


def setup(client):
    client.add_cog(Help(client))
