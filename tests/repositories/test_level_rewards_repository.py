import pytest
from unittest.mock import AsyncMock, MagicMock
from pymongo.errors import DuplicateKeyError

from src.database.models.level_rewards import LevelRewardsModel
from src.utils.repositories.level_rewards_repository import LevelRewardsRepository


pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_db():
    """Fixture para criar um mock do banco de dados e da coleção."""
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.level_rewards = mock_collection
    return mock_db


@pytest.fixture
def sample_reward() -> LevelRewardsModel:
    """Fixture para criar um uma recompensa de nível """
    return LevelRewardsModel(
        level_required=5,
        role_id=1265656,
        role_name='lvl 5 mestre do código'

    )

async def test_get_role_for_level(mock_db, sample_reward):
    """
    Teste para verificar se a query está correta e retorna o nível corretamente.
    """
    mock_db.level_rewards.find_one.return_value = sample_reward.model_dump(by_alias=True)
    repo = LevelRewardsRepository(db=mock_db)
    user_level = 5

    result = await repo.get_role_for_level(user_level)

    assert result is not None
    assert result.level_required == 5

    mock_db.level_rewards.find_one.assert_awaited_with(
        {"level_required": {"$lte": user_level}},
        sort=[("level_required", -1)]  #
    )

async def test_get_role_for_level_too_low(mock_db, sample_reward):
    """
    Teste para verificar se retorna None quando o lvl está abaixo.
    """
    mock_db.level_rewards.find_one.return_value = None
    repo = LevelRewardsRepository(db=mock_db)
    user_level = 3

    result = await repo.get_role_for_level(user_level)

    assert result is None


from unittest.mock import MagicMock, AsyncMock  # <--- Importe o AsyncMock


async def test_get_all_reward_role_ids(mock_db):
    """
    Testa se retorna uma lista limpa de IDs.
    Simula o comportamento assíncrono do Motor (MongoDB).
    """

    # 1. O GABARITO (O que queremos que o 'banco' devolva)
    raw_data = [
        {"role_id": 100},
        {"role_id": 200},
        {"role_id": 300}
    ]

    mock_cursor = MagicMock()


    mock_cursor.to_list = AsyncMock(return_value=raw_data)


    mock_db.level_rewards.find.return_value = mock_cursor

    repo = LevelRewardsRepository(db=mock_db)
    result = await repo.get_all_reward_role_ids()

    assert result == [100, 200, 300]

    mock_cursor.to_list.assert_awaited_with(length=None)

async def test_create_reward(mock_db, sample_reward):
    """Testa a criação bem sucedida de uam recompensa de lvl."""

    reward_repo = LevelRewardsRepository(db=mock_db)
    result = await reward_repo.create(reward_model=sample_reward)

    assert result is True

    expected_data = sample_reward.model_dump(by_alias=True)
    mock_db.level_rewards.insert_one.assert_awaited_with(expected_data)
