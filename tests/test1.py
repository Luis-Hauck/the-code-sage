import discord
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

# Recebe todas as permissões
intents = discord.Intents.all()

bot = commands.Bot('/', intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print('Iniciando')


@bot.event
async def on_member_join(member:discord.Member):
    await member.send(f'Olá seja bem-vindo ao canal {member.name}')


@bot.event
async def on_thread_create(thread: discord.Thread):
    creator = thread.owner
    if thread.parent_id == 1402409945672060928:
        try:

            print(f'Novo topico criado por {creator}')
            starter_message = await thread.fetch_message(thread.id)
            print(starter_message)
            minha_embed = discord.Embed(
                title='# Post Criado',
                description=f'Enigma;;;............... {starter_message.content}',
                color=discord.Color.from_rgb(88, 55, 250)

            )
            imagem = discord.File(r"D:\Projects\the-code-sage\assets\images\img.png", "img.png")
            minha_embed.set_image(url='attachment://img.png')
            await starter_message.reply(embed=minha_embed, file=imagem)

        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            await thread.send(f'`{creator.name} é preciso colocar uma descrição')


@bot.tree.command()
async def ola(interact: discord.Interaction):
    await interact.response.send_message(f'Olá, tudo bem {interact.user.name}?')


@bot.tree.command()
async def avaliar(interact: discord.Interaction, recebedor_nota: str, nota: float):
    if isinstance(nota, float):
        thread = bot.get_channel(1409232904248365187)
        await interact.response.send_message(f'{recebedor_nota} teve nota: {nota}')
        await interact.followup.send(f'O post será fechado!')
        await thread.edit(archived=True, locked=True)


DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

bot.run(DISCORD_TOKEN)
