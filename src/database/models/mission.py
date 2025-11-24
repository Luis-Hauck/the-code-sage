from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from enum import Enum

class MissionStatus(str, Enum):
    OPEN = 'aberta' #missão criada recebendo resposta
    COMPLETED = 'concluida' # missão avaliada e aguardando ser fechada
    UNDER_REVIEW = 'sob_revisao' # missão em análise
    CLOSED = 'fechada'  # missão fechada e não pode mais er aberta



class EvaluatorModel(BaseModel):
    """
    Representa um único avaliador dentro de uma missão.
    """
    user_id: int
    username: str
    rank: str

class MissionModel(BaseModel):
    """
    Modelo de dados para missões.
    mission_id: id da thread criada
    title: Titulo da thread
    creator_id: Criador da thread
    created_at: Data da criação da thread
    status:
    evaluators: Lista de Pessoas que foram avaliadas.
    """
    mission_id: int = Field(alias='_id')
    title: str
    creator_id: int
    created_at: datetime
    status: str
    evaluators: List[EvaluatorModel] = []

    class Config:
        populate_by_name = True

