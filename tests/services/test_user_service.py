import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.services.user_service import UserService
from src.database.models.user import UserModel, UserStatus
from src.database.models.item import ItemModel, ItemType

@pytest.fixture
def mock_user_repo():
    repo = MagicMock()
    repo.get_all_ids = AsyncMock()
    repo.create_many = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.equip_item = AsyncMock()
    repo.unequip_item = AsyncMock()
    return repo

@pytest.fixture
def mock_item_repo():
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    return repo

@pytest.fixture
def service(mock_user_repo, mock_item_repo):
    return UserService(mock_user_repo, mock_item_repo)

@pytest.mark.asyncio
async def test_sync_guild_users(service, mock_user_repo):
    # Setup
    mock_user_repo.get_all_ids.return_value = {101} # 101 já existe
    mock_user_repo.create_many.return_value = 1

    members_data = [
        {"id": 101, "name": "Old User", "joined_at": datetime.now(), "bot": False},
        {"id": 102, "name": "New User", "joined_at": datetime.now(), "bot": False},
        {"id": 999, "name": "Bot User", "joined_at": datetime.now(), "bot": True}
    ]

    # Execução
    created, ignored = await service.sync_guild_users(members_data)

    # Asserções
    assert created == 1
    assert ignored == 1
    mock_user_repo.get_all_ids.assert_awaited_once()
    mock_user_repo.create_many.assert_awaited_once()

    # Verifica argumento do create_many
    args, _ = mock_user_repo.create_many.await_args
    created_users = args[0]
    assert len(created_users) == 1
    assert created_users[0].user_id == 102

@pytest.mark.asyncio
async def test_equip_item_success(service, mock_user_repo, mock_item_repo):
    # Setup
    user = MagicMock(spec=UserModel)
    user.inventory = {1: 1} # Item ID 1, Qty 1
    mock_user_repo.get_by_id.return_value = user

    item = MagicMock(spec=ItemModel)
    item.item_id = 1
    item.item_type = ItemType.EQUIPPABLE # Uso direto do enum correto

    mock_item_repo.get_by_id.return_value = item

    # Execução
    success, msg = await service.equip_item(user_id=123, item_id=1)

    # Asserções
    assert success is True
    assert "sucesso" in msg
    mock_user_repo.equip_item.assert_awaited_once_with(123, 1)

@pytest.mark.asyncio
async def test_equip_item_not_owned(service, mock_user_repo, mock_item_repo):
    # Setup
    user = MagicMock(spec=UserModel)
    user.inventory = {} # Sem itens
    mock_user_repo.get_by_id.return_value = user

    item = MagicMock()
    item.item_id = 1
    mock_item_repo.get_by_id.return_value = item

    # Execução
    success, msg = await service.equip_item(user_id=123, item_id=1)

    # Asserções
    assert success is False
    assert "não possui" in msg
    mock_user_repo.equip_item.assert_not_awaited()

@pytest.mark.asyncio
async def test_equip_item_fail_not_equippable(service, mock_user_repo, mock_item_repo):
    # Setup
    user = MagicMock(spec=UserModel)
    user.inventory = {1: 1}
    mock_user_repo.get_by_id.return_value = user

    item = MagicMock(spec=ItemModel)
    item.item_id = 1
    item.name = "Poção"
    item.item_type = ItemType.CONSUMABLE # Não equipável

    mock_item_repo.get_by_id.return_value = item

    # Execução
    success, msg = await service.equip_item(user_id=123, item_id=1)

    # Asserções
    assert success is False
    assert "não pode ser equipado" in msg
    mock_user_repo.equip_item.assert_not_awaited()

@pytest.mark.asyncio
async def test_unequip_item_success(service, mock_user_repo):
    # Setup
    user = MagicMock(spec=UserModel)
    mock_user_repo.get_by_id.return_value = user

    # Execução
    success, msg = await service.unequip_item(user_id=123)

    # Asserções
    assert success is True
    assert "desequipado com sucesso" in msg
    mock_user_repo.unequip_item.assert_awaited_once_with(123)
