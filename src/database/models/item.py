from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from src.database.models.effects import AnyEffect, AnyPassiveEffect
class ItemType(str, Enum):
    """
    Modelo com os tipos de itens disponiveis
    """
    CONSUMABLE = "consumível"
    EQUIPPABLE = "equipável"
    ROLE = "cargo"


class ItemsModel(BaseModel):
    """
    Modelo de dados para os itens.

    item_id: (int) id único do item
    name: Nome do item
    description: Descrição do item
    price: Preço do item
    type: Tipo do item ["cargo", "item_consumivel", "badge"]
    effect: Efeito ao usar usar o item.
    passive_effects: Efeitos passivos que o item dá.

    """
    item_id: int = Field(alias='_id')
    name: str
    description: str
    price: int
    item_type: ItemType
    effect: Optional[AnyEffect] = Field(None, discriminator='type')
    passive_effects: List[AnyPassiveEffect] = []

    class Config:
        populate_by_name = True

