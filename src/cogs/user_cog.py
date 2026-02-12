import discord
from discord import app_commands
from discord.ext import commands
import logging

from src.services.user_service import UserService
from src.utils.embeds import UserEmbeds, create_error_embed, create_info_embed, InventoryEmbeds

logger = logging.getLogger(__name__)


class UserCog(commands.Cog):
    """Comandos de usuário (perfil, inventário e progresso)."""
    def __init__(self, bot):
        """Inicializa o Cog de usuários.

        Args:
            bot (commands.Bot): Instância principal do bot.
        """
        self.bot = bot
        self.user_service: UserService = bot.user_service

    @app_commands.command(name="perfil", description="Exibe o seu perfil.")
    async def view_profile(self, interaction: discord.Interaction):
        """Exibe o perfil do usuário atual (nível, progresso e saldo).

        Args:
            interaction (discord.Interaction): Interação do comando.
        """
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        guild = interaction.guild

        # Agora get_user_profile cuida de calcular nível, sync roles, etc.
        profile_data = await self.user_service.get_user_profile(user_id, guild)

        if not profile_data:
             await interaction.followup.send(embed=create_error_embed("Erro", "Perfil não encontrado."))
             return

        profile_embed = UserEmbeds.view_profile(
            user_name=profile_data['username'],
            current_level=profile_data['current_level'],
            current_xp=profile_data['current_xp'],
            xp_next_level=profile_data['xp_next_level'],
            progress_percent=profile_data['progress_percent'],
            coin_balance=profile_data['coin_balance'],
            equipped_item_name=profile_data['equipped_item_name']
        )
        await interaction.followup.send(embed=profile_embed)

    @app_commands.command(name='inventário', description='Mostra os itens no inventário')
    async def view_inventory(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        username, equipped_item_name, items = await self.user_service.get_user_inventory(interaction.user.id)

        if not username:
             await interaction.followup.send(embed=create_error_embed("Erro", "Usuário não encontrado."))
             return

        if not items:
            without_data_embed = create_error_embed(
                title='Seu inventário está vazio!',
                message='Você ainda não possui itens. Visite a loja!'
            )
            await interaction.followup.send(embed=without_data_embed)
            return

        embed = InventoryEmbeds.view_inventory(
            user_name=username,
            equipped_name=equipped_item_name,
            items_data=items
        )
        await interaction.followup.send(embed=embed)

    async def equip_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        user_id = interaction.user.id

        # Obtém inventário (ignoramos username/equipped_name aqui)
        _, _, items = await self.user_service.get_user_inventory(user_id)

        if not items:
            return []

        suggestions = []
        for item in items:
            # item agora tem 'id'
            if current.lower() in item['name'].lower():
                suggestions.append(
                    app_commands.Choice(name=item['name'], value=str(item['id']))
                )

        return suggestions[:25]

    @app_commands.command(name='equipar', description='Equipa um item do seu inventário')
    @app_commands.describe(item='Item a ser equipado')
    @app_commands.autocomplete(item=equip_autocomplete)
    async def equip_item(self, interaction: discord.Interaction, item: int):
        await interaction.response.defer(ephemeral=True)

        success, message = await self.user_service.equip_item(
            user_id=interaction.user.id,
            item_id=item
        )

        if success:
            embed = create_info_embed(title='Item equipado com sucesso!', message=message)
        else:
            embed = create_error_embed(title='Falha ao equipar o item', message=message)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name='desequipar', description='Desequipa o item atual')
    async def unequip_item(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        success, message = await self.user_service.unequip_item(interaction.user.id)

        if success:
            embed = create_info_embed(title='Item desequipado com sucesso!', message=message)
        else:
            embed = create_error_embed(title='Falha ao desequipar o item', message=message)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(UserCog(bot))
