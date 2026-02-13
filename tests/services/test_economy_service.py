import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.economy_service import EconomyService
from src.database.models.item import ItemModel, ItemType

@pytest.fixture
def mock_user_service():
    service = MagicMock()
    service.has_balance = AsyncMock()
    service.debit_coins = AsyncMock()
    service.add_item_to_inventory = AsyncMock()
    return service

@pytest.fixture
def mock_item_repo():
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    return repo

@pytest.fixture
def service(mock_user_service, mock_item_repo):
    return EconomyService(mock_user_service, mock_item_repo)

def create_fake_item(item_id=101, price=50):
    return ItemModel(
        _id=item_id,
        name="Espada de Teste",
        description="...",
        price=price,
        item_type=ItemType.EQUIPPABLE
    )

# --- TESTES DE COMPRA (BUY) ---

@pytest.mark.asyncio
async def test_buy_item_success(service, mock_user_service, mock_item_repo):
    """Cenário: Tem dinheiro suficiente e tudo existe."""
    # ARRANGE
    item = create_fake_item(price=50)
    mock_item_repo.get_by_id.return_value = item

    # Simula que tem saldo
    mock_user_service.has_balance.return_value = True
    # Simula sucesso no débito e adição
    mock_user_service.debit_coins.return_value = True
    mock_user_service.add_item_to_inventory.return_value = True

    # ACT
    success, msg = await service.buy_item(user_id=1, item_id=101, item_quantity=1)

    # ASSERT
    assert success is True
    assert "com sucesso" in msg

    # Verifica chamadas ao UserService
    mock_user_service.has_balance.assert_awaited_with(1, 50)
    mock_user_service.debit_coins.assert_awaited_with(1, 50)
    mock_user_service.add_item_to_inventory.assert_awaited_with(1, 101, 1)

@pytest.mark.asyncio
async def test_buy_item_insufficient_funds(service, mock_user_service, mock_item_repo):
    """Cenário: Tenta comprar algo mais caro que o saldo."""
    # ARRANGE
    item = create_fake_item(price=50)
    mock_item_repo.get_by_id.return_value = item

    # Simula falta de saldo
    mock_user_service.has_balance.return_value = False

    # ACT
    success, msg = await service.buy_item(user_id=1, item_id=101, item_quantity=1)

    # ASSERT
    assert success is False
    assert "Saldo insuficiente" in msg

    # GARANTE que não debitou nem adicionou
    mock_user_service.debit_coins.assert_not_awaited()
    mock_user_service.add_item_to_inventory.assert_not_awaited()

@pytest.mark.asyncio
async def test_buy_multiple_items_price_check(service, mock_user_service, mock_item_repo):
    """
    Cenário: Compra 2 itens. Preço total duplicado.
    """
    # ARRANGE
    item = create_fake_item(price=50)
    mock_item_repo.get_by_id.return_value = item

    mock_user_service.has_balance.return_value = True # Assume que tem saldo
    mock_user_service.debit_coins.return_value = True
    mock_user_service.add_item_to_inventory.return_value = True

    # ACT
    success, msg = await service.buy_item(user_id=1, item_id=101, item_quantity=2)

    # ASSERT
    assert success is True
    # Verifica se verificou saldo para 100 (50*2)
    mock_user_service.has_balance.assert_awaited_with(1, 100)
    mock_user_service.debit_coins.assert_awaited_with(1, 100)
    mock_user_service.add_item_to_inventory.assert_awaited_with(1, 101, 2)
