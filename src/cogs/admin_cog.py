import discord
from discord import app_commands
from discord.ext import commands

import logging

from src.database.models.user import UserStatus, UserModel
from src.utils.helpers import is_mission_channel
from src.utils.embeds import MissionEmbeds, create_error_embed, create_info_embed

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
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_users(self, interaction: discord.Interaction):
        """
        Registra todos os membros atuais do server no banco de dados.
        Args:
            interaction (discord.Interaction): Interação do comando.
        """
        await interaction.response.defer(ephemeral=True)

        # Acessa o repo de usuários
        user_repo = self.bot.mission_service.user_repo

        count = 0
        ignored = 0

        # Varre todos os membros do servidor
        for member in interaction.guild.members:
            # se for um bot ignoramos
            if member.bot:
                continue

            user = UserModel(_id=member.id,
                    username=member.name,
                    xp=0,
                    coins=0,
                    inventory = {},
                    equipped_item_id = None,
                    status=UserStatus.ACTIVE,
                    joined_at=member.joined_at,
                    role_ids=[]
                             )
            # Verifica se já existe
            exists = await user_repo.get_by_id(member.id)
            if not exists:
                await user_repo.create(user)

                count += 1
            else:
                ignored += 1

        await interaction.followup.send(
            f"✅ Sincronização concluída!\n🆕 Cadastrados: {count}\n⏭️ Já existiam: {ignored}")



    @app_commands.command(name="ajustar_avaliacao",
                          description="[ADM] Ajusta o rank de uma missão.")
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
        if not is_mission_channel(interaction):
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