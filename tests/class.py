from src.database.models.item import ItemsModel, ItemType
from src.database.models.effects import XpBoostPassive

passiva = XpBoostPassive(type='xp_boost',multiplier=5.5)

item = ItemsModel(_id=5, description='texto', name='cajado', price=5.0, item_type=ItemType.EQUIPPABLE, passive_effects=passiva)

print(item.passive_effects)

