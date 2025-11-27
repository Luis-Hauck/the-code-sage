import pytest
from unittest.mock import AsyncMock, MagicMock
from pymongo.errors import DuplicateKeyError

from src.database.models.item import ItemModel, ItemType
from src.database.models.effects import CoinBoostPassive, GiveRoleEffect, XpBoostPassive, AnyEffect
from src.utils.repositories.item_repository import ItemRepository

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_db():
    """Cria um mock do banco de dados com uma coleção 'items'."""
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.items = mock_collection
    return mock_db

@pytest.fixture
def sample_item() -> ItemModel:
    """Cria um ItemsModel de exemplo para os testes."""
    return ItemModel(
        _id=101,
        name="Poção de XP Pequena",
        description="Concede 50 de XP.",
        price=100,
        item_type=ItemType.CONSUMABLE,
        effect=GiveRoleEffect(type='role_effect', role_id=101),
        passive_effects=[
            XpBoostPassive(type='xp_boost', multiplier=1.05),
            CoinBoostPassive(type='coin_boost', multiplier=1.10)
        ]
    )

@pytest.fixture
def sample_equip_item() -> ItemModel:
    """Cria um item equipável de exemplo."""
    return ItemModel(
       _id=201,
        name="Amuleto Simples",
        description="Aumenta ganho de moedas.",
        price=500,
        item_type=ItemType.EQUIPPABLE,
        effect= AnyEffect(type='role_effect', role_id=101),
        passive_effects=[
            CoinBoostPassive(type='coin_boost', multiplier=1.05)
        ]
    )

async def test_create_item_sucess(mock_db, sample_item):
    """Testa a criação bem sucedida de um item."""

    item_repo = ItemRepository(db=mock_db)
    result = await item_repo.create(item_model=sample_item)

    assert result is True

    expected_data = sample_item.model_dump(by_alias=True)
    mock_db.items.insert_one.assert_awaited_with(expected_data)

async def test_create_item_duplicate_key(mock_db, sample_item):
    """Testa o retorno de erro ao inserir itens com ids duplicados"""
    mock_db.items.insert_one.side_effect =  DuplicateKeyError("duplicate key error")
    item_repo  = ItemRepository(db=mock_db)
    result = await item_repo.create(item_model=sample_item)

    assert result is False

async def test_get_item_by_id_success(mock_db, sample_item):
    """Testa se get_by_id retorna o ItemsModel correto."""

    mock_db.items.find_one.return_value = sample_item.model_dump(by_alias=True)
    item_repo = ItemRepository(db=mock_db)


    result = await item_repo.get_by_id(sample_item.item_id)

    assert isinstance(result, ItemModel)
    assert result.item_id == sample_item.item_id
    mock_db.items.find_one.assert_awaited_with({"_id": sample_item.item_id})

async def test_get_item_by_id_not_found(mock_db):
    """Testa se get_by_id retorna None se o item não for encontrado."""

    mock_db.items.find_one.return_value = None
    item_repo = ItemRepository(db=mock_db)

    result = await item_repo.get_by_id(999) # ID inexistente

    assert result is None

async def test_update_price_success(mock_db, sample_item):
    """Testa a atualização de um campo do item."""

    mock_db.items.update_one.return_value = MagicMock(matched_count=1)
    item_repo = ItemRepository(db=mock_db)
    new_price = 1

    result = await item_repo.update_price(item_id=sample_item.item_id, new_price=new_price)

    assert result is True
    mock_db.items.update_one.assert_awaited_with({"_id": sample_item.item_id}, {'$set': {'price': 1}})

async def test_delete_item_success(mock_db, sample_item):
    """Testa a deleção bem-sucedida de um item."""

    mock_db.items.delete_one.return_value = MagicMock(deleted_count=1)
    item_repo = ItemRepository(db=mock_db)

    result = await item_repo.delete(item_id=sample_item.item_id)

    assert result is True
    mock_db.items.delete_one.assert_awaited_with({"_id": sample_item.item_id})

async def test_delete_item_not_found(mock_db):
    """Testa a deleção quando o item não existe."""

    mock_db.items.delete_one.return_value = MagicMock(deleted_count=0)
    item_repo = ItemRepository(db=mock_db)

    result = await item_repo.delete(item_id=999)

    assert result is False