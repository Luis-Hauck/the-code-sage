from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class MissionStatus(str, Enum):
    """
    Representa os status de uma missão.
    """
    OPEN = 'aberta' #missão criada recebendo resposta
    COMPLETED = 'concluida' # missão avaliada e aguardando ser fechada
    UNDER_REVIEW = 'sob_revisao' # missão em análise
    CLOSED = 'fechada'  # missão fechada e não pode mais er aberta

class EvaluationRank(str, Enum):
    """
    Representa os ranks das missões
    """
    S = 'S'
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'

    @property
    def score(self) -> int:
        """
        :return: A nota númerica de (0 a 5) associada ao rank
        """
        scores = {'S':5, 'A':4, 'B':3, 'C':2, 'D':1, 'E':0}

        return scores.get(self.value, 0)

    @property
    def description(self) -> str:
        """
        :return: A descrição dos ranks
        """
        descriptions ={
            'S':'Lendário',
            'A':'Excelente',
            'B': 'Bom',
            'C': 'Regular',
            'D': 'Ruim',
            'E': 'Falha na missão'

        }
        return descriptions.get(self.value, "Desconhecido")

    @property
    def color(self) -> int:
        """Retorna a cor em Hex (int) para Embeds do Discord."""
        colors = {
            "S": 0xFFD700,  # Dourado
            "A": 0x00FF00,  # Verde
            "B": 0x0000FF,  # Azul
            "C": 0xFFA500,  # Laranja
            "D": 0xFF0000,  # Vermelho
            "E": 0x808080   # Cinza
        }

        return colors.get(self.value, 0xFFFFFF)

    @classmethod
    def from_score(cls, score: int) -> "EvaluationRank":
        """Converte uma nota numérica para um Rank."""
        match score:
            case 5:
                return cls.S
            case 4:
                return cls.A
            case 3:
                return cls.B
            case 2:
                return cls.C
            case 1:
                return cls.D
            case _:
                return cls.E



class EvaluatorModel(BaseModel):
    """
    Representa um único avaliador dentro de uma missão.
    """
    # dados do usuário
    user_id: int
    username: str
    user_level_at_time: int

    # dados da avaliação
    rank: Optional[EvaluationRank] = None
    score: Optional[int] = None

    # recompensas recebidas
    xp_earned: int = 0
    coins_earned: int = 0

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
    status: MissionStatus = Field(default=MissionStatus.OPEN)
    evaluators: List[EvaluatorModel] = []
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True

