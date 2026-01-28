import discord
from discord.ext import commands
from discord import app_commands
import random

from src.services.economy_service import EconomyService
from src.utils.embeds import ShopEmbeds
from src.views.shop_view import ShopView, create_error_embed
from src.app.config import MOD_LOG_CHANNEL_ID

class ShopCog(commands.Cog):
    """Comandos da loja (vitrine e compra de itens)."""
    def __init__(self, bot):
        """Inicializa o Cog da loja.

        Args:
            bot (commands.Bot): Instância do bot principal, usada para acessar repositórios e serviços.
        """
        self.bot = bot
        self.economy_service:EconomyService = bot.economy_service


    @app_commands.command(name="abrir_loja", description="[Admin] Cria a vitrine de itens neste canal")
    @app_commands.checks.has_permissions(administrator=True)
    async def open_shop(self, interaction: discord.Interaction):
        """Abre a vitrine da loja no canal atual.

        Args:
            interaction (discord.Interaction): Interação do comando.
        """
        await interaction.response.defer()

        # Buscamos 100 itens
        all_items = await self.economy_service.item_repo.get_all()

        if not all_items:
            mod_channel = interaction.guild.get_channel(MOD_LOG_CHANNEL_ID)
            error_embed = create_error_embed('Erro ao abrir a loja',
                                             'Nada encontrado no banco de dados.'
            )
            await mod_channel.send(embed=error_embed)
            return

        # Selecionamos 5 itens
        shop_items = random.sample(all_items, min(len(all_items), 5))

        # criamos a vitrine
        showcase_embed = ShopEmbeds.create_showcase()

        # gera o view
        view = ShopView(shop_items, self.economy_service)

        await interaction.followup.send(embed=showcase_embed, view=view)

async def setup(bot):
    await bot.add_cog(ShopCog(bot))