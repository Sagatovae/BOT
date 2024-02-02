# ИМПОРТЫ И ПЕРЕМЕННЫЕ
import discord
import datetime
from discord.ext import commands
from discord import embeds
from discord import Option
from discord.ext import commands, tasks
from discord.ui import View, Button


import sqlite3
import json
from tabulate import tabulate

import re
import random
import math
from config import settings
from collections import defaultdict  

connection = sqlite3.connect('server.db')
cursor = connection.cursor()

intents = discord.Intents().all()
bot = commands.Bot(command_prefix=settings['PREFIX'], intents=intents)
bot.remove_command('help')
int_pattern = re.compile(r'^\s*[-+]?\d+\s*$')
# КОНЕЦ ИМПОРТОВ И ПЕРЕМЕННЫХ

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

    await ctx.message.delete()
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
      
user_messages = {}
previous_message = None

class MyView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.button_clicked = set()
    
    @discord.ui.button(label="Нажми меня!", style=discord.ButtonStyle.primary, emoji="😎", disabled=False)
    async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in self.button_clicked:
            self.button_clicked.remove(user_id)
            button.label = f"Нажало: {len(self.button_clicked)}"
            await interaction.response.edit_message(view=self)
            await interaction.response.send_message("Вы больше не нажимаете на кнопку!")
        else:
            self.button_clicked.add(user_id)
            button.label = f"Нажало: {len(self.button_clicked)}"
            await interaction.response.edit_message(view=self)
            await interaction.response.send_message("Вы нажимаете на кнопку!")


@bot.slash_command(name='roulette', description='Рулетка')
async def roulette(ctx):
    global previous_message
    
    if previous_message:
        await previous_message.delete_original_message()

    instructions = await ctx.send('Да начнется игра:')
    view = MyView()
    button = view.children[0]
    button.disabled = False
    button.label = "Нажало: 0"
    previous_message = instructions
    await instructions.edit(view=view)

@bot.slash_command(name="bet", description='Ставка')
async def bet(ctx, bid: Option(int, name='bid', description='0(00) - 36', required=True), bet: Option(int, name='bet', description='Сумма ставки', required=True), member: discord.Member = None):
    global previous_message
    global user_messages

    if member is None:
        member = ctx.author

    balance = cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]
    
    if balance - bet > 0:
        valid_input = bid in [0, 00] or (0 < bid < 37)
        if valid_input:
            if ctx.author.id not in user_messages:
                user_messages[ctx.author.id] = f"{str(bid)} - {str(bet)}"
                cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(int(bet), member.id))
                view = MyView()
                button = view.children[0]
                button.disabled = False
                button.label = "Нажало: 0"
                if previous_message:
                    await previous_message.edit(content='Да начнется игра:', view=view)
                else:
                    previous_message = await ctx.send('Да начнется игра:', view=view)
            else:
                user_messages[ctx.author.id] += f"\n{str(bid)} - {str(bet)}"
                cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(int(bet), member.id))
            connection.commit()
            if previous_message:
                updated_text = previous_message.content
                for user_id, message in user_messages.items():
                    user = bot.get_user(user_id)
                    updated_text += f"\n\n**{user.name}:**\n{message}"

                await previous_message.edit(content=updated_text)
            else:
                await ctx.respond("Предыдущее сообщение не найдено.")
        else:
            await ctx.respond("Неверный ввод. Пожалуйста, введите число от 0 (00) до 36.")
    else:
        await ctx.respond("На вашем балансе недостаточно средств.")

# @bot.command()
# async def game(ctx, member: discord.Member = None):
#     if ctx.bot.game_choice is None:
#         await ctx.send('Используйте команду !start, чтобы начать игру.')
#         return
#     await ctx.send("Начало")

#     rand = random.randint(1, 4)

#     if member is None:
#         member = ctx.author

#     await ctx.send(f'Загаданное число: {rand}')

#     if ctx.bot.game_choice == rand:
#         cursor.execute("UPDATE users SET cash = cash + 20 WHERE id = {}".format(member.id))
#         connection.commit()
#         await ctx.send(f'{member.mention}, вы выиграли! Загаданное число: {rand}')
#     else:
#         cursor.execute("UPDATE users SET cash = cash - 20 WHERE id = {}".format(member.id))

#         connection.commit()
#         await ctx.send(f'{member.mention}, вы проиграли! Загаданное число: {rand}')
# КОНЕЦ ФУНКЦИЙ СВЯЗАННЫХ С РУЛЕТКОЙ    


# КОММАНДА !HELP 
@bot.command()
async def help(ctx):
    prefix = settings['PREFIX']
    commands = [
        {'name': 'help', 'value': 'Комманды бота (Эта комманда)'},
        {'name': 'roulette', 'value': 'Начало рулетки'},
        {'name': 'bet', 'value': 'Лот и ставка'},
        {'name': 'balance', 'value': 'Ваши деньги'},
        {'name': 'work', 'value': 'Выдает 200:leaves:. Работает каждые 30 секунд'},
        {'name': 'salary', 'value': 'Выдает 5000:leaves:. Работает каждые 24 часа'},
        {'name': 'award', 'value': 'Выдает выбранному пользователю определенное количество денег (Доступно только администраторам)'}
    ]

    emb = discord.Embed(title='Навигация по командам')
    for command in commands:
        emb.add_field(name=f'{prefix}{command["name"]}', value=command['value'], inline=False)

    await ctx.send(embed=emb)
    await ctx.message.delete()

# Функция для заработка
@commands.cooldown(1, 30, commands.BucketType.user)    
@bot.command()
async def work(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    cursor.execute("UPDATE users SET cash = cash + 200 WHERE id = {}".format(member.id))
    connection.commit()
    await ctx.send(f'{member.mention}, **вы получили 200 :leaves:**!')
    await ctx.message.delete()
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        retry_after = str(datetime.timedelta(seconds=error.retry_after)).split('.')[0]
        await ctx.send(f'**Вы устали! Приходите через {retry_after}**')

@commands.cooldown(1, 86400, commands.BucketType.user)    
@bot.command()
async def salary(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    cursor.execute("UPDATE users SET cash = cash + 5000 WHERE id = {}".format(member.id))
    connection.commit()
    await ctx.send(f'{member.mention}, **вы получили 5000 :leaves:**!')
    await ctx.message.delete()
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        retry_after = str(datetime.timedelta(seconds=error.retry_after)).split('.')[0]
        await ctx.send(f'**Следущая зарплата через {retry_after}**')

@bot.slash_command(name='gift', description='Подарить деньги')
async def gift(ctx, recipient: Option(str, name='получатель', description='Получатель', required=True), amount: Option(int, name='сумма', description='Сумма подарка', required=True)):
    recipient_member = None
    for member in ctx.guild.members:
        if member.name.lower() == recipient.lower():
            recipient_member = member
            break

    if recipient_member is None:
        await ctx.send(f"Указанный получатель не найден.")
    else:
        if amount < 1:
            await ctx.send(f"Укажите сумму подарка больше 1.")
        else:
            cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(gift, recipient_member.id))
            cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(gift, ctx.author.id))
            connection.commit()
            await ctx.send(f"Вы успешно подарили {amount} денег пользователю {recipient}.")
# Запуск бота
bot.run(settings['TOKEN'])
