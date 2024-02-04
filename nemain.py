# ИМПОРТЫ И ПЕРЕМЕННЫЕ
import discord
import datetime
from discord.ext import commands
from discord import embeds
from discord import Option
from discord.ext import commands, tasks
from discord.ui import View, Button
import colorsys


import sqlite3
from tabulate import tabulate

import re
import random
from config import settings
from collections import defaultdict  

import asyncio

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
        msg = await ctx.send(embed = discord.Embed(
            description= f"""Баланс пользователя **{ctx.author}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]} :leaves:**"""
        ))
    else:
        msg = await ctx.send(embed = discord.Embed(
            escription= f"""Баланс пользователя **{member}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(member.id)).fetchone()[0]} :leaves:**"""
        ))
    await asyncio.sleep(5)
    await msg.delete()


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
    
    @discord.ui.button(label="Готовность", style=discord.ButtonStyle.primary, emoji="✅", disabled=False)
    async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in self.button_clicked:
            self.button_clicked.remove(user_id)
            button.label = f"Готовы: {len(self.button_clicked)}"
            await interaction.response.edit_message(view=self)
        else:
            if user_id in user_bets:
                self.button_clicked.add(user_id)
                button.label = f"Нажало: {len(self.button_clicked)}"
                await interaction.response.edit_message(view=self)
            else:
                msg = await interaction.response.send_message("Сделайте ставку.")
                await asyncio.sleep(5)
                await msg.delete()


game_ended = False

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


# @bot.command()
# async def startgame(ctx):
#     embed = discord.Embed(title='Переливающийся embed')
#     embed.add_field(name='Поле 1', value='Значение 1')
#     embed.add_field(name='Поле 2', value='Значение 2')
#     embed.add_field(name='Поле 3', value='Значение 3')

#     message = await ctx.send(embed=embed)

#     colors = ['#FFFFFF', '#000000']
#     index = 0

#     while True:
#         color_start = colors[index]
#         color_end = colors[(index + 1) % len(colors)]
#         index = (index + 1) % len(colors)

#         for i in range(101):
#             ratio = i / 100.0
#             rgb_start = tuple(int(color_start[i:i+2], 16) for i in (1, 3, 5))
#             rgb_end = tuple(int(color_end[i:i+2], 16) for i in (1, 3, 5))

#             rgb = [int((1 - ratio) * rgb_start[j] + ratio * rgb_end[j]) for j in range(3)]
#             color = discord.Color.from_rgb(rgb[0], rgb[1], rgb[2])

#             embed.color = color
#             await message.edit(embed=embed)

#             await asyncio.sleep(0.5)

# Функция для заработка
@commands.cooldown(1, 30, commands.BucketType.user)    
@bot.command()
async def work(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    cursor.execute("UPDATE users SET cash = cash + 200 WHERE id = {}".format(member.id))
    connection.commit()
    await ctx.send(f'{member.mention}, **вы получили 200! Ваш баланс составляет {cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]} :leaves:**')
    await ctx.message.delete()
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        retry_after = str(datetime.timedelta(seconds=error.retry_after)).split('.')[0]
        msg = await ctx.send(f'**Вы устали! Приходите через {retry_after}**')
        await asyncio.sleep(5)
        await msg.delete()
@commands.cooldown(1, 48200, commands.BucketType.user)    
@bot.command()
async def salary(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    cursor.execute("UPDATE users SET cash = cash + 5000 WHERE id = {}".format(member.id))
    connection.commit()
    await ctx.send(f'{member.mention}, **вы получили 5000! Ваш баланс составляет {cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]} :leaves:**')
    await ctx.message.delete()
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        retry_after = str(datetime.timedelta(seconds=error.retry_after)).split('.')[0]
        msg = await ctx.send(f'**Следущая зарплата через {retry_after}**')
        await asyncio.sleep(5)
        await msg.delete()
@bot.slash_command(name='gift', description='Подарить деньги')
async def gift(ctx, recipient: Option(str, name='получатель', description='Получатель', required=True), amount: Option(int, name='сумма', description='Сумма подарка', required=True), reason: Option(str, name='комментарий', description='Комментарий', required=False)):
    await ctx.defer()
    numbers = ''.join(c if c.isdigit() else ' ' for c in recipient).split()
    member = ''.join(numbers)
    if amount < 1:
        await ctx.respond(f"**Укажите сумму подарка больше 1:leaves:**")
    else:
        cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, member))
        cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(amount, ctx.author.id))
        connection.commit()
        if reason:
            msg = await ctx.respond(f"**{ctx.author.mention}, вы успешно подарили {amount} пользователю {recipient} по причине: {reason}. Ваш баланс составляет {cursor.execute('SELECT cash FROM users WHERE id = {}'.format(ctx.author.id)).fetchone()[0]} :leaves:.**")
        else:
            msg = await ctx.respond(f"**{ctx.author.mention}, вы успешно подарили {amount} пользователю {recipient}. Ваш баланс составляет {cursor.execute('SELECT cash FROM users WHERE id = {}'.format(ctx.author.id)).fetchone()[0]} :leaves:.**")
        await asyncio.sleep(5)
        await msg.delete()
            

user_bets = {}

class MyModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Bid 0(00) - 36"))
        self.add_item(discord.ui.InputText(label="Bet"))

    async def callback(self, interaction: discord.Interaction):
        bid = self.children[0].value
        bet = self.children[1].value

        embed = discord.Embed(title="Modal Results")
        embed.add_field(name="Bid 0(00) - 36", value=bid)
        embed.add_field(name="Bet", value=bet)

        message = await interaction.response.fetch_message()
        await message.edit(content="Рулетка началась:", embed=embed)


@bot.slash_command(name='roulette', description='Рулетка')
async def roulette(ctx):
    await ctx.defer()

    modal = MyModal(title="Modal")
    await ctx.send_modal(modal)


@bot.slash_command(name="bet", description='Ставка')
async def bet(ctx, member: discord.Member = None):
    global previous_message, user_bets
    if member is None:
        member = ctx.author

    modal = MyModal(title="Modal")
    await ctx.send_modal(modal)

    def check(interaction: discord.Interaction):
        return interaction.user == ctx.author and interaction.message == interaction.message

    try:
        interaction = await bot.wait_for("interaction", check=check, timeout=60.0)
        bid = interaction.data["values"]["Bid 0(00) - 36"]
        bet = interaction.data["values"]["Bet"]

        embed = discord.Embed(color=discord.Color.green())
        balance = cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]
        if balance - bet > 0:
            if bet >= 25:  # Ограничение в ставке в 25 шекелей
                valid_input = int(bid) in [0, 00] or (0 < int(bid) < 37)
                if valid_input:
                    if ctx.author.id not in user_bets:
                        user_bets[ctx.author.id] = {}

                    if bid not in user_bets[ctx.author.id]:
                        user_bets[ctx.author.id][bid] = 0

                    user_bets[ctx.author.id][bid] += bet

                    if len(user_bets[ctx.author.id]) <= 3:
                        cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(int(bet), member.id))
                        connection.commit()

                        if previous_message:
                            await ctx.defer()
                            updated_text = previous_message.content
                            for user_id, bets in user_bets.items():
                                user = bot.get_user(user_id)
                                bet_messages = "\n".join([f"{str(bid)} - {str(total_bet)}" for bid, total_bet in bets.items()])
                                updated_text += f"\n\n**{user.name}:**\n{bet_messages}"
                            await previous_message.edit(content=updated_text)
                            smt = await ctx.respond("обработка...")
                            await smt.delete()
                        else:
                            msg = await ctx.send("Предыдущее сообщение не найдено.")
                    else:
                        msg = await ctx.send("Вы уже сделали максимальное количество ставок.")
                else:
                    msg = await ctx.send("Неверный ввод. Пожалуйста, введите число от 0 (00) до 36.")
            else:
                msg = await ctx.send("Минимальная ставка составляет 25:leaves:")
        else:
            msg = await ctx.respond("Бедняжка")
        await asyncio.sleep(2)
        await msg.delete()
        await ctx.defer()
        smt = await ctx.respond("обработка...")
        await smt.delete()
    except asyncio.TimeoutError:
        await ctx.send("Время ожидания истекло.")

@bot.slash_command(name="start", description='Старт')
async def start(ctx, member: discord.Member = None):
    await ctx.defer()
    global previous_message

    if member is None:
        member = ctx.author

    if previous_message:
        rand = random.choice(['00', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36'])
        updated_text = previous_message.content
        updated_text = updated_text.replace("Да начнется игра:", f"Загаданное число: {str(rand)}")
        updated_text = updated_text.replace("Нажало: 0", "")
        updated_text = updated_text.replace("Нажало: 1", "")

        bet_messages = []
        for user_id, bets in user_bets.items():
            user = bot.get_user(user_id)
            if user is not None:
                user_bet_messages = []
                total_winnings = 0
                for bid, bet in bets.items():
                    winnings = 0
                    if str(bid) == str(rand):
                        winnings = bet * 36
                        cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(winnings, user_id))
                    user_bet_messages.append(f"Число: {bid}")
                    total_winnings += winnings
                if user_bet_messages:
                    user_bet_messages_str = "\n".join(user_bet_messages)
                    bet_messages.append(f"**{user.name}:**\n{user_bet_messages_str}\nОбщий выигрыш: {total_winnings} :leaves:")
                smt = await ctx.respond("обработка...")
                await smt.delete()                
        if bet_messages:
            bet_messages_str = "\n\n".join(bet_messages)
            updated_text += f"\n\n{bet_messages_str}"
        else:
            await ctx.respond("Ни один игрок не сделал ставку или не нажал на кнопку.")

        await previous_message.edit(content=updated_text, view=None)
        user_bets.clear()  # Очищаем словарь с ставками после вывода результатов

        await asyncio.sleep(8)
        await previous_message.delete()

    else:
        await ctx.respond("Предыдущее сообщение не найдено.")

# Запуск бота
bot.run(settings['TOKEN'])