import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from src.services.mission_service import MissionService, RANK_REWARDS
from src.database.models.mission import MissionModel, MissionStatus, EvaluatorModel, EvaluationRank
from src.database.models.user import UserModel



# --- FIXTURES ---

@pytest.fixture
def mock_repos():
    return {
        "mission": MagicMock(),
        "user": MagicMock(),
        "item": MagicMock(),
        "leveling": MagicMock()
    }


@pytest.fixture
def service(mock_repos):
    mock_repos["mission"].get_by_id = AsyncMock()
    mock_repos["mission"].add_participant = AsyncMock()
    mock_repos["mission"].update_evaluator = AsyncMock()
    mock_repos["mission"].update_status = AsyncMock()

    mock_repos["user"].get_by_id = AsyncMock()

    mock_repos["item"].get_by_id = AsyncMock()

    mock_repos["leveling"].grant_reward = AsyncMock()

    return MissionService(
        mission_repo=mock_repos["mission"],
        leveling_service=mock_repos["leveling"],
        user_repo=mock_repos["user"],
    )


# Dados de teste

def create_fake_mission(creator_id=1, evaluators=None):
    return MissionModel(
        _id=100,
        title="Ajuda Python",
        creator_id=creator_id,
        created_at=datetime.now(),
        status=MissionStatus.OPEN,
        evaluators=evaluators or []
    )


def create_fake_user(user_id=2, equipped_item_id=None):
    return UserModel(
        _id=user_id,
        username="Teste1",
        coins=0,
        xp=0,
        joined_at=datetime.now(),
        equipped_item_id=equipped_item_id,
        inventory={}
    )


# --- TESTES DE AVALIAÇÃO (EVALUATE) ---

@pytest.mark.asyncio
async def test_evaluate_user_success(service, mock_repos):
    """Testa a avaliação sem bônus."""

    mission = create_fake_mission(creator_id=1)
    helper = create_fake_user(user_id=2)

    mock_repos["mission"].get_by_id.return_value = mission
    mock_repos["user"].get_by_id.return_value = helper
    mock_repos["leveling"].calculate_bonus = AsyncMock(return_value=(50, 125, ""))

    # Mock do Discord
    guild_mock = MagicMock()
    guild_mock.get_thread.return_value = AsyncMock()  # Thread é assíncrona


    # Mockamos create_task para não disparar thread real
    with patch("asyncio.create_task") as mock_task:
        success, msg = await service.evaluate_user(
            mission_id=100,
            author_id=1,
            user_id=2,
            rank="S",
            guild=guild_mock
        )

    assert success is True
    assert f"O usuário {2} foi avaliado com sucesso na missão {100}" in msg

    # Verifica se deu o prêmio base do Rank S
    expected_xp = RANK_REWARDS["S"]["xp"]
    expected_coins = RANK_REWARDS["S"]["coins"]

    mock_repos["leveling"].grant_reward.assert_awaited_with(2, expected_xp, expected_coins, guild_mock)
    mock_repos["mission"].add_participant.assert_awaited()



@pytest.mark.asyncio
async def test_evaluate_user_fail_self_vote(service, mock_repos):
    """Testa a regra: Não pode avaliar a si mesmo."""

    mission = create_fake_mission(creator_id=1)
    mock_repos["mission"].get_by_id.return_value = mission
    mock_repos["user"].get_by_id.return_value = create_fake_user(user_id=1)

    success, msg = await service.evaluate_user(100, author_id=1, user_id=1, rank="S", guild=MagicMock())

    assert success is False
    assert "não pode avaliar a si mesmo" in msg
    mock_repos["leveling"].grant_reward.assert_not_awaited()


@pytest.mark.asyncio
async def test_evaluate_user_fail_already_evaluated(service, mock_repos):
    """Testa regra: Não pode avaliar duas vezes na mesma missão."""

    # O user 2 JÁ ESTÁ na lista de evaluators
    existing_eval = EvaluatorModel(user_id=2, username="Helper", user_level_at_time=1, rank=EvaluationRank.A,
                                   xp_earned=10, coins_earned=10)
    mission = create_fake_mission(creator_id=1, evaluators=[existing_eval])

    mock_repos["mission"].get_by_id.return_value = mission
    mock_repos["user"].get_by_id.return_value = create_fake_user(user_id=2)


    success, msg = await service.evaluate_user(100, author_id=1, user_id=2, rank="S", guild=MagicMock())

    assert success is False
    assert "já foi avaliado" in msg


