import asyncio
import logging

from src.database.models.item import ItemModel, ItemType
from src.database.models.effects import AddXpEffect, CoinBoostPassive, AddCoinsEffect, XpBoostPassive, GiveRoleEffect
from src.database.connection import connect_to_database
from src.repositories.item_repository import ItemRepository

logger = logging.getLogger(__name__)

async def seed_items():
    logger.info("Iniciando seed de itens")
    db = await connect_to_database()

    item_repo = ItemRepository(db)

    items_data = [
        # --- TIER 1: O Aventureiro Júnior (Iniciante) ---

        ItemModel(
            _id=1,
            name='Amuleto do "Hello World"',
            description='[+5% XP] O primeiro artefato que todo mago do código forja. Dá sorte em novos projetos.',
            price=500,  # ~4 Missões Rank S (Base: 125)
            item_type=ItemType.EQUIPPABLE,
            effect=None,
            passive_effects=[XpBoostPassive(type='xp_boost', multiplier=0.05)]
        ),
        ItemModel(
            _id=2,
            name='Botas do Git Commit',
            description='[+5% MOEDAS] Permite que você "salve seu progresso" e caminhe com segurança, evitando perder ouro.',
            price=625,  # ~5 Missões
            item_type=ItemType.EQUIPPABLE,
            effect=None,
            passive_effects=[CoinBoostPassive(type='coin_boost', multiplier=0.05)]
        ),
        ItemModel(
            _id=3,
            name='Pato de Borracha Ancestral',
            description='[+8% XP] Um pequeno espírito amarelo que ouve seus lamentos e desbloqueia sua lógica travada.',
            price=875,  # ~7 Missões
            item_type=ItemType.EQUIPPABLE,
            effect=None,
            passive_effects=[XpBoostPassive(type='xp_boost', multiplier=0.08)]
        ),

        # --- TIER 2: O Guerreiro Full-Stack (Intermediário) ---

        ItemModel(
            _id=4,
            name='Escudo Firewall Etéreo',
            description='[+10% MOEDAS] Bloqueia ataques de hackers e pacotes maliciosos, protegendo seu tesouro.',
            price=1500,  # ~12 Missões
            item_type=ItemType.EQUIPPABLE,
            effect=None,
            passive_effects=[CoinBoostPassive(type='coin_boost', multiplier=0.10)]
        ),
        ItemModel(
            _id=5,
            name='Espada "Debugger" Sagrada',
            description='[+12% XP] Uma lâmina capaz de cortar o "Spaghetti Code" mais denso e eliminar bugs com um golpe.',
            price=1850,  # ~15 Missões
            item_type=ItemType.EQUIPPABLE,
            effect=None,
            passive_effects=[XpBoostPassive(type='xp_boost', multiplier=0.12)]
        ),
        ItemModel(
            _id=6,
            name='Manoplas Mecânicas (Switch Azul)',
            description='[+15% MOEDAS] Cada clique ecoa como o som de moedas caindo. Aumenta drasticamente a velocidade de "farm".',
            price=2500,  # ~20 Missões
            item_type=ItemType.EQUIPPABLE,
            effect=None,
            passive_effects=[CoinBoostPassive(type='coin_boost', multiplier=0.15)]
        ),
        ItemModel(
            _id=7,
            name='Elmo da Visão Noturna (Dark Mode)',
            description='[+15% XP] Protege os olhos da luz branca cegante, permitindo longas jornadas de codificação nas masmorras.',
            price=3200,  # ~25 Missões
            item_type=ItemType.EQUIPPABLE,
            effect=None,
            passive_effects=[XpBoostPassive(type='xp_boost', multiplier=0.15)]
        ),

        # --- TIER 3: O Arquiteto Lendário (Endgame) ---

        ItemModel(
            _id=8,
            name='Grimório do Stack Overflow',
            description='[+25% XP] Contém as respostas para todas as perguntas do universo... exceto aquelas marcadas como duplicadas.',
            price=6500,  # ~52 Missões
            item_type=ItemType.EQUIPPABLE,
            effect=None,
            passive_effects=[XpBoostPassive(type='xp_boost', multiplier=0.25)]
        ),
        ItemModel(
            _id=9,
            name='Cetro do Root (Sudo)',
            description='[+30% MOEDAS] Concede autoridade absoluta sobre o sistema. O servidor obedece sem questionar.',
            price=8500,  # ~68 Missões
            item_type=ItemType.EQUIPPABLE,
            effect=None,
            passive_effects=[CoinBoostPassive(type='coin_boost', multiplier=0.30)]
        ),
        ItemModel(
            _id=10,
            name='Manto da Arquitetura Limpa',
            description='[+50% XP] Um tecido imaculado onde nenhum débito técnico ousa encostar. O código flui como magia pura.',
            price=15000,  # ~120 Missões
            item_type=ItemType.EQUIPPABLE,
            effect=None,
            passive_effects=[XpBoostPassive(type='xp_boost', multiplier=0.50)]
        )
    ]

    for item in items_data:
        logger.info(f"Criando item {item.name}")
        await item_repo.upsert(item)

if __name__ == "__main__":
    # Roda o loop async
    asyncio.run(seed_items())