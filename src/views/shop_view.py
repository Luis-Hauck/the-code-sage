import discord
from discord import ui

from src.utils.embeds import create_info_embed, create_error_embed
from src.services.economy_service import EconomyService
from src.database.models.item import ItemModel, ItemType


class ShopDropdown(ui.Select):
    """
    Componente de menu suspenso (Select) para listagem de itens da loja.

    Renderiza opções com nome, preço, breve descrição e um emoji indicando o tipo
    do item. Ao selecionar, aciona a compra via EconomyService.
    """
    def __init__(self, items: list[ItemModel], economy_service: EconomyService):
        """
        Inicializa o dropdown com uma lista de itens e o serviço de economia.

        Args:
            items (list[ItemModel]): Itens disponíveis para compra.
            economy_service (EconomyService): Serviço responsável por processar a compra.
        """
        self.economy_service = economy_service

        options = []
        for item in items:
            emoji = ''
            match item.item_type:
                case ItemType.CONSUMABLE:
                    emoji = '🧪'
                case ItemType.EQUIPPABLE:
                    emoji = '🛡️'
                case ItemType.ROLE:
                    emoji = '📜'

            options.append(discord.SelectOption(
                label=item.name,
                description=f"💰 {item.price} | {item.description[:50]}",
                value=str(item.item_id),
                emoji=emoji
            ))

        super().__init__(
            placeholder="Selecione um item para comprar...",
            min_values=1,
            max_values=1,
            options=options
        )


    async def callback(self, interaction: discord.Interaction):
        """
        Manipula a seleção do usuário no dropdown e tenta realizar a compra.

        Args:
            interaction (discord.Interaction): Interação do Discord que contém
                o usuário e o valor selecionado.

        Comportamento:
            - Lê o item selecionado.
            - Defer da resposta (ephemeral).
            - Chama EconomyService.buy_item e envia um embed de sucesso/erro.
        """

        # self.values é uma lista de strings com os values selecionados.
        selected_item_id = int(self.values[0])

        await interaction.response.defer(ephemeral=True)

        # Chama a lógica de negócio
        success, message = await self.economy_service.buy_item(
            user_id=interaction.user.id,
            item_id=selected_item_id,
            item_quantity=1
        )

        if success:
            successful_purchase_embed = create_info_embed(title='Compra realizada!', message=message)
            await interaction.followup.send(embed=successful_purchase_embed, ephemeral=True)
        else:
            purchase_error_embed = create_error_embed(title='Erro na compra', message=message)
            await interaction.followup.send(embed=purchase_error_embed, ephemeral=True)



class ShopView(ui.View):
    """
    View que agrega o dropdown da loja.

    Esta view é responsável por conter o componente ShopDropdown e manter o
    timeout desativado (persistente) para que os botões continuem interativos
    até serem manualmente removidos/desativados.
    """
    def __init__(self, items, economy_service: EconomyService):
        """
        Inicializa a view com os itens e o serviço de economia.

        Args:
            items (list[ItemModel]): Lista de itens disponíveis para compra.
            economy_service (EconomyService): Serviço utilizado pelo dropdown para efetuar compras.
        """
        super().__init__(timeout=None)
        if items:
            self.add_item(ShopDropdown(items, economy_service))