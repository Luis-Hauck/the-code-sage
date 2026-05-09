# Guia rápido: como criar e organizar a documentação (docs/)

Esta pasta concentra toda a documentação em Markdown (.md). Você pode criar subpastas e páginas conforme o projeto evolui.

Objetivo: tornar fácil para qualquer pessoa entender, usar e contribuir com o The Code Sage.

## Estrutura sugerida
- conceitos/ — visão geral e explicações de arquitetura
- guias/ — tutoriais passo a passo (instalação, deploy, seeds, etc.)
- referencias/ — documentação por componente (comandos, serviços, repositórios, modelos)
- modelos/ — arquivos-modelo prontos para copiar e preencher
- exemplos/ — páginas curtas demonstrando padrões de escrita

Sinta-se à vontade para adaptar a estrutura conforme surgirem novas necessidades.

## Por onde começar?
- Leia a visão geral: [conceitos/visao-geral.md](conceitos/visao-geral.md)
- Escolha criar um Guia, uma Referência ou ambos (veja decisões abaixo)
- Use um arquivo de [modelos/](modelos/) para acelerar

## O que documentar: por ação (comando) ou por parte lógica?

Regra prática:
- Documente por ação quando for algo que o usuário final executa diretamente (Slash Commands do Discord).
- Documente por parte lógica quando o foco for a regra de negócio ou código reutilizável (Services, Repositories, Models).

Na dúvida, faça os dois: uma página simples para o comando (o que faz, parâmetros e exemplos) e outra para o serviço correspondente (detalhes internos e regras).

Critérios rápidos
- Comandos (Cogs): nome, parâmetros, comportamento, mensagens de erro, exemplos visuais.
- Serviços: responsabilidade, principais métodos, fluxo, validações, exceções.
- Repositórios: fonte de dados, métodos de acesso, contratos e erros.
- Modelos/Entidades: campos, tipos, validações, relacionamentos.

Modelos prontos
- Comando: [modelos/comando.md](modelos/comando.md)
- Serviço: [modelos/servico.md](referencias/servicos/user-service.md)
- Repositório: [modelos/repositorio.md](modelos/repositorio.md)
- Modelo de dados: [modelos/modelo-de-dados.md](modelos/modelo-de-dados.md)

## Boas práticas de escrita
- Uma única H1 (#) por página; use H2/H3 para seções
- Comece com “para quem é” e “o que resolve”
- Prefira exemplos curtos e verificáveis
- Inclua links entre páginas relacionadas
- Verifique os caminhos relativos antes de abrir PR

## Índice rápido
- Conceitos: [conceitos/visao-geral.md](conceitos/visao-geral.md)
- Guias: [guias/README.md](guias/README.md)
- Referências: [referencias/README.md](referencias/README.md)
- Exemplos: 
  - [exemplos/primeiros-passos.md](exemplos/primeiros-passos.md)
  - [exemplos/exemplo-com-codigo.md](exemplos/exemplo-com-codigo.md)
  - [exemplos/exemplo-user-service.md](exemplos/exemplo-user-service.md)

Bom trabalho e boas contribuições!
