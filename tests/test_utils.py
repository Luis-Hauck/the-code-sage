import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command(name='enviar_mensagem')
async def enviar_mensagem(ctx:commands.Context):
    autor = ctx.author
    await ctx.reply(f'Olá {autor}')


@bot.command()
async def somar(ctx:commands.Context, val1:int, val2:int):
    soma = val1 + val2
    await ctx.reply(f'A soma de {val1} com {val2} é {soma}')

@bot.command()
async def responder_texto(ctx:commands.Context, *, texto):
    await ctx.reply(texto)


@bot.event
async def on_ready():
    print('Bot Ligado!')

bot.run(token=DISCORD_TOKEN