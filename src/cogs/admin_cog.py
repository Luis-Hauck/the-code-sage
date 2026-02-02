import discord
from discord import app_commands
from discord.ext import commands

import logging

from src.database.models.mission import EvaluationRank
from src.utils.helpers import is_mission_channel
from src.utils.embeds import MissionEmbeds, create_error_embed

logger = logging.getLogger(__name__)

class AdminCog(commands.Cog):
    """Comandos administrativos (sync e ajustes de avaliação)."""
    def __init__(self, bot):
        """Inicializa o Cog de Administração.

        Args:
            bot (commands.Bot): Instância principal do bot.
        """
        self.bot = bot

    @app_commands.command(name="sync_users", description="Registra todos os membros atuais do server no banco de dados.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_users(self, interaction: discord.Interaction):
        """
        Registra todos os membros atuais do server no banco de dados.
        Args:
            interaction (discord.Interaction): Interação do comando.
        """
        await interaction.response.defer(ephemeral=True)

        # Prepara os dados dos membros para o service
        members_data = [
            {
                "id": member.id,
                "name": member.name,
                "joined_at": member.joined_at,
                "bot": member.bot
            }
            for member in interaction.guild.members
        ]

        # Chama o UserService para sincronizar
        created, ignored = await self.bot.user_service.sync_guild_users(members_data)

        await interaction.followup.send(
            f"✅ Sincronização concluída!\n🆕 Cadastrados: {created}\n⏭️ Já existiam: {ignored}")



    @app_commands.command(name="ajustar_avaliacao",
                          description="[ADM] Ajusta o rank de uma missão.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(user='O usuário que será reavaliado.', novo_rank='Novo rank que  usuário vai receber!')
    async def adjust_rank(self, interaction: discord.Interaction, user:discord.Member, novo_rank: str):
        """Ajusta o rank da avaliação de um usuário (apenas Admin).

        Args:
            interaction (discord.Interaction): Interação do comando.
            user (discord.Member): Usuário que será reavaliado.
            novo_rank (str): Novo rank a ser aplicado.
        """
        # verifica se é uma Thread
        if not await is_mission_channel(interaction):
            return

        # Validação antecipada do Rank
        if not EvaluationRank.get_or_none(novo_rank):
            await interaction.response.send_message(
                embed=create_error_embed("Rank Inválido", f"O rank '{novo_rank}' não existe. Use: S, A, B, C, D, E."),
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Chamamos o service para ajustar o rank
        success, data = await self.bot.mission_service.adjust_evaluation(
            interaction.channel.id,
            user.id,
            novo_rank,
            interaction.guild
        )

        if success:
            success_adjust_rank_embed = MissionEmbeds.admin_adjustment(target_user=user,
                                                                       old_rank=data['old_rank'],
                                                                       new_rank=data['new_rank'],
                                                                       xp_diff=data['xp_diff'],
                                                                       coins_diff=data['coins_diff']
            )
            await interaction.followup.send(embed=success_adjust_rank_embed)
            logger.info(f'O usuário {user.display_name} teve o rank alterado de:\n '
                        f'{data["old_rank"]} para {data["new_rank"]}.\n'
                        f'Diferença de XP: {data["xp_diff"]}\n'
                        f'Diferença de Moedas: {data["coins_diff"]}')
        else:
            logger.error(f'Erro ao ajustar o rank da missão com id {interaction.channel.id}')
            await interaction.followup.send(embed=create_error_embed(title='Erro ao ajustar rank', message=data), ephemeral=True)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))