import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.database.models.user import UserModel
from src.utils.repositories.user_repository import UserRepository, UserStatus

# Marca todos os testes neste arquivo para serem executados com asyncio
pytestmark = pytest.mark.asyncio

async def test_create_user_succes():
    """
    Testa se o método create cria o usuário
    """

    # simula nossa coleção do banco de dados
    mock_collection = AsyncMock()

    # Criamos o mock do objeto 'db' que tem o atributo 'users'
    mock_db = MagicMock()
    mock_db.users = mock_collection

    # modelo de usuario que vamos testar
    user_to_create = UserModel(
        _id=5,
        username='teste',
        joined_at=datetime.today(),
        xp=0,
        coins=0,
        role_ids=[],
        inventory=[]

    )

    user_repo = UserRepository(db=mock_db)

    result = await user_repo.create(user_model=user_to_create)

    assert result is True





