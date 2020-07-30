import discord
from discord.ext import commands
from description import TRANSLATOR
from googletrans import Translator
from typing import Optional, List, Tuple


class Trans(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.translator = Translator()
        self.error = discord.Colour.red()
        self.orange = discord.Colour.orange()

    async def create_embed(self, description, field: List[Tuple] = None):
        embed_ = discord.Embed(description=description,
                               colour=self.orange)
        if field is not None:
            for name, value, inline in field:
                embed_.add_field(name=name, value=value, inline=inline)
        return embed_

    @commands.command(name='translate', aliases=['переведи'],
                      description=TRANSLATOR, help=TRANSLATOR)
    @commands.has_permissions(send_messages=True)
    async def translates(self, ctx, languages: Optional[str], *, text: Optional[str]):
        src, dest = languages.split('-')
        trans = self.translator.translate(src=src, dest=dest, text=text)
        embed = await self.create_embed(description='', field=[(f'{text}', trans.text, False)])
        embed.set_footer(text=dest)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Translator загружен')


def setup(client):
    client.add_cog(Trans(client))
