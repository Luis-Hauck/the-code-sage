import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.database.models.user import UserModel
from src.utils.repositories.user_repository import UserRepository, UserStatus

# Marca todos os testes neste arquivo para serem executados com asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_db():
    """Fixture para criar um mock do banco de dados"""
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.users = mock_collection
    return mock_db


@pytest.fixture
def sample_user():
    """Fixture para criar um usuário de exemplo"""
    return UserModel(
        _id=5,
        username='teste',
        joined_at=datetime.today(),
        xp=0,
        coins=100,
        equipped_item_id=None,
        role_ids=[],
        inventory=[]
    )


async def test_create_user_succes(mock_db, sample_user):
    """
    Testa se o método create cria o usuário
    """

    user_repo = UserRepository(db=mock_db)

    result = await user_repo.create(user_model=sample_user)

    assert result is True


async def test_create_user_failure(mock_db, sample_user):
    """Testa se o método create lida com erros corretamente"""
    mock_db.users.insert_one.side_effect = Exception("Erro no banco de dados")
    user_repo = UserRepository(db=mock_db)

    result = await user_repo.create(user_model=sample_user)

    assert result is False

async def test_update_status_success(mock_db, sample_user):
    """
    Testa se o método update_status funcioan corretamente
    """
    # Simula que 1 documento foi modificado
    mock_db.users.update_one.return_value = MagicMock(modified_count=1)
    user_repo = UserRepository(db=mock_db)
    result = await user_repo.update_status(user_id=sample_user.user_id, status=UserStatus.INACTIVE)
    assert result is True

async def test_update_status_failure(mock_db, sample_user):
    """
    Testa se o método update_status lida com erros corretamente.
    """
    # Simula que nenhum dcumento foi modificado
    mock_db.users.update_one.return_value = MagicMock(modified_count=0)
    user_repo = UserRepository(db=mock_db)
    result = await user_repo.update_status(user_id=sample_user.user_id, status=UserStatus.INACTIVE)
    assert result is False


async def test_add_xp_coins_success(mock_db):
    """
    Testa se método add_xp_coins funciona corretamente
    """
    # Simula que 1 documento foi modificado
    mock_db.users.update_one.return_value = MagicMock(modified_count=1)
    user_repo = UserRepository(db=mock_db)

    user_id = 5
    xp_to_add = 10.0
    coins_to_add = 10.0

    result = await user_repo.add_xp_coins(user_id=user_id, xp=xp_to_add, coins=coins_to_add)

    # Verifica o retorno
    assert result is True

    # Verifica se foi chamado corretamente
    mock_db.users.update_one.assert_called_once_with(
        {'_id': user_id},
        {'$inc': {'xp': xp_to_add, 'coins': coins_to_add}}
    )


async def test_add_xp_coins_failure(mock_db):
    """
    Testa se método add_xp_coins lida com erros corretamente.
    """
    # Simula que 1 documento foi modificado
    mock_db.users.update_one.return_value = MagicMock(modified_count=0)
    user_repo = UserRepository(db=mock_db)
    result = await user_repo.add_xp_coins(user_id=5, xp=10, coins=10)
    assert result is False


async def test_add_xp_coins_user_not_found(mock_db):
    """Testa quando o usuário não é encontrado (nenhum documento modificado)"""
    mock_db.users.update_one.return_value = MagicMock(modified_count=0)
    user_repo = UserRepository(db=mock_db)

    result = await user_repo.add_xp_coins(user_id=999, xp=50.0, coins=100.0)

    assert result is False


async def test_add_xp_coins_with_negative_values(mock_db):
    """Testa se funciona com valores negativos (remover XP/moedas)"""
    mock_db.users.update_one.return_value = MagicMock(modified_count=1)
    user_repo = UserRepository(db=mock_db)

    result = await user_repo.add_xp_coins(user_id=5, xp=-10.0, coins=-20.0)

    assert result is True
    mock_db.users.update_one.assert_called_once_with(
        {'_id': 5},
        {'$inc': {'xp': -10.0, 'coins': -20.0}}
    )


async def test_add_xp_coins_database_error(mock_db):
    """Testa quando ocorre um erro no banco de dados"""
    mock_db.users.update_one.side_effect = Exception("Erro de conexão")
    user_repo = UserRepository(db=mock_db)

    result = await user_repo.add_xp_coins(user_id=5, xp=50.0, coins=100.0)

    assert result is False


async def test_add_xp_coins_zero_values(mock_db):
    """Testa incremento com valores zero"""
    mock_db.users.update_one.return_value = MagicMock(modified_count=1)
    user_repo = UserRepository(db=mock_db)

    result = await user_repo.add_xp_coins(user_id=5, xp=0, coins=0)

    assert result is True
    mock_db.users.update_one.assert_called_once_with(
        {'_id': 5},
        {'$inc': {'xp': 0, 'coins': 0}}
    )



