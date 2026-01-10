import discord
from src.app.config import MOD_LOG_CHANNEL_ID
from discord.ext import commands
from discord import app_commands
import asyncio
import logging

from src.database.models.mission import EvaluationRank
from src.utils.embeds import MissionEmbeds, create_error_embed, create_info_embed
from src.utils.helpers import is_mission_channel

logger = logging.getLogger(__name__)

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
        if not is_mission_channel(interaction):
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
            embed = create_info_embed(title='Missão Encerrada!', message="🔒 A Missão foi encerrada e arquivada!")
            await thread.send(embed=embed)

            # Tranca a thread no Discord
            await thread.edit(locked=True, archived=True, reason="Missão Concluída (Auto)")

        except Exception as e:
            print(f"Erro ao fechar thread visualmente: {e}")

    @app_commands.command(name="solicitar_revisao",
                          description="Reporta a insatisfação do Rank da missão do Aventureiro")
    @app_commands.describe(motivo='Explique o por que o rank da missão está errado')
    async def review_mission(self, interaction: discord.Interaction, motivo: str):
        """
        Comando para solicitar a revisão do rank.
        :param interaction: Objeto do discord.Interaction
        :param motivo: Motivo para abrir a solicitação
        """
        # verifica se é uma Thread
        if not await is_mission_channel(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        success, data = await self.bot.mission_service.report_evaluation(interaction.channel.id,
                                                                         interaction.user.id,
                                                                         motivo)

        if success:
            # Passamos o canal de logs da moderação
            mod_channel = interaction.guild.get_channel(MOD_LOG_CHANNEL_ID)

            if mod_channel:
                embed_report = MissionEmbeds.mission_report(mission_id=interaction.channel.id,
                                                            mission_title=interaction.channel.name,
                                                            reporter_id=interaction.user.id,
                                                            reporter_name=interaction.user.display_name,
                                                            current_rank=data['current_rank'],
                                                            reason=motivo
                                                            )
                await mod_channel.send(embed=embed_report)

            confirmation_report_embed = MissionEmbeds.report_confirmation()

            await interaction.followup.send(embed=confirmation_report_embed)
            logger.info(f'Sucesso ao reportar a missão {interaction.channel.id}.')
        else:
            await interaction.followup.send(embed=create_error_embed(title='Erro ao reportar', message=data),
                                            ephemeral=True)
            logger.error(f'Canal de moderações não encontrado: {MOD_LOG_CHANNEL_ID}')

    @app_commands.command(name="encerrar_missao",
                          description="Encerra a missão e arquiva o canal (Use caso tenha resolvido sozinho).")
    async def close_mission_command(self, interaction: discord.Interaction):
        """
        Permite que o dono da missão encerre o canal manualmente.
        """
        # Verifica se é uma Thread de missão
        if not await is_mission_channel(interaction):
            return

        # Verifica se quem chamou é o DONO da missão (ou um Admin)
        if interaction.user.id != interaction.channel.owner_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=create_error_embed(title="Sem permissão",
                                         message="Apenas o dono da missão ou um Admin podem encerrá-la."),
                ephemeral=True
            )
            return
        # Executa o encerramento
        await interaction.response.send_message(
            embed=create_info_embed(
                title="A Missão Vai sSr Encerrada!",
                message=f"O aventureiro {interaction.user.mention} decidiu encerrar esta missão.\nO canal será arquivado!."
            )
        )
        logger.info(f"O usuário {interaction.user.id} encerrou a missão {interaction.channel.id} manualmente.")
        self.bot.loop.create_task(self.close_thread_task(interaction.channel, 5))


async def setup(bot):
    await bot.add_cog(MissionCog(bot))