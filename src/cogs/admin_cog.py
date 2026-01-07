import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from src.database.models.user import UserStatus


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sync_users", description=" egistra todos os membros atuais do server no banco de dados.")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_users(self, interaction: discord.Interaction):
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

            # Verifica se já existe
            exists = await user_repo.get_by_id(member.id)
            if not exists:
                await user_repo.create_user(
                    user_id=member.id,
                    username=member.name,
                    xp=0,
                    coin=0,
                    inventory = {},
                    equipped_item_id = None,
                    status=UserStatus.ACTIVE,
                    joined_at=datetime.now(),
                    role_ids=[]
                )

                count += 1
            else:
                ignored += 1

        await interaction.followup.send(
            f"✅ Sincronização concluída!\n🆕 Cadastrados: {count}\n⏭️ Já existiam: {ignored}")


async def setup(bot):
    await bot.add_cog(AdminCog(bot))