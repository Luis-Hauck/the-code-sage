from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class UserStatus(str, Enum):
    ACTIVE = 'ativo'
    INACTIVE = 'inativo'
    BANNED = 'banido'
    MUTED = 'silenciado'


class UserModel(BaseModel):
    """
    Modelo de dados para o usuário
    """
    user_id: int = Field(alias='_id')
    username: str
    xp: int = 0
    coins: int
    inventory: List[str] = []
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    joined_at: datetime
    roles_id: List[int] = []

    class Config:
        populate_by_name = True

class EvaluatorModel(BaseModel):
    """
    Representa um único avaliador dentro de uma missão.
    """
    user_id: int
    username: str
    rank: str

class MissionsModel(BaseModel):
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

class ItemsModel(BaseModel):
    """
    Modelo de dados para os itens.

    item_id (int) id único do item
    name: Nome do item
    description: Descrição do item
    price: Preço do item
    type: Tipo do item ["cargo", "item_consumivel", "badge"]
    role_id_to_give: ID do cargo a ser concedido
    expire_date: Data de expiração do item

    """
    item_id: int = Field(alias='_id')
    name: str
    description: str
    price: int
    type: str
    role_id_to_give: Optional[int] = None
    expire_date: datetime

    class Config:
        populate_by_name = True

