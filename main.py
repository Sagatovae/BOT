import discord
from discord.ext import commands, tasks

import sqlite3
import json
from tabulate import tabulate

import re
import random
from config import settings

connection = sqlite3.connect('server.db')
cursor = connection.cursor()

intents = discord.Intents().all()
bot = commands.Bot(command_prefix=settings['PREFIX'], intents=intents)
int_pattern = re.compile(r'^\s*[-+]?\d+\s*$')


@bot.event
async def on_ready():
    print(f'Бот подключился как {bot.user.name}')
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        name TEXT,
        id INT,
        cash BIGINT,
        rep INT
    )""")

    for guild in bot.guilds:
        for member in guild.members:
            if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0, 0)")
        else:
            pass
    connection.commit()
@bot.event
async def on_member_join(member):
    if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
        cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0, 0)")
        connection.commit()
    else:
        pass

@bot.command(aliases = ['balance', 'cash'])
async def __balance(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send(embed = discord.Embed(
            description= f"""Баланс пользователя **{ctx.author}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]} :leaves:**"""
        ))
    else:
        await ctx.send(embed = discord.Embed(
        description= f"""Баланс пользователя **{member}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(member.id)).fetchone()[0]} :leaves:**"""
        ))
@bot.command(aliases = ['award'])
async def __award(ctx, member: discord.Member = None, amount: int = None):
    if member is None:
        await ctx.send(f"**{ctx.author}**, укажите пользователя, которому желаете выдать определенную сумму")
    else:
        if amount is None:
            await ctx.send(f"**{ctx.author}, укажите сумму, которую хотите выдать**")
        elif int(amount) < 1:
            await ctx.send(f"**{ctx.author}**, укажите сумму больше 1")
        else:
            cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(int(amount), member.id))
            connection.commit()

            await ctx.message.add_reaction('🔴')
            
# @bot.command(aliases = ['take'])
# async def __take(ctx, member: discord.Member = None, amount = None):
#     if member is None:
#         await ctx.send(f"**{ctx.author}**, укажите пользователя, у которого желаете отнять определенную сумму")
#     else:
#         if amount is None:
#             await ctx.send(f"**{ctx.author}, укажите сумму, которую хотите отнять**")
#         else:
#             cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(amount, member.id))
#             connection.commit()

#             await ctx.message.add_reaction('🔴')



@bot.command()
async def start(ctx):
    instructions = await ctx.send('Выберите ставку:')
    await instructions.add_reaction('🍎')
    await instructions.add_reaction('🍊')
    await instructions.add_reaction('🍇')
    await instructions.add_reaction('🍒')

    ctx.bot.game_choice = None  # Initialize the choice

    def check(reaction, user):
        return user == ctx.message.author and reaction.emoji in ['🍎', '🍊', '🍇', '🍒']

    reaction, user = await bot.wait_for('reaction_add', check=check)
    if reaction.emoji == '🍎':
        ctx.bot.game_choice = 1
    elif reaction.emoji == '🍊':
        ctx.bot.game_choice = 2
    elif reaction.emoji == '🍇':
        ctx.bot.game_choice = 3
    elif reaction.emoji == '🍒':
        ctx.bot.game_choice = 4
    # message = await ctx.send(instructions)
    # reactions = ['🍎', '🍊', '🍇', '🍒']
    # for reaction in reactions:
    #     await message.add_reaction(reaction)
    
@bot.command()
async def bet(ctx, bet):
    if ctx.bot.game_choice is None:
        await ctx.send('Используйте команду !start, чтобы начать игру.')
        return
    if ctx.message.author.bot:
            return

    if not int_pattern.match(bet):
        return await ctx.send("Ошибка! Поставьте ставку!")
    num = int(bet)
    if num <= 0:
        return await ctx.send("Число не может быть меньше или равно нулю!")
    return await ctx.send(f"Ставка: {num}")


# @bot.event
# async def on_reaction_add(reaction, user, ctx):
#     bet_number = None
#     if reaction.emoji == '🍎':
#         bet_number = 1
#     elif reaction.emoji == '🍊':
#         bet_number = 2
#     elif reaction.emoji == '🍇':
#         bet_number = 3
#     elif reaction.emoji == '🍒':
#         bet_number = 4

#     if bet_number is not None:
#         rand = random.randint(1, 4)

#         if bet_number == rand:
#             await ctx.send(f'{user.mention}, вы выиграли! Загаданное число: {rand}')
#         else:
#             await ctx.send(f'{user.mention}, вы проиграли! Загаданное число: {rand}')


@bot.command()
async def game(ctx, member: discord.Member = None):
    if ctx.bot.game_choice is None:
        await ctx.send('Используйте команду !start, чтобы начать игру.')
        return

    await ctx.send("Начало")

    rand = random.randint(1, 4)

    if member is None:
        member = ctx.author

    await ctx.send(f'Загаданное число: {rand}')

    if ctx.bot.game_choice == rand:
        cursor.execute("UPDATE users SET cash = cash + 20 WHERE id = {}".format(member.id))
        connection.commit()
        await ctx.send(f'{member.mention}, вы выиграли! Загаданное число: {rand}')
    else:
        cursor.execute("UPDATE users SET cash = cash - 20 WHERE id = {}".format(member.id))

        connection.commit()
        await ctx.send(f'{member.mention}, вы проиграли! Загаданное число: {rand}')
    

@bot.command
async def help(ctx):
    ctx.message.channel.send("тут будет инфа")


bot.run(settings['TOKEN'])