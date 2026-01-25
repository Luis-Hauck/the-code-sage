import discord
from discord import app_commands
from discord.ext import commands
import logging


from src.services.leveling_service import LevelingService
from src.repositories.user_repository import UserRepository
from src.repositories.item_repository import ItemRepository
from src.utils.embeds import UserEmbeds

logger = logging.getLogger(__name__)




class UserCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leveling_service: LevelingService = bot.leveling_service
        self.user_repo: UserRepository = bot.user_repo
        self.item_repo: ItemRepository = bot.item_repo

    @app_commands.command(name="perfil", description="Exibe o seu perfil.")
    async def view_profile(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        guild = interaction.guild
        user_data = await self.user_repo.get_by_id(user_id)

        current_level = self.leveling_service.calculate_level(user_data.xp)

        # Realizamos uma sincronização nos cargos
        await self.leveling_service.sync_roles(user_id=user_data.user_id,
                                                current_level=current_level,
                                                guild=guild)

        user_progress = self.leveling_service.get_user_progress(total_xp=user_data.xp)

        if user_data.equipped_item_id:
            equipped_item = await self.item_repo.get_by_id(user_data.equipped_item_id)
            equipped_item_name = equipped_item.name
        else:
            equipped_item_name = "Nenhum item equipado"

        profile_embed = UserEmbeds.view_profile(user_name=user_data.username,
                                        current_level=current_level,
                                        current_xp=user_progress['relative_xp'],
                                        xp_next_level=user_progress['needed_xp'],
                                        progress_percent=user_progress['percentage'],
                                        coin_balance=user_data.coins,
                                        equipped_item_name=equipped_item_name

        )
        await interaction.followup.send(embed=profile_embed)

async def setup(bot):
    await bot.add_cog(UserCog(bot))














