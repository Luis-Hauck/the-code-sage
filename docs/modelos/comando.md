# Modelo de Documentação — Comando (Slash / Cog)

Preencha este modelo para documentar um comando do Discord no projeto.

## Resumo
- Nome do comando: `/nome`
- Cog/Arquivo: `src/cogs/xyz_cog.py`
- Para quem é: descreva rapidamente o público-alvo
- Resultado: o que o usuário obtém ao executar

## Parâmetros
- `param1` (tipo) — obrigatório/opcional — descrição e exemplos
- `param2` (tipo) — ...

## Comportamento
- O que o comando faz em alto nível
- Regras importantes, validações, limitações

## Fluxo interno
1. Recebe a interação do Discord
2. Chama `ServiceXYZ.metodo`
3. Monta Embed/View e responde

## Erros e mensagens
- Lista de mensagens de erro comuns e suas causas

## Exemplos de uso
- Capturas de tela (opcional)
- GIF/trecho de log/saída esperada

## Referências
- Service relacionado: `[ServiceXYZ](../referencias/servicos/servicexyz.md)` (criar se não existir)
- Repositórios: links
- Modelos: links
