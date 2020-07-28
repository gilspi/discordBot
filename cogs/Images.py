import discord
import requests
import json
from config import WHITELIST
from discord.ext import commands
import description


class Images(commands.Cog):

    def __init__(self, client):
        self._client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Images загружен.')

    @commands.command(name='kitty', aliases=['cat'], description=description.CAT, help=description.CAT)
    @commands.cooldown(1, 30, type=commands.BucketType.user)
    async def show_kitty(self, ctx):
        # десериализует текст в объект Python
        await ctx.message.delete()
        html = json.loads(requests.get('https://nekos.life/api/v2/img/meow').text)

        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_image(url=html['url'])
        await ctx.send(embed=embed)

    @show_kitty.after_invoke
    async def reset_kitty_cd(self, ctx):
        for role_id in WHITELIST:
            if role_id in [role.id for role in ctx.author.roles]:
                self.show_kitty.reset_cooldown(ctx)

    @commands.command(name='dog', aliases=['doggie', 'bowwow'], description=description.DOG, help=description.DOG)
    @commands.cooldown(1, 30, type=commands.BucketType.user)
    async def show_dog(self, ctx):
        await ctx.message.delete()
        html = json.loads(requests.get('https://nekos.life/api/v2/img/woof').text)

        embed = discord.Embed(colour=discord.Colour.from_rgb(160, 82, 45))
        embed.set_image(url=html['url'])
        await ctx.send(embed=embed)

    @show_dog.after_invoke
    async def reset_dog_cd(self, ctx):
        for role_id in WHITELIST:
            if role_id in [role.id for role in ctx.author.roles]:
                self.show_dog.reset_cooldown(ctx)

    @commands.command(name='lizard', description=description.LIZARD, help=description.LIZARD)
    @commands.cooldown(1, 30, type=commands.BucketType.user)
    async def show_lizard(self, ctx):
        await ctx.message.delete()
        html = json.loads(requests.get('https://nekos.life/api/v2/img/lizard').text)

        embed = discord.Embed(colour=discord.Colour.dark_teal())
        embed.set_image(url=html['url'])
        await ctx.send(embed=embed)

    @show_lizard.after_invoke
    async def reset_lizard_cd(self, ctx):
        for role_id in WHITELIST:
            if role_id in [role.id for role in ctx.author.roles]:
                self.show_lizard.reset_cooldown(ctx)

    @commands.command(name='8ball', aliases=['Q&A'], description=description._8BALL, help=description._8BALL)
    @commands.cooldown(1, 30, type=commands.BucketType.user)
    async def send_8ball(self, ctx, *, question):
        await ctx.message.delete()
        html = json.loads(requests.get('https://nekos.life/api/v2/img/8ball').text)

        embed = discord.Embed(colour=discord.Colour.from_rgb(44, 35, 122),
                              description=f'Question: {question}\nAnswer:')
        embed.set_footer(text=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
        embed.set_image(url=html['url'])
        await ctx.send(embed=embed)

    @send_8ball.after_invoke
    async def reset_8ball_cd(self, ctx):
        for role_id in WHITELIST:
            if role_id in [role.id for role in ctx.author.roles]:
                self.send_8ball.reset_cooldown(ctx)


def setup(client):
    client.add_cog(Images(client))
