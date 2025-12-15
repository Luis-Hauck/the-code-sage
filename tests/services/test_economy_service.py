import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.economy_service import EconomyService
from src.database.models.user import UserModel, UserStatus
from src.database.models.item import ItemModel, ItemType
import datetime


@pytest.fixture
def mock_user_repo():
    repo = MagicMock()
    # Definimos todos os métodos que o service chama como Assíncronos
    repo.get_by_id = AsyncMock()
    repo.add_xp_coins = AsyncMock()
    repo.add_item_to_inventory = AsyncMock()
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
    return EconomyService(mock_user_repo, mock_item_repo)


# Dados Falsos para reuso
def create_fake_user(user_id=1, coins=100, inventory=None, equipped=None):
    return UserModel(
        _id=user_id,
        username="Tester",
        coins=coins,
        inventory=inventory or {},
        equipped_item_id=equipped,
        xp=0,
        status=UserStatus.ACTIVE,
        joined_at=datetime.date.today()
    )


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
async def test_buy_item_success(service, mock_user_repo, mock_item_repo):
    """Cenário: Tem dinheiro suficiente e tudo existe."""
    # ARRANGE
    user = create_fake_user(coins=100)  # Tem 100
    item = create_fake_item(price=50)  # Custa 50

    mock_user_repo.get_by_id.return_value = user
    mock_item_repo.get_by_id.return_value = item
    # Simula que o desconto de moedas funcionou e retornou o user atualizado
    mock_user_repo.add_xp_coins.return_value = user

    # ACT
    success, msg = await service.buy_item(user_id=1, item_id=101, item_quantity=1)

    # ASSERT
    assert success is True
    assert "com sucesso" in msg
    # Verifica se descontou o valor correto (-50)
    mock_user_repo.add_xp_coins.assert_awaited_with(user_id=1, xp=0, coins=-50)
    # Verifica se adicionou ao inventário
    mock_user_repo.add_item_to_inventory.assert_awaited_with(1, 101, 1)


@pytest.mark.asyncio
async def test_buy_item_insufficient_funds(service, mock_user_repo, mock_item_repo):
    """Cenário: Tenta comprar algo mais caro que o saldo."""
    # ARRANGE
    user = create_fake_user(coins=10)  # Só tem 10
    item = create_fake_item(price=50)  # Custa 50

    mock_user_repo.get_by_id.return_value = user
    mock_item_repo.get_by_id.return_value = item

    # ACT
    success, msg = await service.buy_item(user_id=1, item_id=101, item_quantity=1)

    # ASSERT
    assert success is False
    assert "Saldo insuficiente" in msg
    # GARANTE que não mexeu no dinheiro nem no inventário
    mock_user_repo.add_xp_coins.assert_not_called()
    mock_user_repo.add_item_to_inventory.assert_not_called()


@pytest.mark.asyncio
async def test_buy_multiple_items_price_check(service, mock_user_repo, mock_item_repo):
    """
    Cenário: Compra 2 itens. Tem dinheiro para 1, mas não para 2.
    Testa se a multiplicação (price * quantity) está funcionando.
    """
    # ARRANGE
    user = create_fake_user(coins=80)  # Tem 80
    item = create_fake_item(price=50)  # Custa 50

    mock_user_repo.get_by_id.return_value = user
    mock_item_repo.get_by_id.return_value = item

    # ACT (Tenta comprar 2. Total = 100)
    success, msg = await service.buy_item(user_id=1, item_id=101, item_quantity=2)

    # ASSERT
    assert success is False  # Deve falhar pois 80 < 100
    mock_user_repo.add_xp_coins.assert_not_called()


# --- TESTES DE EQUIPAR (EQUIP) ---

@pytest.mark.asyncio
async def test_equip_item_success(service, mock_user_repo,mock_item_repo):
    """Cenário: Usuário tem o item no inventário e equipa."""
    # ARRANGE

    # Inventário tem o item 101
    user = create_fake_user(inventory={101: 1})

    equippable_item = create_fake_item(item_id=101, price=50)
    equippable_item.item_type = ItemType.EQUIPPABLE  # Garantimos que é equipável

    mock_user_repo.get_by_id.return_value = user
    mock_item_repo.get_by_id.return_value = equippable_item


    # ACT
    success, msg = await service.equip_item(user_id=1, item_id=101)

    # ASSERT
    assert success is True
    mock_user_repo.equip_item.assert_awaited_with(1, 101)


@pytest.mark.asyncio
async def test_equip_item_fail_missing_inventory(service, mock_user_repo):
    """Cenário: Tenta equipar item que não comprou."""

    # ARRANGE
    user = create_fake_user(inventory={})  # Inventário vazio
    mock_user_repo.get_by_id.return_value = user


    # ACT
    success, msg = await service.equip_item(user_id=1, item_id=999)

    # ASSERT
    assert success is False
    assert "não possui" in msg
    mock_user_repo.equip_item.assert_not_called()


# --- TESTES DE DESEQUIPAR (UNEQUIP) ---

@pytest.mark.asyncio
async def test_unequip_item_success(service, mock_user_repo):
    """Cenário: Usuário está segurando o item e guarda."""
    # ARRANGE
    user = create_fake_user(equipped=200)  # Está usando o item 200
    mock_user_repo.get_by_id.return_value = user

    # ACT
    success, msg = await service.unequip_item(user_id=1, item_id=200)

    # ASSERT
    assert success is True
    mock_user_repo.unequip_item.assert_awaited_with(1)


@pytest.mark.asyncio
async def test_unequip_item_fail_wrong_item(service, mock_user_repo):
    """Cenário: Tenta desequipar um item que não está usando."""
    # ARRANGE
    user = create_fake_user(equipped=200)  # Está usando 200
    mock_user_repo.get_by_id.return_value = user

    # ACT
    # Tenta tirar o item 500 (mas está usando o 200)
    success, msg = await service.unequip_item(user_id=1, item_id=500)

    # ASSERT
    assert success is False
    assert "Você não possuí item equipado." in msg
    mock_user_repo.unequip_item.assert_not_called()


@pytest.mark.asyncio
async def test_equip_item_fail_not_equippable(service, mock_user_repo, mock_item_repo):
    """
    Cenário: Usuário tem o item, mas tenta equipar uma Poção (Consumível).
    Expectativa: Deve bloquear e avisar que não é equipável.
    """
    # ARRANGE
    # Usuário tem o item 101 no inventário
    user = create_fake_user(inventory={101: 5})

    # O item 101 é do tipo CONSUMÍVEL (Ex: Poção)
    item_consumivel = ItemModel(
        _id=101,
        name="Poção de Vida",
        description="Cura",
        price=10,
        effect=None,
        passive_effects=[],
        item_type=ItemType.CONSUMABLE
    )

    mock_user_repo.get_by_id.return_value = user
    mock_item_repo.get_by_id.return_value = item_consumivel

    # ACT
    success, msg = await service.equip_item(user_id=1, item_id=101)

    # ASSERT
    assert success is False
    assert "não pode ser equipado" in msg
    # Garante que NÃO chamou o método de salvar no banco
    mock_user_repo.equip_item.assert_not_called()