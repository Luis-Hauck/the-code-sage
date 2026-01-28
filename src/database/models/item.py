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


class ItemModel(BaseModel):
    """Modelo de dados para itens da loja/inventário.

    Attributes:
        item_id (int): ID único do item (chave primária no banco). Alias: _id.
        name (str): Nome do item.
        description (str): Descrição do item para exibição.
        price (int): Preço do item em moedas.
        item_type (ItemType): Tipo do item (consumível, equipável ou cargo).
        effect (Optional[AnyEffect]): Efeito ativo aplicado ao usar o item.
        passive_effects (List[AnyPassiveEffect]): Efeitos passivos aplicados enquanto equipado.
    """
    item_id: int = Field(alias='_id')
    name: str
    description: str
    price: int
    item_type: ItemType
    effect: Optional[AnyEffect] = None
    passive_effects: List[AnyPassiveEffect] = []

    class Config:
        populate_by_name = True

