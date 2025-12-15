import logging
from typing import Tuple

from src.repositories.user_repository import UserRepository
from src.repositories.item_repository import ItemRepository
from src.database.models.item import ItemType

logger = logging.getLogger(__name__)

class EconomyService:
    def __init__(self, user_repo: UserRepository, item_repo: ItemRepository):
        self.user_repo = user_repo
        self.item_repo = item_repo

    async def buy_item(self, user_id: int, item_id: int, item_quantity: int) -> Tuple[bool, str]:
        """
        Processa a compra de um item
        :param user_id: ID do usuário;
        :param item_id: ID do item a ser comprado;
        :param item_quantity: Quantidade de itens a serem comprados;
        :return: (True/False, Mensagem)
        """

        # Buscamos os dados do item/usuário
        item = await self.item_repo.get_by_id(item_id)
        user = await self.user_repo.get_by_id(user_id)


        if not item:
            return False, f'Item {item_id} não encontrado.'

        if not user:
            return False, f'Usuário {user_id} não encontrado.'

        total_price = item.price * item_quantity

        # Verificamos se usuário tem dinheiro
        if user.coins < total_price:
            return False, f'Saldo insuficiente! O item {item.name} custa: {item.price}X{item_quantity}={total_price} moeda(s) e você tem {user.coins} moeda(s)'

        # Desconta as moedas
        new_balance = await self.user_repo.add_xp_coins(user_id=user_id,
                                                        xp=0,
                                                        coins=-total_price
                                                        )

        if not new_balance:
            return False, 'Erro ao processar a compra!'

        # Adiciona o item ao inventário
        await self.user_repo.add_item_to_inventory(user_id, item_id, item_quantity)

        logger.info(f"User {user_id} comprou {item.name} - {item_quantity}X por {total_price} moeda(s)")
        return True, f'Voces comprou {item.name} com sucesso!'

    async def equip_item(self, user_id: int, item_id: int) -> Tuple[bool, str]:
        """
        Equipa um item que está no inventário
        :param user_id: ID do usuário para equipar o item;
        :param item_id: ID do item a ser equipado;
        :return: (True/False, Mensagem)
        """

        user = await self.user_repo.get_by_id(user_id)
        item = await self.item_repo.get_by_id(item_id)
        if not user:
            return False, f"Usuário não encontrado."

        # Busca detalhes do item para ver o TIPO
        item = await self.item_repo.get_by_id(item_id)
        if not item:
            return False, "Item não existe no banco de dados."

        # Verifica se ele realmente tem o item
        if item_id not in user.inventory:
            return False, "Você não possui este item. Compre-o primeiro!"

        # Verificamos se é do tipo "equipável"
        if item.item_type != ItemType.EQUIPPABLE:
            return False, f"O item '{item.name}' não pode ser equipado (Tipo: {item.item_type.value})."


        # Equipa o item
        await self.user_repo.equip_item(user_id, item_id)

        return True, "Item equipado com sucesso!"

    async def unequip_item(self,user_id: int, item_id: int) -> Tuple[bool, str]:
        """
        Desequipa um item equipado
        :param user_id: ID do usuário para equipar o item;
        :param item_id: ID do item a ser equipado;
        :return: (True/False, Mensagem).
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False, f"Usuário não encontrado."

        if user.equipped_item_id !=  item_id :
            return False, f'Você não possuí item equipado.'

        await self.user_repo.unequip_item(user_id)
        return True, "Item desequipado com sucesso!"







