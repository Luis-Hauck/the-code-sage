from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class MissionStatus(str, Enum):
    """Status possíveis de uma missão no ciclo de vida."""
    OPEN = 'aberta'  # missão criada, recebendo respostas
    COMPLETED = 'concluida'  # missão avaliada e aguardando ser fechada
    UNDER_REVIEW = 'sob_revisao'  # missão em análise
    CLOSED = 'fechada'  # missão fechada e não pode mais ser aberta

class EvaluationRank(str, Enum):
    """
    Representa os ranks das missões de S à E.
    """
    S = 'S'
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'

    @classmethod
    def get_or_none(cls, value: str):
        """Tenta retornar o Enum, se falhar retorna None."""
        try:
            return cls(value.upper())
        except ValueError:
            return None

    @property
    def score(self) -> int:
        """Nota numérica equivalente ao rank.

        Returns:
            int: Valor de 0 a 5 associado ao rank.
        """
        scores = {'S': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1, 'E': 0}
        return scores.get(self.value, 0)

    @property
    def description(self) -> str:
        """Descrição textual do rank.

        Returns:
            str: Texto amigável para o usuário.
        """
        descriptions = {
            'S': 'Lendário',
            'A': 'Excelente',
            'B': 'Bom',
            'C': 'Regular',
            'D': 'Ruim',
            'E': 'Falha na missão'
        }
        return descriptions.get(self.value, "Desconhecido")

    @property
    def color(self) -> int:
        """Cores em Hex para Embeds do Discord com base nos ranks.
        Returns:
            int: a cor em Hex (int) para Embeds do Discord."""
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

    @property
    def thumbnail_url(self) -> str:
        """URL da imagem associada ao rank para uso em Embeds.

        Returns:
            str: URL absoluta da imagem do rank.
        """

        images = {
            'S': 'https://cdn.discordapp.com/attachments/1253476072553451590/1456761385416659095/S.PNG?ex=69598a43&is=695838c3&hm=83504aedf15a2657971457a855daba094283c5579292308df47d344bc9dc0908&',
            'A': 'https://cdn.discordapp.com/attachments/1253476072553451590/1456761380832018522/A.PNG?ex=69598a42&is=695838c2&hm=fd422b48bc8dd54a4ef0727b76c3914502453ad1ea8cd61cc4d380d909cd469f&',
            'B': 'https://cdn.discordapp.com/attachments/1253476072553451590/1456761382300291102/B.PNG?ex=69598a42&is=695838c2&hm=425cfcf6f5bbb644b574cd3805bbaf50142b01906c71ebeb5fd4c440e9f15246&',
            'C': 'https://cdn.discordapp.com/attachments/1253476072553451590/1456761382878842931/C.PNG?ex=69598a42&is=695838c2&hm=53f37610366778c08c2fa722dcf50f313077ec1632b76eaf76335830cb1d8fce&',
            'D': 'https://cdn.discordapp.com/attachments/1253476072553451590/1456761383990460458/D.PNG?ex=69598a43&is=695838c3&hm=0b63800cc0747703991aa5c56f9e18fb335c96dc3bc87747a263caf038a046c6&',
            'E': 'https://cdn.discordapp.com/attachments/1253476072553451590/1456761384653164594/E.PNG?ex=69598a43&is=695838c3&hm=a34976596eaee5faa16d28e59597706a521454f1d5c7e92327afb8c618de5ae6&'
        }

        return images.get(self.value, '')


class EvaluatorModel(BaseModel):
    """
    Representa um usuário que foi avaliado em uma missõa.

    Attributes:
        user_id: ID único do Usuário avaliado.
        username: Nome do usuário avaliado.
        user_level_at_time: Nível que usuário estava quando completou a missão.
        rank: Rank que usuário recebeu na missão.
        xp_earned: Quantidade de experiência que o usuário recebeu na missão.
        coins_earned: Quantidade de moedas que o usuário recebeu na missão.
        evaluate_at: Horário em que o usuário foi avalaido.
    """
    # dados do usuário
    user_id: int
    username: str
    user_level_at_time: int

    # dados da avaliação
    rank: Optional[EvaluationRank] = None
    # recompensas recebidas
    xp_earned: int = 0
    coins_earned: int = 0
    evaluate_at: Optional[datetime] = None

class MissionModel(BaseModel):
    """
    Modelo de dados para missões.
    
    Attributes:
        mission_id: id da thread criada
        title: Titulo da missão(thread)
        creator_id: Criador da missão(thread)
        created_at: Data da criação da missão(thread)
        status: Estado atual da missão(thread).
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

