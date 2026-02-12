import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument

from src.database.models.user import UserModel, UserStatus
from src.repositories.user_repository import UserRepository

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
        inventory={101: 2}
    )


async def test_create_user_success(mock_db, sample_user):
    """Testa se o método create chama insert_one com os dados corretos."""
    user_repo = UserRepository(db=mock_db)
    result = await user_repo.create(user_model=sample_user)

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
    mock_db.users.update_one.return_value = MagicMock(matched_count=1)
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
async def test_add_xp_coins(mock_db, sample_user, user_id, xp, coins):
    """Testa se add_xp_coins chama update_one com o operador $inc correto."""
    user_repo = UserRepository(db=mock_db)

    # Configuração para quando os valores são 0 (chama get_by_id -> find_one)
    if xp == 0 and coins == 0:
        mock_db.users.find_one.return_value = sample_user.model_dump(by_alias=True)

        result = await user_repo.add_xp_coins(user_id=user_id, xp=xp, coins=coins)

        assert isinstance(result, UserModel)
        mock_db.users.find_one_and_update.assert_not_awaited()
        mock_db.users.find_one.assert_awaited()

    # Configuração para quando há valores (chama find_one_and_update)
    else:
        # find_one_and_update retorna o documento atualizado (dicionário)
        mock_db.users.find_one_and_update.return_value = sample_user.model_dump(by_alias=True)

        result = await user_repo.add_xp_coins(user_id=user_id, xp=xp, coins=coins)

        assert isinstance(result, UserModel)  # O repositório retorna o objeto, não True
        mock_db.users.find_one_and_update.assert_awaited_with(
            {'_id': user_id},
            {'$inc': {'xp': xp, 'coins': coins}},
            return_document=ReturnDocument.AFTER
        )


async def test_add_xp_coins_database_error(mock_db):
    """Testa quando ocorre um erro no banco de dados."""
    mock_db.users.update_one.side_effect = Exception("Erro de conexão")
    user_repo = UserRepository(db=mock_db)
    result = await user_repo.add_xp_coins(user_id=5, xp=50, coins=100)
    assert result is None


# USA `parametrize` para combinar vários testes em um só
@pytest.mark.parametrize("user_id, item_id, quantity", [
    (123, 50, 100),  # Caso de sucesso normal
    (456, 268, 6),  # Caso com valores negativos
    (789, 588, 0)  # Caso com valores zero
])

async def test_add_item_to_inventory(mock_db, user_id, item_id, quantity):
    """Testa o funcionamento de adicionar um item ao inventário"""

    mock_db.users.update_one.return_value = MagicMock(modified_count=True)
    user_repo = UserRepository(db=mock_db)

    result = await user_repo.add_item_to_inventory(user_id=user_id, item_id=item_id, quantity=quantity)

    assert result is True

    # Se a quantidade for zero, verificamos se o DB NÃO foi chamado.
    if quantity == 0:
        mock_db.users.update_one.assert_not_awaited()
    # Senão, verificamos se o DB FOI chamado com os argumentos corretos.
    else:
        mock_db.users.update_one.assert_awaited_with(
            {'_id': user_id},
            {'$inc': {f'inventory.{item_id}': quantity}}
        )

async def test_equip_item_success(mock_db):
    """
    Testa o sucesso: O usuário existe, tem o item e o equipa.
    """
    # Simulamos que o MongoDB encontrou 1 documento e modificou 1.
    mock_db.users.update_one.return_value = MagicMock(matched_count=1, modified_count=1)
    user_repo = UserRepository(db=mock_db)

    # Passamos os IDs
    result = await user_repo.equip_item(user_id=12345, item_id=101)

    assert result is True
    mock_db.users.update_one.assert_awaited_with(
        {
            '_id': 12345,
            'inventory.101': {'$gt': 0}
        },
        {'$set': {'equipped_item_id': 101}}
    )


async def test_equip_item_already_equipped(mock_db):
    """
    Testa o caso onde o item já estava equipado.
    Cenário: matched_count=1 (encontrou e tem o item), modified_count=0 (nada mudou).
    """
    # Encontrou o documento (matched=1), mas o valor já era esse (modified=0)
    mock_db.users.update_one.return_value = MagicMock(matched_count=1, modified_count=0)
    user_repo = UserRepository(db=mock_db)


    result = await user_repo.equip_item(user_id=12345, item_id=101)


    assert result is True

async def test_remove_all_item_from_inventory(mock_db, sample_user):
    """Testa a função remove_item_from_inventory quando removemos todos os itens do inventário"""

    sample_user.inventory = {101: 1}

    mock_db.users.find_one.return_value = sample_user.model_dump(by_alias=True)

    mock_db.users.update_one.return_value = MagicMock(modified_count=1)

    user_repo = UserRepository(db=mock_db)

    result = await user_repo.remove_item_from_inventory(user_id=sample_user.user_id, item_id=101, quantity=1)

    assert result is True

    mock_db.users.update_one.assert_awaited_with(
        {'_id': sample_user.user_id},
        {'$unset': {f'inventory.{101}': ''}}
    )

async def test_remove_item_from_inventory(mock_db, sample_user):
    """Testa a função remove_item_from_inventory quando removemos 1 item do inventário"""

    sample_user.inventory = {101: 2} # Start with 2 items
    mock_db.users.find_one.return_value = sample_user.model_dump(by_alias=True)
    mock_db.users.update_one.return_value = MagicMock(modified_count=1)
    user_repo = UserRepository(db=mock_db)


    quantity_to_remove = 1
    result = await user_repo.remove_item_from_inventory(
        user_id=sample_user.user_id,
        item_id=101,
        quantity=quantity_to_remove
    )


    assert result is True
    mock_db.users.update_one.assert_awaited_with(
        {'_id': sample_user.user_id},
        {'$inc': {f'inventory.{101}': -quantity_to_remove}} # <-- Expect -1 here
    )

async def test_equip_item_failure_not_owned_or_no_user(mock_db):
    """
    Testa a falha: Usuário não existe OU não tem o item no inventário.
    Cenário: matched_count=0.
    """
    # O filtro falhou, então nenhum documento foi encontrado.
    mock_db.users.update_one.return_value = MagicMock(matched_count=0)
    user_repo = UserRepository(db=mock_db)

    result = await user_repo.equip_item(user_id=12345, item_id=999) # Item que não tem

    assert result is False


async def test_unequip_item_success(mock_db):
    """Testa o desequipamento atômico."""

    # Simulamos que o usuário foi encontrado e modificado
    mock_db.users.update_one.return_value = MagicMock(matched_count=1, modified_count=1)
    user_repo = UserRepository(db=mock_db)

    result = await user_repo.unequip_item(user_id=12345)

    assert result is True

    # Verifica a query atômica com $unset
    mock_db.users.update_one.assert_awaited_with(
        {'_id': 12345},
        {'$unset': {'equipped_item_id': ""}}
    )

async def test_unequip_item_idempotent(mock_db):
    """Testa que retorna True mesmo se já estava desequipado."""

    # Encontrado (matched=1), mas nada mudou (modified=0)
    mock_db.users.update_one.return_value = MagicMock(matched_count=1, modified_count=0)
    user_repo = UserRepository(db=mock_db)

    result = await user_repo.unequip_item(user_id=12345)

    assert result is True

async def test_add_role(mock_db, sample_user):
    """Testa a função add_role."""

    mock_db.users.update_one.return_value = MagicMock(modified_count=1,acknowledged=True)

    user_repo = UserRepository(db=mock_db)

    result = await user_repo.add_role(user_id=sample_user.user_id, role_id=1)

    assert result is True
    mock_db.users.update_one.assert_awaited_with(
        {'_id': sample_user.user_id},
        {'$addToSet': {'role_ids': 1}}
    )

async def test_remove_role(mock_db, sample_user):
    """Testa a remoção de um role."""

    mock_db.users.update_one.return_value = MagicMock(modified_count=True,acknowledged=True)

    user_repo = UserRepository(db=mock_db)

    result = await user_repo.remove_role(user_id=sample_user.user_id, role_id=1)

    assert result is True
    mock_db.users.update_one.assert_awaited_with(
        {'_id': sample_user.user_id},
        {'$pull': {'role_ids': 1}}
    )