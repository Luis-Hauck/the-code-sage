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
    repo.add_xp_coins = AsyncMock()
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


def create_fake_user(
    user_id: int = 1,
    username: str = "Tester",
    coins: int = 100,
    inventory: dict | None = None,
    equipped_item_id: int | None = None,
) -> UserModel:
    """Factory de usuário para manter os testes consistentes."""
    return UserModel(
        _id=user_id,
        username=username,
        coins=coins,
        inventory=inventory or {},
        equipped_item_id=equipped_item_id,
        xp=0,
        status=UserStatus.ACTIVE,
        joined_at=datetime.now(),
        role_ids=[],
    )


def create_fake_item(
    item_id: int = 1,
    name: str = "Espada de Teste",
    item_type: ItemType = ItemType.EQUIPPABLE,
) -> ItemModel:
    """Factory de item para reaproveitar cenários do antigo economy service."""
    return ItemModel(
        _id=item_id,
        name=name,
        description="Item de teste",
        price=50,
        item_type=item_type,
        effect=None,
        passive_effects=[],
    )


@pytest.mark.asyncio
async def test_sync_guild_users(service, mock_user_repo):
    """Sincroniza membros da guilda criando apenas usuários novos não-bot."""
    # Setup
    mock_user_repo.get_all_ids.return_value = {101}  # 101 já existe
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
    """Equipa item quando usuário possui o item e ele é equipável."""
    # Setup
    user = create_fake_user(user_id=123, inventory={1: 1})
    mock_user_repo.get_by_id.return_value = user

    item = create_fake_item(item_id=1, item_type=ItemType.EQUIPPABLE)
    mock_item_repo.get_by_id.return_value = item

    # Execução
    success, msg = await service.equip_item(user_id=123, item_id=1)

    # Asserções
    assert success is True
    assert "sucesso" in msg
    mock_user_repo.equip_item.assert_awaited_once_with(123, 1)


@pytest.mark.asyncio
async def test_equip_item_not_owned(service, mock_user_repo, mock_item_repo):
    """Bloqueia equipar quando o item não está no inventário."""
    # Setup
    user = create_fake_user(user_id=123, inventory={})  # Sem itens
    mock_user_repo.get_by_id.return_value = user

    item = create_fake_item(item_id=1)
    mock_item_repo.get_by_id.return_value = item

    # Execução
    success, msg = await service.equip_item(user_id=123, item_id=1)

    # Asserções
    assert success is False
    assert "não possui" in msg
    mock_user_repo.equip_item.assert_not_awaited()


@pytest.mark.asyncio
async def test_equip_item_fail_not_equippable(service, mock_user_repo, mock_item_repo):
    """Bloqueia equipar quando o tipo do item não é EQUIPPABLE."""
    # Setup
    user = create_fake_user(user_id=123, inventory={1: 1})
    mock_user_repo.get_by_id.return_value = user

    item = create_fake_item(item_id=1, name="Poção", item_type=ItemType.CONSUMABLE)
    mock_item_repo.get_by_id.return_value = item

    # Execução
    success, msg = await service.equip_item(user_id=123, item_id=1)

    # Asserções
    assert success is False
    assert "não pode ser equipado" in msg
    mock_user_repo.equip_item.assert_not_awaited()


@pytest.mark.asyncio
async def test_unequip_item_success(service, mock_user_repo):
    """Desequipa item com sucesso para usuário existente."""
    # Setup
    user = create_fake_user(user_id=123, equipped_item_id=1)
    mock_user_repo.get_by_id.return_value = user

    # Execução
    success, msg = await service.unequip_item(user_id=123)

    # Asserções
    assert success is True
    assert "desequipado com sucesso" in msg
    mock_user_repo.unequip_item.assert_awaited_once_with(123)


@pytest.mark.asyncio
async def test_equip_item_user_not_found(service, mock_user_repo):
    """Retorna erro de domínio quando o usuário não existe."""
    mock_user_repo.get_by_id.return_value = None

    success, msg = await service.equip_item(user_id=999, item_id=1)

    assert success is False
    assert "Usuário não encontrado" in msg
    mock_user_repo.equip_item.assert_not_awaited()


@pytest.mark.asyncio
async def test_equip_item_item_not_found(service, mock_user_repo, mock_item_repo):
    """Retorna erro quando o item não é encontrado no repositório de itens."""
    mock_user_repo.get_by_id.return_value = create_fake_user(user_id=123, inventory={1: 1})
    mock_item_repo.get_by_id.return_value = None

    success, msg = await service.equip_item(user_id=123, item_id=1)

    assert success is False
    assert "Item não existe" in msg
    mock_user_repo.equip_item.assert_not_awaited()


@pytest.mark.asyncio
async def test_unequip_item_user_not_found(service, mock_user_repo):
    """Bloqueia operação de desequipar quando usuário não existe."""
    mock_user_repo.get_by_id.return_value = None

    success, msg = await service.unequip_item(user_id=999)

    assert success is False
    assert "não encontrado" in msg
    mock_user_repo.unequip_item.assert_not_awaited()


@pytest.mark.asyncio
async def test_has_balance_true(service, mock_user_repo):
    """has_balance retorna True quando saldo cobre o valor solicitado."""
    mock_user_repo.get_by_id.return_value = create_fake_user(coins=200)

    result = await service.has_balance(user_id=1, amount=150)

    assert result is True


@pytest.mark.asyncio
async def test_has_balance_false_when_insufficient(service, mock_user_repo):
    """has_balance retorna False quando o saldo é insuficiente."""
    mock_user_repo.get_by_id.return_value = create_fake_user(coins=50)

    result = await service.has_balance(user_id=1, amount=150)

    assert result is False


@pytest.mark.asyncio
async def test_has_balance_false_when_user_missing(service, mock_user_repo):
    """has_balance retorna False para usuário inexistente."""
    mock_user_repo.get_by_id.return_value = None

    result = await service.has_balance(user_id=1, amount=10)

    assert result is False


@pytest.mark.asyncio
async def test_debit_coins_success(service, mock_user_repo):
    """Debita moedas com sinal negativo no repositório e retorna sucesso."""
    mock_user_repo.add_xp_coins.return_value = create_fake_user(coins=70)

    result = await service.debit_coins(user_id=1, amount=30)

    assert result is True
    mock_user_repo.add_xp_coins.assert_awaited_once_with(user_id=1, xp=0, coins=-30)


@pytest.mark.asyncio
async def test_debit_coins_invalid_amount(service, mock_user_repo):
    """Não permite débito com valor negativo e evita chamada ao repositório."""
    # Regra de segurança: valor negativo significaria crédito acidental.
    result = await service.debit_coins(user_id=1, amount=-10)

    assert result is False
    mock_user_repo.add_xp_coins.assert_not_awaited()


@pytest.mark.asyncio
async def test_debit_coins_returns_false_on_repo_failure(service, mock_user_repo):
    """Propaga falha de persistência retornando False quando repo falha."""
    # add_xp_coins retorna None quando o update não foi concluído.
    mock_user_repo.add_xp_coins.return_value = None

    result = await service.debit_coins(user_id=1, amount=20)

    assert result is False
