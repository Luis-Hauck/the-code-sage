import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from pymongo.errors import DuplicateKeyError

from src.database.models.user import UserModel, UserStatus
from src.utils.repositories.user_repository import UserRepository

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    """Fixture para criar um mock do banco de dados e da coleção."""
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.users = mock_collection
    return mock_db


@pytest.fixture
def sample_user() -> UserModel:
    """Fixture para criar um usuário de exemplo reutilizável."""
    return UserModel(
        _id=12345,  #
        username='Gandalf',
        joined_at=datetime.now(),
        xp=1000,
        coins=500,
        equipped_item_id=None,
        role_ids=[],
        inventory={'101': 2}
    )


async def test_create_user_success(mock_db, sample_user):
    """Testa se o método create chama insert_one com os dados corretos."""
    user_repo = UserRepository(db=mock_db)
    result = await user_repo.create(user_model=sample_user)

    # 1. ASSERT FORTE: Verifica não apenas o retorno, mas a chamada ao mock.
    assert result is True
    expected_data = sample_user.model_dump(by_alias=True)
    mock_db.users.insert_one.assert_awaited_with(expected_data)


async def test_create_user_duplicate_key(mock_db, sample_user):
    """Testa se o método create retorna False em caso de DuplicateKeyError."""
    mock_db.users.insert_one.side_effect = DuplicateKeyError("duplicate key error")
    user_repo = UserRepository(db=mock_db)
    result = await user_repo.create(user_model=sample_user)
    assert result is False


async def test_get_by_id_success(mock_db, sample_user):
    """Testa se get_by_id retorna um UserModel quando o usuário é encontrado."""
    mock_db.users.find_one.return_value = sample_user.model_dump(by_alias=True)
    user_repo = UserRepository(db=mock_db)
    result = await user_repo.get_by_id(sample_user.user_id)

    assert isinstance(result, UserModel)
    assert result.user_id == sample_user.user_id
    # 2. USA `assert_awaited_with` para corrotinas
    mock_db.users.find_one.assert_awaited_with({'_id': sample_user.user_id})


async def test_get_by_id_not_found(mock_db):
    """Testa se get_by_id retorna None quando o usuário não é encontrado."""
    mock_db.users.find_one.return_value = None
    user_repo = UserRepository(db=mock_db)
    result = await user_repo.get_by_id(99999)
    assert result is None


@pytest.mark.parametrize("status_to_set", [UserStatus.BANNED, UserStatus.INACTIVE])
async def test_update_status(mock_db, status_to_set):
    """Testa se update_status chama update_one com o filtro e $set corretos."""
    # Assumindo que a função agora retorna `result.acknowledged`
    mock_db.users.update_one.return_value = MagicMock(acknowledged=True)
    user_repo = UserRepository(db=mock_db)
    result = await user_repo.update_status(user_id=12345, status=status_to_set)

    assert result is True
    mock_db.users.update_one.assert_awaited_with(
        {'_id': 12345},
        {'$set': {'status': status_to_set}}
    )


# 3. USA `parametrize` para combinar vários testes em um só
@pytest.mark.parametrize("user_id, xp, coins", [
    (123, 50, 100),  # Caso de sucesso normal
    (456, -10, -20),  # Caso com valores negativos
    (789, 0, 0)  # Caso com valores zero
])
async def test_add_xp_coins(mock_db, user_id, xp, coins):
    """Testa se add_xp_coins chama update_one com o operador $inc correto."""
    mock_db.users.update_one.return_value = MagicMock(modified_count=True)
    user_repo = UserRepository(db=mock_db)
    result = await user_repo.add_xp_coins(user_id=user_id, xp=xp, coins=coins)

    # A lógica da função real não chama update_one se os valores forem 0
    if xp == 0 and coins == 0:
        assert result is True
        mock_db.users.update_one.assert_not_awaited()
    else:
        assert result is True
        mock_db.users.update_one.assert_awaited_with(
            {'_id': user_id},
            {'$inc': {'xp': xp, 'coins': coins}}
        )


async def test_add_xp_coins_database_error(mock_db):
    """Testa quando ocorre um erro no banco de dados."""
    mock_db.users.update_one.side_effect = Exception("Erro de conexão")
    user_repo = UserRepository(db=mock_db)
    result = await user_repo.add_xp_coins(user_id=5, xp=50, coins=100)
    assert result is False



