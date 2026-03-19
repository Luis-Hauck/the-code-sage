import logging
from typing import Tuple


from src.repositories.item_repository import ItemRepository
from src.services.user_service import UserService

logger = logging.getLogger(__name__)

class EconomyService:
    """Regras de economia: compras e manipulação de itens equipáveis."""
    def __init__(self, user_service: UserService, item_repo: ItemRepository):
        """Inicializa o serviço de economia.

        Args:
            user_service (UserService): Serviço de usuário para manipular saldo/inventário.
            item_repo (ItemRepository): Repositório de itens (para consu
        """
        self.user_service = user_service
        self.item_repo = item_repo

    async def buy_item(self, user_id: int, item_id: int, item_quantity: int) -> Tuple[bool, str]:
        """Processa a compra de um item.

        Args:
            user_id (int): ID do usuário.
            item_id (int): ID do item a ser comprado.
            item_quantity (int): Quantidade de itens a serem comprados.

        Returns:
            Tuple[bool, str]: (True/False, Mensagem)
        """

        # Buscamos os dados do item
        item = await self.item_repo.get_by_id(item_id)

        if not item:
            return False, f'Item {item_id} não encontrado.'

        total_price = item.price * item_quantity

        # Verificamos se usuário tem saldo suficiente
        has_funds = await self.user_service.has_balance(user_id, total_price)

        if not has_funds:
            return False, f'Saldo insuficiente! O item custa {total_price}.'

        # Realiza a transação
        # Debita moedas
        debit_success = await self.user_service.debit_coins(user_id, total_price)
        if not debit_success:
            return False, 'Erro ao processar o pagamento!'

        # Adiciona o item
        add_success = await self.user_service.add_item_to_inventory(user_id, item_id, item_quantity)
        if not add_success:
            # Alterar logica para comprar e debitar moedas
            logger.error(f"ERRO CRÍTICO: User {user_id} pagou {total_price} mas o item {item_id} não foi adicionado!")
            return False, 'Erro ao entregar o item. Contate o suporte.'

        logger.info(f"User {user_id} comprou {item.name} - {item_quantity}X por {total_price} moeda(s)")
        return True, f'Você comprou {item.name} com sucesso!'



