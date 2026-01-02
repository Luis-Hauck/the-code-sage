import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.leveling_service import LevelingService
from src.database.models.user import UserModel, UserStatus
import datetime
from src.database.models.level_rewards import LevelRewardsModel
from src.database.models.effects import XpBoostPassive
from src.database.models.item import ItemModel, ItemType

# --- FIXTURES ---

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
def service(mock_user_repo, mock_rewards_repo):
    svc = LevelingService(mock_user_repo, mock_rewards_repo, mock_item_repo)
    svc.BASE_XP_FACTOR = 100
    return svc

@pytest.fixture
def leveling_service_setup(mock_user_repo, mock_rewards_repo, mock_item_repo):
    service = LevelingService(mock_user_repo, mock_rewards_repo, mock_item_repo)
    return service, mock_item_repo


@pytest.fixture
def mock_guild():
    guild = MagicMock()
    guild.get_role.return_value = MagicMock(name="CargoNovo")
    return guild


@pytest.fixture
def mock_member():
    member = MagicMock()
    # add_roles e remove_roles são corrotinas no discord.py
    member.add_roles = AsyncMock()
    member.remove_roles = AsyncMock()
    return member


# --- TESTES DA MATEMÁTICA ---

def test_calculate_level_logic(service):
    assert service.calculate_level(0) == 0
    assert service.calculate_level(100) == 1
    assert service.calculate_level(400) == 2
    assert service.calculate_level(350) == 1



@pytest.mark.asyncio
async def test_grant_reward_no_level_up(service, mock_user_repo, mock_guild):
    """
    Cenário: Ganhou XP, mas continuou no mesmo nível.
    Expectativa: Não deve chamar sync_roles.
    """
    # 160 XP = Nível 1. (Raiz de 1.6 = 1.26 -> Floor 1)
    user_fake = UserModel(_id=1, username='luis', xp=160, coins=10, inventory={}, status=UserStatus.ACTIVE,
                          joined_at=datetime.date.today(), role_ids=[6])

    mock_user_repo.add_xp_coins.return_value = user_fake

    service.sync_roles = AsyncMock()

    await service.grant_reward(user_id=1, xp_amount=10, coins_amount=0, guild=mock_guild)

    # Se não mudou de nível, NÃO deve chamar sync_roles
    service.sync_roles.assert_not_called()


@pytest.mark.asyncio
async def test_grant_reward_with_level_up(service, mock_user_repo, mock_guild):
    """
    Cenário: Ganhou XP suficiente para upar.
    Expectativa: DEVE chamar sync_roles.
    """

    # 400 XP = Nível 2. (Raiz de 4 = 2)
    user_fake = UserModel(_id=1, username='luis', xp=400, coins=10, inventory={}, status=UserStatus.ACTIVE,
                          joined_at=datetime.date.today(), role_ids=[6])

    mock_user_repo.add_xp_coins.return_value = user_fake

    service.sync_roles = AsyncMock()


    await service.grant_reward(user_id=1, xp_amount=10, coins_amount=0, guild=mock_guild)


    service.sync_roles.assert_called_once_with(1, 2, mock_guild)



@pytest.mark.asyncio
async def test_sync_roles_logic(service, mock_rewards_repo, mock_guild, mock_member):
    reward_fake = LevelRewardsModel(level_required=2, role_id=200, role_name="Veterano")
    mock_rewards_repo.get_role_for_level.return_value = reward_fake
    mock_rewards_repo.get_all_reward_role_ids.return_value = [100, 200, 300]

    role_iniciante = MagicMock(id=100)
    role_veterano = MagicMock(id=200)
    role_admin = MagicMock(id=999)

    mock_member.roles = [role_iniciante, role_veterano, role_admin]
    mock_member.name = "TestUser"

    mock_guild.get_member.return_value = mock_member
    mock_guild.get_role.return_value = MagicMock(id=200)

    await service.sync_roles(user_id=123, nivel_atual=2, guild=mock_guild)

    # ASSERT
    mock_member.remove_roles.assert_awaited_once()
    args, _ = mock_member.remove_roles.await_args
    assert args[0].id == 100
    mock_member.add_roles.assert_not_called()


@pytest.mark.asyncio
async def test_sync_roles_add_new(service, mock_rewards_repo, mock_guild, mock_member):

    reward_fake = LevelRewardsModel(level_required=5, role_id=500, role_name="Mestre")
    mock_rewards_repo.get_role_for_level.return_value = reward_fake
    mock_rewards_repo.get_all_reward_role_ids.return_value = [500]

    mock_member.roles = []
    mock_guild.get_member.return_value = mock_member

    role_mestre_obj = MagicMock(id=500, name="Mestre")
    mock_guild.get_role.return_value = role_mestre_obj

    await service.sync_roles(user_id=123, nivel_atual=5, guild=mock_guild)


    mock_member.add_roles.assert_awaited_once_with(role_mestre_obj)

# --- TESTES DE CÁLCULO DE BÔNUS ---

@pytest.mark.asyncio
async def test_calculate_bonus_with_xp_item(leveling_service_setup):
    """Testa se o cálculo de bônus aplica o multiplicador de XP corretamente."""
    service, item_repo = leveling_service_setup

    # DADOS
    user = UserModel(_id=1,
                     username="Test",
                     coins=0, xp=0,
                     equipped_item_id=99,
                     joined_at=datetime.date.today())

    # Mock do Item (Anel de +50% XP)
    item_repo.get_by_id.return_value = ItemModel(
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

    # AÇÃO
    final_xp, final_coins, text = await service.calculate_bonus(user, base_xp, base_coins)

    # VERIFICAÇÃO
    assert final_xp == 150  # 100 + 50%
    assert final_coins == 100  # Sem bônus


@pytest.mark.asyncio
async def test_calculate_bonus_no_item(leveling_service_setup):
    """Testa se retorna o valor base quando não tem item."""
    service, item_repo = leveling_service_setup

    user = UserModel(_id=1,
                     username="Test",
                     coins=0,
                     xp=0,
                     equipped_item_id=None,
                     joined_at=datetime.date.today())

    final_xp, final_coins, text = await service.calculate_bonus(user, 100, 100)

    assert final_xp == 100
    assert final_coins == 100

