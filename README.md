# 🧙‍♂️ The Code Sage

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Discord.py](https://img.shields.io/badge/Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white)![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)

[![YouTube](https://img.shields.io/badge/YouTube-Eitech-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@Eitech_)
[![Discord](https://img.shields.io/badge/Discord-Code%20Cave-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/bv7puNnqBB)
> **The Code Sage** é um bot de Discord que tem o objetivo de gamificar e aumentar o engamento de comunidades de desenvolvedores.
> Ele transforma interações no servidor em XP, níveis e recompensas.


## 📋 Principais Funcionalidades

* 🎮 **Sistema de Leveling:** Ganhe XP ao interagir e suba de nível.
* 📜 **Missões:** Participe de threads de desafios e receba avaliações.
* 🛍️ **Loja de Itens:** Gaste suas moedas (Coins) em itens que dão bônus de XP ou de moedas.
* 🛡️ **Cargos Automáticos:** Sincronização de cargos baseada no nível.
* ❓ **Charadas:** Com base na sua dúvida o **The Code Sage** gera uma charada para tentar resolver seu problema.

## ⚡ Como Funciona o Ciclo do Bot

1.  **Entrada:** Uma pessoa entra no servidor, nosso bot envia uma mensagem de boas vindas e cadastra ele no banco de dados.
2. **Criação:** Um membro cria um tópico de dúvida (Thread). O bot detecta e registra como uma "Missão Aberta".
3. **Resolução:** Outros membros ajudam na dúvida.
   1. **Autoresolução** Caso o usuário resolva o problema sozinho ele pode usar o comando `/encerrar_missao`
4. **Avaliação:** O autor usa `/avaliar` para dar uma nota (S, A, B...) a quem ajudou.
5. **Recompensa:** O bot calcula XP baseado na nota + itens equipados e deposita na conta do ajudante, caso ele suba de nível ele recebe o maior cargo compátivel.
   1. **Revisão:** Caso o usuário avaliado não goste da nota ele pode usar o comando `/solicitar_revisao`, que envia um alerta aos administardores.
   2. **Ajuste:** Caso o administardor perceba que á avaliação realmente não condiz com reposta ele usa o comando `/ajustar_avaliação`
6. **Compras:** Após ganhar suas moedas você pode utilizar a loja, mas antes disso o ADM precisa selecionar um canal e usar o comando `/abrir_loja`
7. **Inventário:** Você comprou seu item e quer saber o que tem? Use o comando `/inventario`
8. **Equipar:** item comprado, inventário checado, para equipar o item basta usar o comando `/equipar` e selecionar o item desejado.
9. **Desequipar:** Cansou do item e quer trocar? Utilize o comando `/desequipar` que irá remover o item atual apra o inventário.
10. **Perfil:** Quer checar suas informações pessoais? Use o comando `/perfil`, que você irá saber o que tem em caixa e quanto falta para o próximo nível.

## 🚀 Roadmap (O que vem por aí)

Aqui estão as funcionalidades planejadas para as próximas versões:

- [x] Sistema base de XP e Níveis.
- [x] Comandos de Administração (Sync e Ajustes).
- [x] **Integração com IA:** O The Code Sage analisará dúvidas e irá gerar charadas.
- [ ] **Dashboard:** Visualização de ranking dos usuários.
- [ ] **Comando Usar:** Até o momento o usuário só pode equipar um item, apesar de iniciarmos o processo de usar itens consumiveis.

Antes de começar, verifique se você atende aos seguintes requisitos:

* **Python 3.12+** instalado.
* **Poetry** (Gerenciador de dependências) instalado.
* Uma instância do **MongoDB** (Local ou Atlas).
* Um Bot criado no [Discord Developer Portal](https://discord.com/developers/applications).

## 🔧 Instalação e Execução

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/the-code-sage.git](https://github.com/seu-usuario/the-code-sage.git)
    cd the-code-sage
    ```

2.  **Instale as dependências:**
    ```bash
    poetry install
    ```

3.  **Configure as Variáveis de Ambiente:**
    * Duplique o arquivo `.env.example` e renomeie para `.env`.
    * Preencha com seu Token do Discord e URL do Mongo.
    ```ini
    DISCORD_TOKEN=seu_token_aqui
    MONGO_URI=mongodb://localhost:27017
    ```

4.  **Execute o Bot:**
    ```bash
    poetry run python src/main.py
    ```


## 🤝 Contribuindo

Contribuições são sempre bem-vindas! Veja o arquivo [CONTRIBUTING.md](docs/CONTRIBUTING.md)  para saber como começar.

## 📢 Comunidade

Quer ver o bot funcionando na prática, tirar dúvidas ou dar sugestões?
Entre no nosso servidor oficial:

[Entrar no Code Cave](https://discord.gg/bv7puNnqBB)

## 📝 Licença

Esse projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---
Feito com 💜 por [Luis Gustavo Hauck](https://github.com/Luis-Hauck)