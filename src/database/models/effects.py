from pydantic import BaseModel, Field
from typing import Literal, Union

class CoinBoostPassive(BaseModel):
    type: Literal['coin_boost']
    multiplier: float

class XpBoostPassive(BaseModel):
    type: Literal['xp_boost']
    multiplier: float

class GiveRoleEffect(BaseModel):
    type: Literal['role_effect']
    role_id: int



# Com Union AnyPassiveEffect e Effect pode receber mais tipos de objeto
AnyPassiveEffect = Union[CoinBoostPassive, XpBoostPassive]
AnyEffect = Union[GiveRoleEffect]
