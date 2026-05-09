# Visão Geral do The Code Sage

Esta página apresenta, em alto nível, os principais componentes do projeto e como eles interagem. É um bom ponto de partida antes de ler referências detalhadas.

## Para quem é esta página
- Novos contribuidores que querem entender rapidamente a arquitetura.
- Mantenedores que precisam de um mapa mental do sistema.

## Arquitetura em alto nível

- Bot (Discord)
  - Cogs (src/cogs/*): camadas de comandos Slash e eventos do Discord.
- Serviços (src/services/*)
  - Regras de negócio e orquestração entre camadas.
- Repositórios (src/repositories/*)
  - Acesso a dados e persistência.
- Banco de Dados (src/database/*)
  - Modelos/entidades e conexão com o banco.
- Utilitários e Views (src/utils/*, src/views/*)
  - Suporte (embeds, helpers) e componentes visuais do Discord.

Um fluxo típico:
1) Usuário executa um comando (Cog)
2) Cog chama um Service
3) Service consulta/atualiza dados via Repository
4) Repository interage com os Models/DB
5) Service retorna um resultado para o Cog montar a resposta (Embed/View)

## Funcionalidades principais
- Leveling (XP, níveis, recompensas)
- Missões (criação, avaliação, ajuste)
- Economia (moedas, loja, inventário, equipar/desequipar)

## Próximos passos sugeridos
- Ler os Guias (docs/guias/README.md) para tarefas passo a passo
- Ver a Referência (docs/referencias/README.md) para detalhes por componente
- Explorar os Modelos (docs/modelos/) para documentar novas partes
