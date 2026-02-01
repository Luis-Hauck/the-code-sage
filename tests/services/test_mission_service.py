import pytest
from unittest.mock import MagicMock, AsyncMock, ANY
from datetime import datetime

from src.services.mission_service import MissionService, RANK_REWARDS
from src.database.models.mission import MissionModel, MissionStatus, EvaluatorModel, EvaluationRank
from src.database.models.user import UserModel


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


@pytest.mark.asyncio
async def test_evaluate_user_success(service, mock_repos):
    """
    Testa o fluxo feliz da avaliação.
    Verifica se calcula bônus, entrega recompensa e registra no banco.
    """
    mission_id = 100
    author_id = 1
    target_user_id = 2
    rank_str = "S"

    # 1. Configurar Mocks de Dados
    mission = create_fake_mission(creator_id=author_id)
    target_user = create_fake_user(user_id=target_user_id)

    mock_repos["mission"].get_by_id.return_value = mission
    mock_repos["user"].get_by_id.return_value = target_user

    # calculate_bonus retorna (xp, coins, texto)
    # Vamos simular que o bônus dobrou o XP base do rank S (50 -> 100)
    mock_repos["leveling"].calculate_bonus = AsyncMock(
        return_value=(100, 250, "Bônus Ativo!")
    )

    # grant_reward retorna (success, current_level)
    mock_repos["leveling"].grant_reward = AsyncMock(
        return_value=(True, 5)
    )

    success, data = await service.evaluate_user(
        mission_id=mission_id,
        author_id=author_id,
        user_id=target_user_id,
        rank=rank_str,
        guild=MagicMock()
    )

    assert success is True
    assert data["rank"] == EvaluationRank.S
    assert data["xp"] == 100  # Valor retornado pelo calculate_bonus
    assert data["coins"] == 250
    assert data["bonus"] == "Bônus Ativo!"

    # Verifica se grant_reward foi chamado com os valores finais (pós-bônus)
    mock_repos["leveling"].grant_reward.assert_awaited_with(
        target_user_id, 100, 250, ANY
    )

    # Verifica se salvou no banco
    mock_repos["mission"].add_participant.assert_awaited()
    args, _ = mock_repos["mission"].add_participant.await_args
    assert args[0] == mission_id
    assert isinstance(args[1], EvaluatorModel)
    assert args[1].xp_earned == 100  # Garante que salvou o XP com bônus


@pytest.mark.asyncio
async def test_evaluate_user_fail_self_vote(service, mock_repos):
    """Testa a regra: Não pode avaliar a si mesmo."""
    user_id = 1
    mission = create_fake_mission(creator_id=user_id)

    mock_repos["user"].get_by_id.return_value = create_fake_user(user_id=user_id)
    mock_repos["mission"].get_by_id.return_value = mission

    success, msg = await service.evaluate_user(100, user_id, user_id, "S", MagicMock())

    assert success is False
    assert "não pode avaliar a si mesmo" in msg
    mock_repos["leveling"].grant_reward.assert_not_awaited()


@pytest.mark.asyncio
async def test_evaluate_user_fail_already_evaluated(service, mock_repos):
    """Testa regra: Não pode avaliar duas vezes na mesma missão."""

    target_id = 2
    # O user já existe na lista de avaliadores
    existing_eval = EvaluatorModel(
        user_id=target_id,
        username="Helper",
        user_level_at_time=1,
        rank=EvaluationRank.A,
        xp_earned=10,
        coins_earned=10,
        evaluate_at=datetime.now()
    )
    mission = create_fake_mission(creator_id=1, evaluators=[existing_eval])

    mock_repos["mission"].get_by_id.return_value = mission
    mock_repos["user"].get_by_id.return_value = create_fake_user(user_id=target_id)

    success, msg = await service.evaluate_user(100, author_id=1, user_id=target_id, rank="S", guild=MagicMock())

    assert success is False
    assert "já foi avaliado" in msg


@pytest.mark.asyncio
async def test_evaluate_user_fail_not_author(service, mock_repos):
    """Testa regra: Somente o criador da missão pode avaliar."""

    mission = create_fake_mission(creator_id=1)  # Criado por 1
    mock_repos["mission"].get_by_id.return_value = mission
    mock_repos["user"].get_by_id.return_value = create_fake_user(user_id=2)

    # User 99 tenta avaliar
    success, msg = await service.evaluate_user(100, author_id=99, user_id=2, rank="S", guild=MagicMock())

    assert success is False
    assert "Somente o criador" in msg



@pytest.mark.asyncio
async def test_adjust_evaluation_success(service, mock_repos):
    """
    Testa o ajuste de C para S.
    Verifica se o usuário recebe apenas a diferença (Delta) de XP/Coins.
    """
    # Dados do Cenário
    # C -> S: (20->50 XP) e (50->125 Coins)
    OLD_XP, OLD_COINS = 20, 50
    NEW_XP, NEW_COINS = 50, 125
    DELTA_XP, DELTA_COINS = 30, 75

    target_id = 2
    mission_id = 100

    # Criamos a missão já com o avaliador antigo dentro
    old_eval = EvaluatorModel(
        user_id=target_id,
        username="Tester",
        user_level_at_time=1,
        rank=EvaluationRank.C,
        xp_earned=OLD_XP,
        coins_earned=OLD_COINS,
        evaluate_at=datetime.now()
    )

    mock_repos["mission"].get_by_id.return_value = create_fake_mission(mission_id, evaluators=[old_eval])
    mock_repos["user"].get_by_id.return_value = create_fake_user(user_id=target_id)

    # Configura os métodos que fazem ações (Action Mocks)
    mock_repos["mission"].update_evaluator = AsyncMock(return_value=True)
    mock_repos["leveling"].calculate_bonus = AsyncMock(return_value=(NEW_XP, NEW_COINS, ""))  # Retorna o Total Novo

    success, data = await service.adjust_evaluation(mission_id, target_id, "S", MagicMock())

    assert success is True

    # Valida se o retorno visual para o usuário mostra os DELTAS
    assert data == {
        "old_rank": EvaluationRank.C,
        "new_rank": EvaluationRank.S,
        "xp_diff": DELTA_XP,
        "coins_diff": DELTA_COINS
    }

    # Valida se entregou apenas a DIFERENÇA (Delta) de prêmio
    mock_repos["leveling"].grant_reward.assert_awaited_with(
        user_id=target_id, xp_amount=DELTA_XP, coins_amount=DELTA_COINS, guild=ANY
    )

    # Valida se salvou no banco o valor TOTAL
    # Acessamos direto o argumento nomeado usado na chamada
    saved_eval = mock_repos["mission"].update_evaluator.await_args.kwargs['evaluator_model']

    assert saved_eval.rank == EvaluationRank.S
    assert saved_eval.xp_earned == NEW_XP
    assert saved_eval.coins_earned == NEW_COINS

@pytest.mark.asyncio
async def test_report_evaluation_success(service, mock_repos):
    """Testa reportar uma missão onde o usuário participou."""

    reporter_id = 5
    participant = EvaluatorModel(
        user_id=reporter_id, username="Rep", user_level_at_time=1, rank=EvaluationRank.B,
        xp_earned=10, coins_earned=10, evaluate_at=datetime.now()
    )
    mission = create_fake_mission(evaluators=[participant])

    mock_repos["mission"].get_by_id.return_value = mission

    success, data = await service.report_evaluation(100, reporter_id, "Nota injusta")

    assert success is True
    assert data["reporter_id"] == reporter_id
    assert data["reason"] == "Nota injusta"


@pytest.mark.asyncio
async def test_report_evaluation_fail_not_participant(service, mock_repos):
    """Testa reportar uma missão onde o usuário NÃO participou."""
    mission = create_fake_mission(evaluators=[])  # Lista vazia
    mock_repos["mission"].get_by_id.return_value = mission

    success, msg = await service.report_evaluation(100, 999, "Reclamação")

    assert success is False
    assert "não foi avaliado" in msg
