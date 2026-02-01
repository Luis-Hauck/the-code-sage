import pytest
from unittest.mock import MagicMock, AsyncMock
import datetime

from src.services.leveling_service import LevelingService
from src.database.models.user import UserModel
from src.database.models.item import ItemModel, ItemType
from src.database.models.level_rewards import LevelRewardsModel
from src.database.models.effects import XpBoostPassive


@pytest.fixture
def mock_user_repo():
    repo = MagicMock()
    repo.add_xp_coins = AsyncMock()
    return repo


@pytest.fixture
def mock_item_repo():
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_rewards_repo():
    repo = MagicMock()
    repo.get_role_for_level = AsyncMock()
    repo.get_all_reward_role_ids = AsyncMock()
    return repo


@pytest.fixture
def service(mock_user_repo, mock_rewards_repo, mock_item_repo):
    svc = LevelingService(mock_user_repo, mock_rewards_repo, mock_item_repo)
    # Define o fator base para facilitar a matemática dos testes (100 xp = lvl 1)
    svc.BASE_XP_FACTOR = 100
    return svc


@pytest.fixture
def mock_guild():
    guild = MagicMock()
    guild.get_role.return_value = MagicMock(name="CargoNovo")
    # Mock do get_member para garantir que retorna algo
    guild.get_member.return_value = MagicMock()
    return guild


@pytest.fixture
def mock_member():
    member = MagicMock()
    member.id = 123
    member.display_name = "TestUser"
    member.name = "TestUser"
    member.roles = []
    member.add_roles = AsyncMock()
    member.remove_roles = AsyncMock()
    return member


def test_calculate_level_logic(service):
    # Com BASE_XP_FACTOR = 100
    assert service.calculate_level(0) == 0
    assert service.calculate_level(99) == 0
    assert service.calculate_level(100) == 1
    assert service.calculate_level(400) == 2
    assert service.calculate_level(350) == 1



@pytest.mark.asyncio
async def test_grant_reward_no_change(service, mock_user_repo, mock_guild):
    """
    Cenário: Ganhou XP, mas sync_roles retornou False (não houve mudança de cargo).
    Expectativa: Deve retornar (False, Nível atual).
    """
    # Setup do User
    user_fake = UserModel(_id=1, username='luis', xp=150, coins=10, role_ids=[], joined_at=datetime.datetime.now())
    mock_user_repo.add_xp_coins.return_value = user_fake

    # Mockamos o sync_roles para retornar False (simulando que nada mudou)
    service.sync_roles = AsyncMock(return_value=False)

    result, level = await service.grant_reward(user_id=1, xp_amount=10, coins_amount=0, guild=mock_guild)

    service.sync_roles.assert_called_once()  # Ele deve chamar para verificar
    assert result is False
    assert level is 1


@pytest.mark.asyncio
async def test_grant_reward_with_level_up_success(service, mock_user_repo, mock_guild):
    """
    Cenário: Ganhou XP e sync_roles retornou True (Houve Level Up/Novo Cargo).
    Expectativa: Deve retornar (True, nivel_atual).
    """
    # Setup (400 XP = Nível 2)
    user_fake = UserModel(_id=1, username='luis', xp=400, coins=10, role_ids=[], joined_at=datetime.datetime.now())
    mock_user_repo.add_xp_coins.return_value = user_fake

    # Mockamos o sync_roles para retornar True
    service.sync_roles = AsyncMock(return_value=True)

    result, level = await service.grant_reward(user_id=1, xp_amount=50, coins_amount=0, guild=mock_guild)

    service.sync_roles.assert_called_once_with(1, 2, mock_guild)
    assert result is True
    assert level == 2


@pytest.mark.asyncio
async def test_sync_roles_add_new_role(service, mock_rewards_repo, mock_guild, mock_member):
    """
    Cenário: Usuário Nível 5 não tem o cargo.
    Expectativa: Deve adicionar o cargo e retornar True.
    """
    # Configuração dos Mocks
    mock_guild.get_member.return_value = mock_member
    mock_member.roles = []  # Usuário sem cargos

    # Recompensa esperada
    reward_fake = LevelRewardsModel(level_required=5, role_id=500, role_name="Mestre")
    mock_rewards_repo.get_role_for_level.return_value = reward_fake
    mock_rewards_repo.get_all_reward_role_ids.return_value = [500]

    # Cargo no Discord
    role_obj = MagicMock(id=500, name="Mestre")
    mock_guild.get_role.return_value = role_obj

    result = await service.sync_roles(user_id=123, current_level=5, guild=mock_guild)

    mock_member.add_roles.assert_awaited_once_with(role_obj)
    assert result is True  # Deve indicar que houve adição


@pytest.mark.asyncio
async def test_sync_roles_already_has_role(service, mock_rewards_repo, mock_guild, mock_member):
    """
    Cenário: Usuário Nível 5 JÁ TEM o cargo.
    Expectativa: Não deve adicionar nada, nem remover, e retornar False (Idempotência).
    """
    mock_guild.get_member.return_value = mock_member

    # O usuário já tem o cargo ID 500
    role_mestre = MagicMock(id=500, name="Mestre")
    mock_member.roles = [role_mestre]

    reward_fake = LevelRewardsModel(level_required=5, role_id=500, role_name="Mestre")
    mock_rewards_repo.get_role_for_level.return_value = reward_fake
    mock_rewards_repo.get_all_reward_role_ids.return_value = [500]

    result = await service.sync_roles(user_id=123, current_level=5, guild=mock_guild)

    mock_member.add_roles.assert_not_called()
    mock_member.remove_roles.assert_not_called()
    assert result is False  # Nada mudou


@pytest.mark.asyncio
async def test_sync_roles_replace_old_role(service, mock_rewards_repo, mock_guild, mock_member):
    """
    Cenário: Usuário subiu de nível. Tem cargo antigo (Lvl 1) e precisa do novo (Lvl 2).
    Expectativa: Remove o antigo, adiciona o novo, retorna True.
    """
    mock_guild.get_member.return_value = mock_member

    # Configuração: Meta é Nível 2 (ID 200)
    reward_target = LevelRewardsModel(level_required=2, role_id=200, role_name="Veterano")
    mock_rewards_repo.get_role_for_level.return_value = reward_target

    # Lista de todos os cargos de nível conhecidos
    mock_rewards_repo.get_all_reward_role_ids.return_value = [100, 200, 300]

    # Estado atual do usuário: Tem cargo ID 100 (Antigo) e ID 999 (Admin - não deve ser removido)
    role_old = MagicMock(id=100)
    role_admin = MagicMock(id=999)
    mock_member.roles = [role_old, role_admin]

    # Objeto do cargo novo no Discord
    role_new_obj = MagicMock(id=200)
    mock_guild.get_role.return_value = role_new_obj

    result = await service.sync_roles(user_id=123, current_level=2, guild=mock_guild)


    # Verificamos a remoção (deve remover ID 100)
    mock_member.remove_roles.assert_awaited_once()
    args, _ = mock_member.remove_roles.await_args
    assert args[0].id == 100  # Garante que removeu o certo

    # Verificamos a adição (deve adicionar ID 200)
    mock_member.add_roles.assert_awaited_once_with(role_new_obj)

    assert result is True


@pytest.mark.asyncio
async def test_calculate_bonus_with_xp_item(service, mock_item_repo):
    """Testa se o cálculo de bônus aplica o multiplicador de XP corretamente."""

    user = UserModel(_id=1, username="Test", coins=0, xp=0, equipped_item_id=99, joined_at=datetime.datetime.now())

    # Mock do Item (Anel de +50% XP)
    mock_item_repo.get_by_id.return_value = ItemModel(
        _id=99,
        name="Anel Sábio",
        price=100,
        item_type=ItemType.EQUIPPABLE,
        description="...",
        passive_effects=[XpBoostPassive(type="xp_boost", multiplier=0.5)],
        effect=None
    )

    base_xp = 100
    base_coins = 100

    final_xp, final_coins, text = await service.calculate_bonus(user, base_xp, base_coins)

    assert final_xp == 150  # 100 + 50%
    assert final_coins == 100  # Sem bônus de moeda