import logging
import asyncio
from typing import List, Dict, Any, Tuple, Set
from datetime import datetime

from src.repositories.user_repository import UserRepository
from src.database.models.user import UserModel, UserStatus

logger = logging.getLogger(__name__)

class UserService:
    """
    Serviço responsável pela lógica de negócio relacionada a usuários.
    """
    def __init__(self, user_repo: UserRepository):
        """
        Inicializa o UserService.

        Args:
            user_repo (UserRepository): Repositório de usuários.
        """
        self.user_repo = user_repo

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
            new_user = UserModel(
                _id=user_id,
                username=member['name'],
                xp=0,
                coins=0,
                inventory={},
                equipped_item_id=None,
                status=UserStatus.ACTIVE,
                joined_at=member['joined_at'],
                role_ids=[]
            )
            new_users.append(new_user)

        return new_users, ignored_count
