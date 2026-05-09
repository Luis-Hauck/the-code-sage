# Exemplo prático — Documentando um Service real (UserService)

Este exemplo usa um trecho real do projeto para mostrar “como ficaria” a documentação de um Service em docs/.
Ele segue o modelo em docs/modelos/servico.md, mas já preenchido para o UserService.

## Resumo
- Nome da classe: `UserService`
- Arquivo: `src/services/user_service.py`
- Responsabilidade: consolidar regras de usuário, como montar o perfil (/perfil), exibir inventário, equipar e desequipar itens e sincronizar cargos por nível.

## Principais métodos (exemplos)
- `get_user_profile(user_id: int, guild) -> dict | None`
  - Retorna dados para o comando `/perfil` (nível atual, progresso, saldo e item equipado).
- `get_user_inventory(user_id: int) -> tuple[str|None, str|None, list[dict]]`
  - Retorna nome, item equipado e a lista de itens do inventário para o `/inventário`.
- `equip_item(user_id: int, item_id: int) -> tuple[bool, str]`
  - Valida se o item existe, pertence ao usuário e é “equipável”, e então equipa.
- `unequip_item(user_id: int) -> tuple[bool, str]`
  - Remove o item atualmente equipado, voltando-o ao inventário.

## Dependências
- Repositórios
  - `UserRepository` (src/repositories/user_repository.py)
  - `ItemRepository` (src/repositories/item_repository.py)
- Serviços
  - `LevelingService` (src/services/leveling_service.py) — cálculo e sincronização de nível/cargos.

## Fluxo típico: get_user_profile
1. Busca o usuário no `UserRepository`.
2. Calcula nível e progresso via `LevelingService` (se injetado) e sincroniza cargos no `guild`.
3. Se houver item equipado, resolve o nome via `ItemRepository`.
4. Retorna um dicionário pronto para uso na camada de apresentação (Embeds).

Trecho real (resumido) de src/services/user_service.py:

```python
async def get_user_profile(self, user_id: int, guild) -> Optional[Dict[str, Any]]:
    user_data = await self.user_repo.get_by_id(user_id)
    if not user_data:
        return None

    if self.leveling_service:
        current_level = self.leveling_service.calculate_level(user_data.xp)
        await self.leveling_service.sync_roles(
            user_id=user_data.user_id,
            current_level=current_level,
            guild=guild
        )
        user_progress = self.leveling_service.get_user_progress(total_xp=user_data.xp)
    else:
        current_level = 0
        user_progress = {'relative_xp': 0, 'needed_xp': 100, 'percentage': 0}

    equipped_item_name = "Nenhum item equipado"
    if user_data.equipped_item_id and self.item_repo:
        equipped_item = await self.item_repo.get_by_id(user_data.equipped_item_id)
        if equipped_item:
            equipped_item_name = equipped_item.name

    return {
        "username": user_data.username,
        "current_level": current_level,
        "current_xp": user_progress['relative_xp'],
        "xp_next_level": user_progress['needed_xp'],
        "progress_percent": user_progress['percentage'],
        "coin_balance": user_data.coins,
        "equipped_item_name": equipped_item_name
    }
```

Relação com o comando `/perfil` (src/cogs/user_cog.py):

```python
profile_data = await self.user_service.get_user_profile(user_id, guild)
# Dados retornados alimentam o Embed de perfil
```

## Validações e regras: equip_item
- Verifica se o usuário existe e se o item existe no banco.
- Garante que o item está no inventário do usuário.
- Garante que o item é do tipo `EQUIPPABLE`.
- Se tudo ok, marca o item como equipado no repositório.

Trecho real (resumido):

```python
async def equip_item(self, user_id: int, item_id: int) -> Tuple[bool, str]:
    user = await self.user_repo.get_by_id(user_id)
    item = await self.item_repo.get_by_id(item_id)
    if not user:
        return False, "Usuário não encontrado."
    if not item:
        return False, "Item não existe no banco de dados."
    if item_id not in user.inventory:
        return False, "Você não possui este item. Compre-o primeiro!"
    if item.item_type != ItemType.EQUIPPABLE:
        return False, f"O item '{item.name}' não pode ser equipado (Tipo: {item.item_type.value})."

    await self.user_repo.equip_item(user_id, item_id)
    return True, "Item equipado com sucesso!"
```

Relação com o comando `/equipar` (src/cogs/user_cog.py):

```python
sucess, message = await self.user_service.equip_item(
    user_id=interaction.user.id,
    item_id=item
)
```

## Erros e exceções esperadas
- Usuário não encontrado → retorna `(False, "Usuário não encontrado.")` nos casos de ação, ou `None` no `get_user_profile`.
- Item inexistente → `(False, "Item não existe no banco de dados.")`.
- Item fora do inventário → `(False, "Você não possui este item. Compre-o primeiro!")`.
- Item não equipável → `(False, "O item 'X' não pode ser equipado...")`.

## Exemplos rápidos de uso (pseudo-código)
```python
service = UserService(user_repo, item_repo, leveling_service)
perfil = await service.get_user_profile(user_id=123, guild=guild)
status, msg = await service.equip_item(user_id=123, item_id=456)
```

## Referências
- Comandos relacionados: 
  - `/perfil` e `/equipar` em `src/cogs/user_cog.py`
- Repositórios relacionados:
  - `src/repositories/user_repository.py`
  - `src/repositories/item_repository.py`
- Serviço relacionado:
  - `src/services/leveling_service.py`
