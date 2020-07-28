import json
import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from discord.ext.commands import errors
from config import WHITELIST, desc_errors, owner_role_id, deputy_role_id, admin_role_id
from db import Database
import exceptions


class Shop(commands.Cog):
    def __init__(self, client):
        self._client = client
        self.db = Database()
        self.error = discord.Colour.red()  # Цвет embed ошибки

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Shop загружен.')

    async def displays_error(self, ctx, description):
        embed = discord.Embed(description=description,
                              colour=self.error)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    def create_embed(self, title, description, isthumbnail: bool = True):
        embed = discord.Embed(title=title,
                              description=description,
                              colour=discord.Colour.from_rgb(255, 154, 0))
        if isthumbnail:
            embed.set_thumbnail(url=self._client.user.avatar_url)
        return embed

    async def insert_into_shops(self, ctx, title, description):
        self.db.insert_many('shops',
                            {'gid': ctx.guild.id,
                             'name': title,
                             'description': description})
        embed = self.create_embed(f'Магазин {title}', description)
        await ctx.send(embed=embed, delete_after=10)
        await ctx.send('Пора добавлять товары в магазин.', delete_after=10)

    @commands.command(name='create-shop', aliases=['new-market', 'build-store'])
    @commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id)
    async def creates_a_store(self, ctx, title: str, description: str = 'Добро пожаловать в Hydrargyrum Hype Shop.'):
        shop = self.db.select_one('shops',
                                  ('id',),
                                  {'gid': ctx.guild.id,
                                   'name': title})
        if not shop:
            if len(title) < 3:
                raise errors.BadArgument
            else:
                await self.insert_into_shops(ctx, title, description)
        self.db.commit()

    @creates_a_store.error
    async def creates_a_store_error(self, ctx, error):
        if isinstance(error, errors.MissingAnyRole):
            await self.displays_error(ctx, desc_errors['miss_any_role'])
        if isinstance(error, errors.MissingRequiredArgument):
            await self.displays_error(ctx, desc_errors['miss_req_arg'])
        if isinstance(error, errors.BadArgument):
            await self.displays_error(ctx, desc_errors['need_more'])

    @commands.command(name='add-product', aliases=['add-item', 'добавить-продукт'])
    @commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id)
    async def adds_product(self, ctx, title: str, price: int, *, name: str):
        if price < 0 or len(name) < 3:
            raise errors.BadArgument
        else:
            sid = self.db.select_one('shops',
                                     ('id',),
                                     {'gid': ctx.guild.id,
                                      'name': title})  # [0]
            if not sid:
                raise exceptions.ShopNotFound
            else:
                item = self.db.select_one('products',
                                          ('id',),
                                          {'gid': ctx.guild.id,
                                           'sid': sid[0],
                                           'name': name})
                if not item:
                    self.db.insert_many('products',
                                        {'gid': ctx.guild.id,
                                         'sid': sid[0],
                                         'price': price,
                                         'name': name})

                    with open('prefixes.json') as f:
                        prefixes = json.load(f)
                    prefix = prefixes[str(ctx.guild.id)]
                    
                    embed = self.create_embed(title='Товар добален.', description='', isthumbnail=False)
                    embed.set_footer(text=f'Чтобы увидеть товары, введи {prefix}shop {title}',
                                     icon_url=ctx.author.avatar_url)
                    await ctx.send(embed=embed, delete_after=10)
            self.db.commit()

    @adds_product.error
    async def adds_product_error(self, ctx, error):
        if isinstance(error, errors.MissingAnyRole):
            await self.displays_error(ctx, desc_errors['miss_any_role'])
        if isinstance(error, errors.MissingRequiredArgument):
            await self.displays_error(ctx, desc_errors['miss_req_arg'])
        if isinstance(error, errors.BadArgument):
            await self.displays_error(ctx, desc_errors['need_more+'])
        if isinstance(error, exceptions.ShopNotFound):
            await self.displays_error(ctx, desc_errors['shop_not_found'])

    @commands.command(name='shop', aliases=['market', 'store', 'магазин'])
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 5, type=BucketType.user)
    async def display_shop(self, ctx, title: str):
        sid, description = self.db.select_one('shops',
                                              ('id', 'description'),
                                              {'gid': ctx.guild.id,
                                               'name': title})
        products = self.db.select_many('products',
                                       ('name', 'price'),
                                       {'gid': ctx.guild.id,
                                        'sid': sid})
        if not sid:
            raise exceptions.ShopNotFound
        else:
            embed = self.create_embed(title, description)
            for product in products:
                name, price = product
                embed.add_field(name=f'Название: __``{name}``__', value=f'Цена: **``{price}``**', inline=False)
            await ctx.send(embed=embed)

    @display_shop.error
    async def display_shop_error(self, ctx, error):
        if isinstance(error, errors.MissingRequiredArgument):
            await self.displays_error(ctx, desc_errors['miss_req_arg'])
        if isinstance(error, exceptions.ShopNotFound):
            await self.displays_error(ctx, desc_errors['shop_not_found'])

    @display_shop.after_invoke
    async def reset_display_shop_cd(self, ctx):
        for role_id in WHITELIST:
            if role_id in [role.id for role in ctx.author.roles]:
                self.display_shop.reset_cooldown(ctx)


def setup(client):
    client.add_cog(Shop(client))
