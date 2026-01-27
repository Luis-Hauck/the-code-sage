import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from pymongo.errors import DuplicateKeyError

from repositories.missions_repository import MissionRepository
from src.database.models.mission import MissionModel, MissionStatus, EvaluationRank, EvaluatorModel

pytestmark = pytest.mark.asyncio

@pytest.fixture()
def mock_db():
    """Fixture para criar um mock do banco de dados e da coleção
    """
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.missions = mock_collection
    return mock_db

@pytest.fixture()
def sample_mission() -> MissionModel:
    """Cria um objeto do tipo MissionModel"""
    return MissionModel(_id=555,
                        title='Missão teste',
                        creator_id=8855,
                        created_at=datetime.today(),
                        status=MissionStatus.OPEN,
                        evaluators=[EvaluatorModel(user_id=555,
                                                    username= 'Luis',
                                                    user_level_at_time= 5,
                                                    rank=EvaluationRank.A,
                                                    xp_earned= 5,
                                                    coins_earned = 0
                                                   )

                        ],
                        completed_at=datetime.today()
                   )


async def test_create_mission_sucess(mock_db, sample_mission):
    """Testa se o método create chama insert_one com os dados corretos."""
    mission_repo = MissionRepository(db=mock_db)
    result = await mission_repo.create(mission_model=sample_mission)

    assert result is True
    expected_data = sample_mission.model_dump(by_alias=True)
    mock_db.missions.insert_one.assert_awaited_with(expected_data)

async def test_create_mission_duplicate_key(mock_db, sample_mission):
    """Teste o método create pra verificar duplicatas"""
    mock_db.missions.insert_one.side_effect = DuplicateKeyError("duplicate key error")
    mission_repo = MissionRepository(db=mock_db)
    result = await mission_repo.create(mission_model=sample_mission)
    assert result is False


async def test_get_by_id_success(mock_db, sample_mission):
    """Testa se get_by_id retorna um UserModel quando o usuário é encontrado."""
    mock_db.missions.find_one.return_value = sample_mission.model_dump(by_alias=True)
    mission_repo = MissionRepository(db=mock_db)
    result = await mission_repo.get_by_id(sample_mission.mission_id)

    assert isinstance(result, MissionModel)
    assert result.mission_id == sample_mission.mission_id
    mock_db.missions.find_one.assert_awaited_with({'_id': sample_mission.mission_id})


async def test_get_by_id_not_found(mock_db):
    """Testa se get_by_id retorna None quando o usuário não é encontrado."""
    mock_db.missions.find_one.return_value = None
    mission_repo = MissionRepository(db=mock_db)
    result = await mission_repo.get_by_id(99999)
    assert result is None


async def test_update_status_success(mock_db):
    """Testa atualizar o status da missão."""
    mock_db.missions.update_one.return_value = MagicMock(matched_count=1)
    repo = MissionRepository(db=mock_db)

    result = await repo.update_status(mission_id=101, new_status=MissionStatus.COMPLETED)

    assert result is True
    # Verifica se enviou o $set correto
    args, _ = mock_db.missions.update_one.await_args
    assert args[0] == {'_id': 101}
    assert args[1]['$set']['status'] == MissionStatus.COMPLETED


async def test_register_evaluation_success(mock_db):
    """
    Testa registrar a nota de um usuário.
    Verifica se o filtro composto e o operador posicional ($) estão corretos.
    """
    mock_db.missions.update_one.return_value = MagicMock(matched_count=1)
    repo = MissionRepository(db=mock_db)

    mission_id = 101
    user_id = 555
    score = 5
    rank = EvaluationRank.S

    result = await repo.register_evaluation(
        mission_id=mission_id,
        user_id=user_id,
        score=score,
        rank=rank,
        level_at_time=10,
        xp=100,
        coins=50
    )

    assert result is True

    mock_db.missions.update_one.assert_awaited_with(
        {
            "_id": mission_id,
            "evaluators.user_id": user_id
        },

        {
            "$set": {
                'evaluators.$.user_id': 555,
                'evaluators.$.level_at_time': 10,
                'evaluators.$.rank': rank,
                'evaluators.$.score': score,
                'evaluators.$.coins': 50,
                'evaluators.$.xp': 100,

            }
        }
    )


async def test_register_evaluation_user_not_in_list(mock_db):
    """
    Testa falha quando o usuário não está na lista de avaliadores.
    (Matched count será 0 pois o filtro "evaluators.user_id" falhará)
    """
    mock_db.missions.update_one.return_value = MagicMock(matched_count=0)
    repo = MissionRepository(db=mock_db)

    result = await repo.register_evaluation(
        mission_id=101,
        user_id=999,
        score=5, rank=EvaluationRank.S,
        level_at_time=1, xp=0, coins=0
    )

    assert result is False


async def test_add_participant(mock_db):
    """Testa adicionar um usuário na lista de participantes"""
    mock_db.missions.update_one.return_value = MagicMock(modified_count=1)
    repo = MissionRepository(db=mock_db)

    new_participant = EvaluatorModel(user_id=999,
                                     username= 'Luis',
                                        user_level_at_time=1
                                     )

    result = await repo.add_participant(mission_id=101, evaluator_model=new_participant)

    assert result is True

    args, _ = mock_db.missions.update_one.await_args
    filtro_usado = args[0]
    update_usado = args[1]

    assert filtro_usado['_id'] == 101
    assert filtro_usado['evaluators.user_id'] == {'$ne':999}
    assert update_usado['$push']['evaluators']['user_id'] == 999


