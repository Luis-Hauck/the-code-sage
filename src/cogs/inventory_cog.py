import discord
from discord.ext import commands
from discord import app_commands

from src.services.economy_service import EconomyService
from utils.embeds import create_error_embed, create_info_embed, InventoryEmbeds

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy_service:EconomyService = bot.economy_service

    async def equip_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:

        user_id = interaction.user.id

        # 2. Buscamos o usuário no banco para ver o inventário dele
        user_data = await self.economy_service.user_repo.get_by_id(user_id)

        if not user_data or not user_data.inventory:
            return []  # Se não tem inventário, não sugere nada

        # Sugere com base no que está no inventário do user
        sugestoes = []

        for item_id in user_data.inventory:
            item = await self.economy_service.item_repo.get_by_id(item_id)

            # Se o item existe E o nome dele bate com o que o usuário está digitando
            if item and current.lower() in item.name.lower():
                sugestoes.append(
                    app_commands.Choice(name=item.name, value=str(item.item_id))
                )

        return sugestoes[:25]

    @app_commands.command(name='equipar', description='Equipa um item do seu inventário')
    @app_commands.describe(item='Item a ser equipado')
    @app_commands.autocomplete(item=equip_autocomplete)
    async def equip_item(self, interaction: discord.Interaction, item: int):
        await interaction.response.defer(ephemeral=True)

        sucess, message = await self.economy_service.equip_item(
            user_id=interaction.user.id,
            item_id=item)


        embed = create_info_embed(title='Item equipado com sucesso!', message='Bora juntar mais moedas para comprar mais ;)') if sucess \
            else create_error_embed(title='Falha ao equipar o item', message=message)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name='desequipar', description='Desequipa o item atual e manda para inventário')
    async def unequip_item(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        sucess, message = await self.economy_service.unequip_item(interaction.user.id)

        embed = create_info_embed(title='Item desequipado com sucesso!', message='Bora juntar mais moedas para comprar mais um ;)') if sucess \
            else create_error_embed(title='Falha ao desequipar o item', message=message)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name='inventário', description='Mostra os itens no inventário')
    async def view_inventory(self, interaction:discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Buscamos dados do user
        user_data = await self.economy_service.user_repo.get_by_id(interaction.user.id)

        if not user_data or not user_data.inventory:
            without_data_embed = create_error_embed(title='Seu inventário está vazio! Ou você não existe? :)',
                                                    message='Não possível acessar os seus itens.'
                                                    )
            await interaction.followup.send(embed=without_data_embed)
            return

        # Verificamos se tem um item equipado
        equipped_item_name = "Nenhum item equipado"
        if user_data.equipped_item_id:
            equipped_item = await self.economy_service.item_repo.get_by_id(user_data.equipped_item_id)
            equipped_item_name = equipped_item.name


        items_for_display = []

        for item_id, quantity in user_data.inventory.items():
            item = await self.economy_service.item_repo.get_by_id(item_id)
            items_for_display.append({
                'name': item.name,
                'qty': quantity,
                'type': item.item_type.value,
                'description': item.description
            })

        embed = InventoryEmbeds.view_inventory(user_name=user_data.username,
                                               equipped_name=equipped_item_name,
                                               items_data=items_for_display)
        await interaction.followup.send(embed=embed)









async def setup(bot):
    await bot.add_cog(InventoryCog(bot))



