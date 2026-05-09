# Modelo de Documentação — Modelo de Dados (Entidade/Schema)

Use este modelo para documentar entidades em src/database/models/.

## Resumo
- Nome do modelo: `NomeModel`
- Arquivo: `src/database/models/nome.py`
- Descrição: o que esta entidade representa no domínio

## Campos
- `campo_a: tipo` — obrigatório/opcional — descrição e validações
- `campo_b: tipo` — valores possíveis, default
- Índices/Chaves: descrição de índices, chaves únicas, relações

## Relações
- Com outras entidades (1:N, N:N), chaves estrangeiras, referências

## Regras e validações
- Restrições de domínio aplicadas neste nível

## Exemplos
```json
{
  "_id": "...",
  "nome": "...",
  "xp": 1200,
  "nivel": 5
}
```

## Referências
- Repositórios que persistem este modelo: links
- Serviços que consomem este modelo: links
