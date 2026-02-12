import logging
import asyncio
from typing import List, Dict, Any, Tuple, Set, Optional
from datetime import datetime

from src.repositories.user_repository import UserRepository
from src.repositories.item_repository import ItemRepository
from src.services.leveling_service import LevelingService
from src.database.models.user import UserModel, UserStatus
from src.database.models.item import ItemType

logger = logging.getLogger(__name__)

class UserService:
    """
    Serviço responsável pela lógica de negócio relacionada a usuários.
    """
    def __init__(self, user_repo: UserRepository, item_repo: ItemRepository = None, leveling_service: LevelingService = None):
        """
        Inicializa o UserService.

        Args:
            user_repo (UserRepository): Repositório de usuários.
            item_repo (ItemRepository, optional): Repositório de itens.
            leveling_service (LevelingService, optional): Serviço de nivelamento.
        """
        self.user_repo = user_repo
        self.item_repo = item_repo
        self.leveling_service = leveling_service

    async def get_user_profile(self, user_id: int, guild) -> Optional[Dict[str, Any]]:
        """
        Retorna os dados completos do perfil do usuário.

        Args:
            user_id (int): ID do usuário.
            guild: Objeto Guild para sincronização de cargos.

        Returns:
            Optional[Dict[str, Any]]: Dados do perfil ou None se usuário não encontrado.
        """
        user_data = await self.user_repo.get_by_id(user_id)
        if not user_data:
            return None

        if self.leveling_service:
            current_level = self.leveling_service.calculate_level(user_data.xp)
            # Sincroniza cargos
            await self.leveling_service.sync_roles(user_id=user_data.user_id,
                                                   current_level=current_level,
                                                   guild=guild)
            user_progress = self.leveling_service.get_user_progress(total_xp=user_data.xp)
        else:
            # Fallback caso leveling_service não esteja injetado (ex: testes unitários simples)
            current_level = 0
            user_progress = {'relative_xp': 0, 'needed_xp': 100, 'percentage': 0}

        equipped_item_name = "Nenhum item equipado"
        if user_data.equipped_item_id and self.item_repo:
            equipped_item = await self.item_repo.get_by_id(user_data.equipped_item_id)
            if equipped_item:
                equipped_item_name = equipped_item.name

        return {
            "username": user_data.username,
            "current_level": current_level,
            "current_xp": user_progress['relative_xp'],
            "xp_next_level": user_progress['needed_xp'],
            "progress_percent": user_progress['percentage'],
            "coin_balance": user_data.coins,
            "equipped_item_name": equipped_item_name
        }

    async def get_user_inventory(self, user_id: int) -> Tuple[Optional[str], Optional[str], List[Dict[str, Any]]]:
        """
        Retorna os dados do inventário do usuário.

        Returns:
            Tuple: (username, equipped_item_name, items_list)
        """
        user_data = await self.user_repo.get_by_id(user_id)
        if not user_data:
            return None, None, []

        equipped_item_name = "Nenhum item equipado"
        if user_data.equipped_item_id and self.item_repo:
            equipped_item = await self.item_repo.get_by_id(user_data.equipped_item_id)
            if equipped_item:
                equipped_item_name = equipped_item.name

        items_for_display = []
        if self.item_repo and user_data.inventory:
            for item_id, quantity in user_data.inventory.items():
                item = await self.item_repo.get_by_id(item_id)
                if item:
                    items_for_display.append({
                        'id': item.item_id,
                        'name': item.name,
                        'qty': quantity,
                        'type': item.item_type.value,
                        'description': item.description
                    })

        return user_data.username, equipped_item_name, items_for_display

    async def equip_item(self, user_id: int, item_id: int) -> Tuple[bool, str]:
        """
        Equipa um item que está no inventário do usuário.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False, "Usuário não encontrado."

        if not self.item_repo:
             return False, "Serviço de itens indisponível."

        item = await self.item_repo.get_by_id(item_id)
        if not item:
            return False, "Item não existe no banco de dados."

        # Verificação robusta para chaves int/str
        str_item_id = str(item_id)
        inventory_keys_str = {str(k) for k in user.inventory.keys()}

        if str_item_id not in inventory_keys_str:
             return False, "Você não possui este item. Compre-o primeiro!"

        if item.item_type != ItemType.EQUIPPABLE:
            return False, f"O item '{item.name}' não pode ser equipado (Tipo: {item.item_type.value})."

        await self.user_repo.equip_item(user_id, item_id)
        return True, "Item equipado com sucesso!"

    async def unequip_item(self, user_id: int) -> Tuple[bool, str]:
        """
        Desequipa o item atualmente equipado pelo usuário.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False, "Usuário não encontrado para desequipar o item."

        await self.user_repo.unequip_item(user_id)
        return True, "Item desequipado com sucesso!"

    async def sync_guild_users(self, members_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Sincroniza os usuários da guilda com o banco de dados.

        Busca todos os IDs existentes, filtra os novos, e insere em lote.

        Args:
            members_data (List[Dict]): Lista de dicionários com dados dos membros (id, name, joined_at, bot).

        Returns:
            Tuple[int, int]: (users_created_count, users_ignored_count)
        """
        if not members_data:
            return 0, 0

        # Busca IDs existentes no banco (Set[int])
        existing_ids = await self.user_repo.get_all_ids()

        # Executa o processamento pesado na thread
        new_users, ignored_count = await asyncio.to_thread(self._process_users_sync, members_data, existing_ids)

        created_count = 0
        if new_users:
            created_count = await self.user_repo.create_many(new_users)

        return created_count, ignored_count

    def _process_users_sync(self, members_data: List[Dict], existing_ids: Set[int]) -> Tuple[List[UserModel], int]:
        """
        Processamento síncrono (CPU-bound) para filtrar e criar modelos de usuário.
        Executado em thread separada para não bloquear o event loop.
        """
        new_users = []
        ignored_count = 0

        # Filtra bots e processa
        for member in members_data:
            if member.get('bot', False):
                continue

            user_id = member['id']
            if user_id in existing_ids:
                ignored_count += 1
                continue

            # Cria o modelo para o novo usuário
            joined_at = member.get('joined_at') or datetime.utcnow()
            new_user = UserModel(
                _id=user_id,
                username=member['name'],
                xp=0,
                coins=0,
                inventory={},
                equipped_item_id=None,
                status=UserStatus.ACTIVE,
                joined_at=joined_at,
                role_ids=[]
            )
            new_users.append(new_user)

        return new_users, ignored_count
