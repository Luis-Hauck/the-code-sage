import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from pymongo.errors import DuplicateKeyError

from src.repositories.missions_repository import MissionRepository
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

@pytest.fixture()
def sample_evaluator() -> EvaluatorModel:
    """Cria um objeto do tipo EvaluatorModel"""
    return EvaluatorModel(
        user_id=555,
        rank=EvaluationRank.S,
        user_level_at_time=10,
        xp_earned=100,
        coins_earned=50,
        evaluate_at=datetime.today(),
        username='Luis'
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


async def test_add_participant_success(mock_db, sample_evaluator):
    """
    Testa registrar a nota de um usuário.
    Verifica se o filtro composto e o operador posicional ($) estão corretos.
    """
    mock_db.missions.update_one.return_value = MagicMock(modified_count=1)
    repo = MissionRepository(db=mock_db)

    mission_id = 101
    fixed_time = datetime.now()



    result = await repo.add_participant(
        mission_id=mission_id,
        evaluator_model=sample_evaluator
    )

    assert result is True

    mock_db.missions.update_one.assert_awaited_with(
        {
            "_id": mission_id,
            "evaluators.user_id": {'$ne': 555}
        },
        {
            "$push": {
                # O Pydantic gera o dicionário perfeito para você comparar
                'evaluators': sample_evaluator.model_dump()
            }
        }
    )


async def test_add_participant_mission_not_exist(mock_db, sample_evaluator):
    """
    Testa falha quando a missão não existe.
    """
    mock_db.missions.update_one.return_value = MagicMock(modified_count=0)
    mock_db.missions.count_documents.return_value = 0
    repo = MissionRepository(db=mock_db)



    result = await repo.add_participant(
        mission_id=9999,
        evaluator_model=sample_evaluator

    )

    assert result is False

async def test_update_evaluator_success(mock_db, sample_evaluator):
    """
    Testa o sucesso de uma atualização de uma pessoa avalaida na missão
    """
    mock_db.missions.update_one.return_value = MagicMock(matched_count=1)
    repo = MissionRepository(db=mock_db)

    mission_id = 101



    result = await repo.update_evaluator(mission_id=101,
                                   evaluator_model=sample_evaluator
    )

    assert result is True

    mock_db.missions.update_one.assert_awaited_with(
        {
            "_id": mission_id,
            "evaluators.user_id": sample_evaluator.user_id
        },
        {
            "$set": {
                'evaluators.$.level_at_time': sample_evaluator.user_level_at_time,
                'evaluators.$.rank': sample_evaluator.rank,
                'evaluators.$.coins_earned': sample_evaluator.coins_earned,
                'evaluators.$.xp_earned': sample_evaluator.xp_earned,
                'evaluators.$.evaluate_at': sample_evaluator.evaluate_at
            }
        }
    )

async def test_update_evaluator_fail(mock_db, sample_evaluator):
    """
    Testa a falha de uma atualizazação de uma pessoa avalaida na missão
    """
    mock_db.missions.update_one.return_value = MagicMock(matched_count=0)
    repo = MissionRepository(db=mock_db)

    mission_id = 107



    result = await repo.update_evaluator(mission_id=107,
                                   evaluator_model=sample_evaluator
    )

    assert result is False

