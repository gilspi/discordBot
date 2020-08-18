import discord
import asyncpg
import os
from discord.ext import commands
from config import settings, owner_role_id, deputy_role_id, admin_role_id
import json


def get_prefix(client, message):
    with open('prefixes.json') as f:
        prefixes = json.load(f)

    return prefixes[str(message.guild.id)]


client = commands.Bot(command_prefix=get_prefix)


@client.command(hidden=True)
@commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id)
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    await ctx.send('Load')


@client.command(hidden=True)
@commands.has_any_role(owner_role_id, deputy_role_id, admin_role_id)
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    await ctx.send('Reload')


@client.command(hidden=True)
@commands.has_any_role()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    await ctx.send('Unload')  # FIXME добавить embed для красоты


if __name__ == '__main__':
    for file in os.listdir('./cogs'):
        if file.endswith('.py'):
            client.load_extension(f'cogs.{file[:-3]}')

client.run(settings['token'])

# FIXME Сделать возможность создавать роль guild --> create_role(), редактировать и т.д.
# ack()
# FIXME slowmode_delay
"""Потом сделать файлы en и ru, там будут храниться фразы! Если регион сервера не СНГ, то бот будет на английском, иначе
на русском"""
