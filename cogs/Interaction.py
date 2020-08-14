import discord
import json
import requests
from config import WHITELIST
from phrases import *
from random import choice
from discord.ext import commands
import description


class Interaction(commands.Cog):

    def __init__(self, client):
        self._client = client
        self.blue = discord.Colour.blue()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Interaction загружен.')

    @commands.command(aliases=['clap'], description=description.PAT, help=description.PAT)
    @commands.cooldown(1, 30, type=commands.BucketType.user)
    async def pat(self, ctx, member: discord.Member):
        await ctx.message.delete()
        html = json.loads(requests.get('https://nekos.life/api/v2/img/pat').text)

        phrase = choice(pat_phrases).format(ctx.message.author.mention, member.mention)
        embed = discord.Embed(description=phrase,
                              colour=self.blue)
        embed.set_image(url=html['url'])
        await ctx.send(embed=embed)

    @pat.after_invoke
    async def reset_pat_cd(self, ctx):
        for role_id in WHITELIST:
            if role_id in [role.id for role in ctx.author.roles]:
                self.pat.reset_cooldown(ctx)

    @commands.command(aliases=['дать-леща'], description=description.SLAP, help=description.SLAP)
    @commands.cooldown(1, 30, type=commands.BucketType.user)
    async def slap(self, ctx, member: discord.Member):
        await ctx.message.delete()
        html = json.loads(requests.get('https://nekos.life/api/v2/img/slap').text)

        phrase = choice(slap_phrases).format(ctx.author.mention, member.mention)
        embed = discord.Embed(description=phrase,
                              colour=self.blue)
        embed.set_image(url=html['url'])
        await ctx.send(embed=embed)

    @slap.after_invoke
    async def reset_slap_cd(self, ctx):
        for role_id in WHITELIST:
            if role_id in [role.id for role in ctx.author.roles]:
                self.slap.reset_cooldown(ctx)


def setup(client):
    client.add_cog(Interaction(client))
