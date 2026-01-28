from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum

class UserStatus(str, Enum):
    ACTIVE = 'ativo'
    INACTIVE = 'inativo'
    BANNED = 'banido'
    MUTED = 'silenciado'


class UserModel(BaseModel):
    """Modelo de usuário do Discord armazenado no banco.

    Mantém o estado do jogador: experiência, moedas, inventário, item equipado
    e status de atividade no servidor.

    Attributes:
        user_id (int): ID único do usuário no Discord. Alias: _id.
        username (str): Nome de exibição atual do usuário.
        xp (int): Total de experiência acumulada. Default: 0.
        coins (int): Saldo de moedas do usuário.
        inventory (Dict[int, int]): Mapa item_id -> quantidade no inventário.
        equipped_item_id (Optional[int]): ID do item atualmente equipado, se houver.
        status (UserStatus): Status do usuário (ativo, inativo, banido, silenciado).
        joined_at (datetime): Data/hora da primeira entrada no servidor.
        role_ids (List[int]): IDs de cargos do servidor armazenados para restauração.
    """
    user_id: int = Field(alias='_id')
    username: str
    xp: int = 0
    coins: int
    inventory: Dict[int, int] = {}
    equipped_item_id: Optional[int] = None
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    joined_at: datetime
    role_ids: List[int] = []

    class Config:
        populate_by_name = True

