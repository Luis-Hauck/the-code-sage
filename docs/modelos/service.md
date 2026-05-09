# Modelo de Documentação — Serviço (Regra de Negócio)

Use este modelo para documentar um Service em src/services/.

## Resumo
- Nome da classe: `NomeService`
- Arquivo: `src/services/nome_service.py`
- Responsabilidade: descreva em 1–2 linhas o que este serviço faz

## Principais métodos
- `metodo_a(params) -> Tipo` — o que faz, quando usar
- `metodo_b(params) -> Tipo` — validações e efeitos colaterais

## Dependências
- Repositórios utilizados: links para docs
- Outros serviços: links

## Fluxo típico
1. Entrada/trigger (quem chama e quando)
2. Validações principais
3. Acesso a dados (repositories)
4. Regras de negócio aplicadas
5. Resultado retornado

## Erros e exceções
- Liste exceções esperadas e como tratá‑las nas camadas superiores

## Exemplos
```python
# Exemplo de uso sintético
service = NomeService(...)
resultado = service.metodo_a(param)
```

## Referências
- Comandos que usam este serviço: links
- Repositórios relacionados: links
- Modelos/Entidades: links
