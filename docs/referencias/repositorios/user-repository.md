# UserRepository

## Resumo
- Nome da classe: `UserRepository`
- Arquivo: `src/repositories/user_repository.py`
- Fonte de dados: MongoDB/Outro — Coleção: users
- Responsabilidade: Résponsável por operações na coleção de usuários, oferencendo métodos de criação, consulta e atualização.


## Métodos
- `create(user_model: Usermodel) -> bool`
  - Recebe um [UserModel]()
  - Cria um novo usuário no banco de dados.
  - Retorna True caso crie o usuário, False caso o contrário
- `update_status(user_id: int, status: UserStatus) -> bool` 
  - Atualiza o status do usuário com base no seu ID.
  - Pode atualizar para um desses status: ativo, inativo, banido, silenciado.
  - Retorna True caso crie o usuário, False caso o contrário
- `add_xp_coins(user_id: int, xp: int, coins: int) -> Optional[UserModel]`
  - Adiciona XP e moedas ao usuário pelo ID.
  - Caso seja para remover moedas ou xp passamos valores negativos:
    - Ex: UserRepository.add_xp_coins(self, xp:-5, coins:-5)
  - Retorna: 
    - UserModel: Caso não tenha nada para adicionar.
    - UserModel Atualizado: se encontrado
    - None: se o usuário não existir ou em caso de erro.
- `get_by_id(user_id:int) -> Optional[UserModel]`
  - Busca um usuário pelo ID.
  - Retorna:
    - UserModel: Caso o usuário seja encontrado.
    - None: Caso não consiga buscar o usuário pelo ID.
- `equip_item(user_id: int, item_id: int) -> bool`
  - Equipa um item no usuario caso ele tenha ele dísponivel no inventário.
  - Retorna:
    - True: Se a operação foi concluída (inclusive se o item já estava equipado)
    - False: Se o usuário não existir ou não possuir o item.
- `unequip_item(user_id: int) -> bool`
  - Romove o item atual que usuário tem equipado.
  - Retorna:
    - True: Se a operação foi processada (inclusive se já não havia item equipado)
    - False: Se o usuário não existir ou ocorrer erro.
- `add_item_to_inventory(user_id: int, item_id: int, quantity: int) -> bool`
  - Adiciona item(s) ao inventário do usuário.
  - Retorna:
    - True: Se a operação foi bem-sucedida ou se a quantidade era zero.
    - False: Se caso a qtd seja menor que zero ou em caso de erro.
- `remove_item_from_inventory(user_id: int, item_id: int, quantity: int = 1) -> bool`  
  - Remove item(s) do inventário do usuário.
  - Verifica se o usuário tem a qtd passada para ser retirada. 
  - Se remove tudo que o usuário tem também apagamos a chave do item no inventário.
  - Retorna:
    - True se removeu com sucesso, False caso contrário.
- `add_role(self, user_id: int, role_id: int) -> bool` 
  - Adiciona uma role (cargo do discord) ao usuário.
  - Retorna:
    - True: se adicionou com sucesso (ou se já possuía o cargo)
- `remove_role(self, user_id: int, role_id: int) -> bool`

## Contratos e garantias
- O que este repositório garante (ex.: id único, consistência mínima)
- Quando pode lançar exceção e quais

## Exemplos
```python
repo = NomeRepository(conn)
usuario = repo.obter_por_id(user_id)
```

## Referências
- Serviços que o utilizam: links
- Modelos/Entidades relacionados: links
