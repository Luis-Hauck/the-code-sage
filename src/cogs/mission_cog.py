import discord
from src.app.config import MISSION_CHANNEL_ID
from discord.ext import commands
from discord import app_commands
import asyncio

from src.services.mission_service import MissionService
from src.database.models.mission import EvaluationRank
from src.utils.embeds import MissionEmbeds, create_error_embed, create_info_embed

class MissionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = bot.mission_service


    @app_commands.command(name="avaliar", description='Avalia quem te ajudou na missão.')
    @app_commands.describe(aventureiro='Quem te ajudou?', rank='Rank de S a E')
    async def evaluate(self, interaction: discord.Interaction, aventureiro: discord.Member, rank: str):
        """
        Comando para avaliar o ajudante.
        :param interaction:
        :param aventureiro:
        :param rank:
        :return:
        """
        # verifica se é uma Thread
        if not isinstance(interaction.channel, discord.Thread) or not interaction.channel.parent_id == MISSION_CHANNEL_ID:
            wrong_channel_embed = create_error_embed(title='Você não pode usar esse comando aqui!',
                                                     message='Esse comando só pode ser usado dentro de uma missão'

            )
            await interaction.response.send_message(embed=wrong_channel_embed, ephemeral=True)
            return


        await interaction.response.defer()

        success, data = await self.service.evaluate_user(
            mission_id=interaction.channel.id,
            author_id=interaction.user.id,
            user_id=aventureiro.id,
            rank=rank,
            guild=interaction.guild
            )

        if success:
            succes_embed = MissionEmbeds.evaluation_success(
                target_user=aventureiro,
                rank=EvaluationRank.get_or_none(rank),
                xp=data['xp'],
                coins=data['coins']

            )
            mission_closed_embed = create_info_embed(title='A missão será encerrada!',
                                                     message='A missão será feechada e arquivada dentro de 2 minutos.'


            )

            await interaction.followup.send(embed=succes_embed)
            await interaction.followup.send(embed=mission_closed_embed)
            self.bot.loop.create_task(
                self.close_thread_task(interaction.channel, 120)
            )

        else:
            await interaction.followup.send(embed=create_error_embed(title='Erro ao avaliar', message=data), ephemeral=True)


    async def close_thread_task(self, thread: discord.Thread, delay: int):
        """
        Tarefa que espera X segundos e fecha a thread se ela ainda estiver aberta.
        """
        # Espera o tempo de delay
        await asyncio.sleep(delay)

        # Verifica se a thread ainda existe visualmente
        try:
            if thread.archived or thread.locked:
                return

        except Exception:
            return

        # Verificamos se a thread está fechada no banco de dados
        just_closed = await self.service.close_mission(thread.id)

        # Se retornou False, é porque alguém já fechou manualmente
        if not just_closed:
            return

        # Manda a mensagem que encerrou a thread
        try:
            embed = create_info_embed(title='Missão Encerrada!', message="🔒 Missão encerrada automaticamente.")
            await thread.send(embed=embed)

            # Tranca a thread no Discord
            await thread.edit(locked=True, archived=True, reason="Missão Concluída (Auto)")

        except Exception as e:
            print(f"Erro ao fechar thread visualmente: {e}")

async def setup(bot):
    await bot.add_cog(MissionCog(bot))