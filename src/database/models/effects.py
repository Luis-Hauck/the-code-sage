from pydantic import BaseModel, Field
from typing import Literal, Union, Annotated


class AddXpEffect(BaseModel):
    type: Literal["add_xp"]
    amount: int

class AddCoinsEffect(BaseModel):
    type: Literal["add_coins"]
    amount: int

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
AnyPassiveEffect = Annotated[Union[
    CoinBoostPassive, XpBoostPassive],
    Field(discriminator='type')
]

AnyEffect = Annotated[Union[
    GiveRoleEffect,
    AddXpEffect,
    AddCoinsEffect],
    Field(discriminator='type')
]
