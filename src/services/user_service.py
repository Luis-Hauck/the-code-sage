import logging
from typing import Tuple, List
import discord
from src.database.models.user import UserModel, UserStatus
from src.repositories.user_repository import UserRepository
from src.repositories.item_repository import ItemRepository
from src.database.models.item import ItemType

logger = logging.getLogger(__name__)

class UserService:
    """Regras de negócio relacionadas ao usuário: economia, inventário e sincronização."""
    def __init__(self, user_repo: UserRepository, item_repo: ItemRepository):
        """Inicializa o serviço de usuário.

        Args:
            user_repo (UserRepository): Repositório de usuários.
            item_repo (ItemRepository): Repositório de itens.
        """
        self.user_repo = user_repo
        self.item_repo = item_repo

    async def sync_guild_users(self, guild_members: List[discord.Member]) -> Tuple[int, int]:
        """
        Sincroniza a lista de membros do Discord com o banco de dados.
        Retorna: (total_criados, total_ignorados)
        """
        count = 0
        ignored = 0

        # O Service detém a regra de negócio (ignorar bots, dados padrão, etc)
        for member in guild_members:
            if member.bot:
                continue

            # Verifica existência (O Service usa seu próprio repo, sem expor para fora)
            exists = await self.user_repo.get_by_id(member.id)

            if not exists:
                # O Service sabe como instanciar um User
                new_user = UserModel(
                    _id=member.id,
                    username=member.name,
                    xp=0,
                    coins=0,
                    inventory={},
                    equipped_item_id=None,
                    status=UserStatus.ACTIVE,
                    joined_at=member.joined_at,
                    role_ids=[]
                )
                await self.user_repo.create(new_user)
                count += 1
            else:
                ignored += 1

        return count, ignored

    async def buy_item(self, user_id: int, item_id: int, item_quantity: int) -> Tuple[bool, str]:
        """Processa a compra de um item.

        Args:
            user_id (int): ID do usuário.
            item_id (int): ID do item a ser comprado.
            item_quantity (int): Quantidade de itens a serem comprados.

        Returns:
            Tuple[bool, str]: (True/False, Mensagem)
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

        # 1. Adiciona o item ao inventário PRIMEIRO
        success_add = await self.user_repo.add_item_to_inventory(user_id, item_id, item_quantity)

        if not success_add:
            return False, "Erro ao entregar item. A compra foi cancelada."

        # 2. Desconta as moedas
        new_balance = await self.user_repo.add_xp_coins(user_id=user_id,
                                                        xp=0,
                                                        coins=-total_price
                                                        )

        if not new_balance:
            # CRÍTICO: Rollback manual (remover item) se a cobrança falhar
            await self.user_repo.remove_item_from_inventory(user_id, item_id, item_quantity)
            logger.error(f"Rollback executado para usuário {user_id} na compra do item {item_id}")
            return False, 'Erro ao processar o pagamento! A compra foi cancelada.'

        logger.info(f"User {user_id} comprou {item.name} - {item_quantity}X por {total_price} moeda(s)")
        return True, f'Você comprou {item.name} com sucesso!'

    async def equip_item(self, user_id: int, item_id: int) -> Tuple[bool, str]:
        """Equipa um item que está no inventário do usuário.

        Args:
            user_id (int): ID do usuário que equipará o item.
            item_id (int): ID do item a ser equipado.

        Returns:
            Tuple[bool, str]: (True/False, mensagem)
        """

        user = await self.user_repo.get_by_id(user_id)
        item = await self.item_repo.get_by_id(item_id)
        if not user:
            return False, f"Usuário não encontrado."

        # Busca detalhes do item para ver o TIPO
        item = await self.item_repo.get_by_id(item_id)
        if not item:
            return False, "Item não existe no banco de dados."

        # Verifica se ele realmente tem o item (usando str conversion se necessário, mas mantendo int por enquanto)
        # O modelo UserModel define inventory como Dict[int, int]
        if item_id not in user.inventory:
            return False, "Você não possui este item. Compre-o primeiro!"

        # Verificamos se é do tipo "equipável"
        if item.item_type != ItemType.EQUIPPABLE:
            return False, f"O item '{item.name}' não pode ser equipado (Tipo: {item.item_type.value})."


        # Equipa o item
        await self.user_repo.equip_item(user_id, item_id)

        return True, "Item equipado com sucesso!"

    async def unequip_item(self,user_id: int) -> Tuple[bool, str]:
        """Desequipa o item atualmente equipado pelo usuário.

        Args:
            user_id (int): ID do usuário que terá o item desequipado.

        Returns:
            Tuple[bool, str]: (True/False, mensagem)
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False, f"Usuário não encontrado para desequipar o item."

        await self.user_repo.unequip_item(user_id)
        return True, "Item desequipado com sucesso!"
