# ИМПОРТЫ И ПЕРЕМЕННЫЕ

import discord
import datetime
from discord.ext import commands
from discord import embeds
from discord import Option
from discord.ext import commands, tasks

import sqlite3
import json
from tabulate import tabulate

import re
import random
from config import settings
from collections import defaultdict  

connection = sqlite3.connect('server.db')
cursor = connection.cursor()

intents = discord.Intents().all()
bot = commands.Bot(command_prefix=settings['PREFIX'], intents=intents)
bot.remove_command('help')
int_pattern = re.compile(r'^\s*[-+]?\d+\s*$')

# КОНЕЦ ИМПОРТов И ПЕРЕМЕННЫХ

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



# НАЧАЛО ФУНКЦИЙ СВЯЗАННЫХ С БАЛАНСОМ    
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
@commands.has_permissions(administrator = True)
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

# КОНЕЦ ФУНКЦИЙ СВЯЗАННЫХ С БАЛАНСОМ    
    
  
previous_message = None
user_messages = {}  # Словарь для хранения сообщений каждого пользователя

@bot.command()
async def startgame(ctx):
    global previous_message
    instructions = await ctx.send('Да начнется игра:')
    previous_message = instructions

@bot.command()
async def add_text(ctx, *, new_text):
    global previous_message
    global user_messages

    if ctx.author.id not in user_messages:
        user_messages[ctx.author.id] = new_text
    else:
        user_messages[ctx.author.id] += f"\n{new_text}"

    await ctx.message.delete()  # Удаляем сообщение пользователя

    if previous_message:
        updated_text = previous_message.content
        for user_id, message in user_messages.items():
            user = bot.get_user(user_id)
            updated_text += f"\n\n**{user.name}:**\n{message}"

        await previous_message.edit(content=updated_text)
    else:
        await ctx.send("Предыдущее сообщение бота не найдено.")



@bot.slash_command(name="sgame", description='Описание команды')
async def sgame(ctx, foo: Option(str, #тип данных ввода
                                 name='роль', #имя опции (необязательно)
                                 description='Bar', #описание опции
                                 required=True)): #обязательность введения параметра для команды
    pass


@bot.command()
async def bet(ctx, bet):
    # if ctx.bot.game_choice is None:
    #     start_message = await ctx.send('Используйте команду !start, чтобы начать игру.')
    message = await ctx.send(f"@{ctx.message.author.name} {bet}")
    await message.edit(content='Ставка: {bet}')
    if ctx.message.author.bot:
        return

    if not int_pattern.match(bet):
        return await ctx.send("Ошибка! Поставьте ставку!")
    num = int(bet)
    if num <= 0:
        return await ctx.send("Число не может быть меньше или равно нулю!")
    return await ctx.send(f"Ставка: {num}")


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
# КОНЕЦ ФУНКЦИЙ СВЯЗАННЫХ С РУЛЕТКОЙ    


# КОММАНДА !HELP 
@bot.command(pass_context = True)
async def help(ctx):
    emb = discord.Embed(title = 'Навигация по коммандам')
    emb.add_field(name= '{}start'.format(settings['PREFIX']), value = 'Начало рулетки')

    await ctx.send(embed = emb)
    
@bot.command()
async def work(ctx, member: discord.Member = None):
    cursor.execute("UPDATE users SET cash = cash + 200 WHERE id = {}".format(member.id))
    connection.commit()
    await ctx.send(f'{member.mention}, вы получили 200 деняк')

bot.run(settings['TOKEN'])
    