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
    equipped_item_id: Optional[int] = None
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    joined_at: datetime
    role_ids: List[int] = []

    class Config:
        populate_by_name = True

