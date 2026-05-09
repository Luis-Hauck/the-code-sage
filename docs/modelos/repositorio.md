# Modelo de Documentação — Repositório (Acesso a Dados)

Use este modelo para documentar classes em src/repositories/.

## Resumo
- Nome da classe: `NomeRepository`
- Arquivo: `src/repositories/nome_repository.py`
- Fonte de dados: MongoDB/Outro — coleção/tabelas envolvidas
- Responsabilidade: descreva o que este repositório fornece

## Métodos
- `obter_por_id(id) -> Modelo` — descrição, filtros, projeções
- `criar(dto) -> Modelo` — validações, campos obrigatórios
- `atualizar(id, mudanças) -> bool` — política de atualização
- `listar(filtros) -> list[Modelo]` — paginação, ordenação

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
