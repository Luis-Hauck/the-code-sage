import discord
from datetime import datetime
from typing import Optional

from discord.types import embed

from src.database.models.mission import EvaluationRank

def create_error_embed(title:str, message: str) -> discord.Embed:
    """Cria um embed padronizado de erro (vermelho).

    Args:
        title (str): Título do embed.
        message (str): Descrição detalhando o erro.

    Returns:
        discord.Embed: Objeto Embed configurado como erro.
    """
    return discord.Embed(title=title,
        description=message,
        color=discord.Color.red()
    )

def create_info_embed(title:str, message: str) -> discord.Embed:
    """Cria um embed informativo (azul/cinza).

    Args:
        title (str): Título do embed.
        message (str): Mensagem a ser exibida.

    Returns:
        discord.Embed: Objeto Embed configurado como informativo.
    """
    return discord.Embed(title=title,
        description=message,
        color=discord.Color.blue()
    )


class MissionEmbeds:

    @staticmethod
    def evaluation_success(target_user:discord.Member, rank:EvaluationRank, xp:int, coins:int) -> discord.Embed:
        """Gera o embed de avaliação do usuário.

        Args:
            target_user (discord.Member): Usuário avaliado.
            rank (EvaluationRank): Rank da avaliação.
            xp (int): Quantidade de XP ganho.
            coins (int): Quantidade de moedas ganhas.

        Returns:
            discord.Embed: Embed gerado com os detalhes da avaliação.
        """

        embed = discord.Embed(title=f'{target_user.display_name} Completou a missão!',
                              description=f'Obrigado por contribuir com a comunidade!',
                              color=discord.Color(rank.color)
                              )

        embed.set_thumbnail(url=rank.thumbnail_url)

        embed.add_field(name='Rank', value=rank.value, inline=True)
        embed.add_field(name='XP', value=xp, inline=True)
        embed.add_field(name='Moedas', value=coins, inline=True)
        embed.set_footer(text='Caso não tenha recebido sua avaliação ou acha ela foi injusta, use /review e iremos analisar!')


        return embed

    @staticmethod
    def mission_start(riddle_text) -> discord.Embed:
        """Gera o embed de início da missão com uma charada de apoio.

        Args:
            riddle_text (str): Texto da charada gerada para a missão.

        Returns:
            discord.Embed: Embed com instruções e a charada.
        """

        embed = discord.Embed(title='Missão criada!',
                              description=(f'*{riddle_text}*\n\n'
                                           f'> 💎 **Não esqueça de recompensar o Aventureiro que te ajudou!**\n'
                                           f"> Ao final, use o comando: `/avaliar`\n"
                                           f"> Isso garante **XP** e **Moedas** para quem te salvou.\n\n"
                                           "Se você completar a missão sozinho, use o comando `/encerrar_missão`."
                                           ),

                              color=discord.Color.from_rgb(88, 55, 250)
        )

        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1253476072553451590/1457068144194617445/ac215eaefff22d1b2a35e5a5b17c959b.gif?ex=695aa7f4&is=69595674&hm=69fc2329302bf888fb76287432c2f61b9bff11bdae2114b05e46fdc6783de7da&')
        embed.set_footer(text="Code Sage • Transformando dúvidas em XP")

        return embed

    @staticmethod
    def mission_report(mission_id: int, mission_title:str, reporter_id: int, reporter_name:str, current_rank:str, reason: str) -> embed.Embed:
        """Gera o embed de denúncia de missão.

        Args:
            mission_id (int): ID da missão.
            mission_title (str): Título da missão reportada.
            reporter_id (int): ID de quem reportou.
            reporter_name (str): Nome de quem reportou.
            current_rank (str): Rank atual do usuário que reporta.
            reason (str): Motivo do report.

        Returns:
            embed.Embed: Embed gerado com os detalhes do report.
        """

        embed = discord.Embed(title=f'Report da missão: {mission_title}',
                              description=f'Um usuário contestou uma avaliação.',
                              color=discord.Color.red(),
                              timestamp=datetime.now()
        )

        embed.add_field(name='Reportado por', value=f'{reporter_name} ({reporter_id})', inline=True)
        embed.add_field(name='ID da missão', value=mission_id, inline=True)
        embed.add_field(name='Rank atual', value=current_rank, inline=True)
        embed.add_field(name='Motivo do report', value=reason, inline=False)

        return embed

    @staticmethod
    def admin_adjustment(target_user:discord.Member, old_rank:EvaluationRank, new_rank:EvaluationRank, xp_diff:int, coins_diff:int) -> embed.Embed:
        """Gera o embed de ajuste administrativo de avaliação.

        Mostra a diferença de valores entre o rank antigo e o novo.

        Args:
            target_user (discord.Member): Usuário que recebeu o ajuste.
            old_rank (EvaluationRank): Rank anterior.
            new_rank (EvaluationRank): Novo rank.
            xp_diff (int): Diferença de XP entre os ranks.
            coins_diff (int): Diferença de moedas entre os ranks.

        Returns:
            embed.Embed: Embed gerado com os detalhes do ajuste.
        """

        embed = discord.Embed(title=f'Ajuste de rank realizado!',
                              description=f'O rank de {target_user.mention} foi ajustado pela moderação!.',
                              color=discord.Color(new_rank.color)
        )

        # Formata o saldo com sinal (+50 ou -50)
        xp_str = f"+{xp_diff}" if xp_diff > 0 else f"{xp_diff}"
        coins_str = f"+{coins_diff}" if coins_diff > 0 else f"{coins_diff}"

        embed.add_field(name='Rank antigo ⬇️', value=old_rank.value, inline=True)
        embed.add_field(name='Rank novo ⬆️', value=new_rank.value, inline=True)
        embed.add_field(name='Diferença de XP', value=xp_str, inline=True)
        embed.add_field(name='Diferença de Moedas', value=coins_str, inline=True)


        return embed

    @staticmethod
    def report_confirmation() -> discord.Embed:
        """Gera o feedback de confirmação após o usuário reportar uma avaliação.

        Returns:
            discord.Embed: Embed de confirmação para o usuário.
        """
        return discord.Embed(
            title='Denúncia Enviada',
            description="Nossa equipe de sábios moderadores irá analisar o caso.\n"
                        "Se a nota for ajustada, você receberá a diferença de XP/Moedas automaticamente.",
            color=discord.Color.green()
        )

class ShopEmbeds:

    @staticmethod
    def create_showcase() -> discord.Embed:
        """Gera o cabeçalho visual da loja.

        Returns:
            discord.Embed: Embed com o cabeçalho da loja.
        """

        embed = discord.Embed(title='💰 Mercado do Servidor',
                              description=("**BEM-VINDO À LOJA!**\n\n"
                                "Aqui você pode gastar suas preciosas moedas.\n"
                                "**Selecione um item no menu abaixo para ver o preço e comprar.**"
                            ),
                            color=discord.Color.from_rgb(46, 204, 113)

        )


        embed.set_footer(text='Aproveite as promoções enquanto durarem os estoques!')

        return embed

class InventoryEmbeds:

    @staticmethod
    def view_inventory(user_name: str, equipped_name: str, items_data: list[dict]) -> discord.Embed:
        """Gera o embed do inventário do usuário.

        Args:
            user_name (str): Nome do usuário para o título.
            equipped_name (str): Nome do item já equipado (ou 'Nenhum').
            items_data (list[dict]): Lista de itens no formato
                [{'name': str, 'qty': int, 'type': str, 'description': str}].

        Returns:
            discord.Embed: Embed com a listagem do inventário.
        """

        embed = discord.Embed(title=f'🎒 Inventário do {user_name}',
                              color=discord.Color.blue()
        )
        embed.add_field(name=f'⚔️ Item Equipado por {user_name}',
                        value=equipped_name,
                        inline=True
        )

        description_lines = []
        for item in items_data:
            line = f"**{item['qty']}x** **{item['name']}** - *({item['type']})*: *{item['description']}*"
            description_lines.append(line)

        embed.description = "\n".join(description_lines)

        return embed

class UserEmbeds:

    @staticmethod
    def view_profile(user_name:str, current_level:int, current_xp:int, xp_next_level:int, progress_percent: int,coin_balance:int, equipped_item_name:str) -> discord.Embed:
        """
        Gera o embed do perfil do usuário

        Args:
            current_level (str): Nivel atual do usuário;
            user_name (int): Nome do usuário;
            current_xp (int): XP do usuário
            xp_next_level (int): XP par ao próximo nível do usuário
            progress_percent (int): Progresso(%) par ao próximo nível.
            coin_balance (int): Moedas em caixa.
            equipped_item_name (str): Nome do item equipado
        Returns:
            discord.Embed: Embed com dados do inventário.
        """

        filled = int(progress_percent / 10)
        bar = "🟦" * filled + "⬜" * (10 - filled)

        embed = discord.Embed(title=f"🛡️ Perfil de {user_name}")
        embed.add_field(name="Progresso", value=f"{bar} **{progress_percent}%****\n`{current_xp} / {xp_next_level} XP`", inline=False)
        embed.add_field(name="Nível", value=f"🏆 **{current_level}**", inline=True)
        embed.add_field(name="Saldo", value=f"💰 **{coin_balance}**", inline=True)
        if equipped_item_name != "Nenhum item equipado":
            embed.add_field(name="Item equipado", value=f'⚔️ **{equipped_item_name}**', inline=False)


        return embed

class CodeSageEmbeds:

    @staticmethod
    def welcome_message(member:discord.Member) -> discord.Embed:
        """Mensagem de boas-vindas ao entrar no servidor.

        Args:
            member (discord.Member): Membro que entrou no servidor.

        Returns:
            discord.Embed: Embed de boas-vindas.
        """
        link_repo = 'https://github.com/Luis-Hauck/the-code-sage'

        embed = discord.Embed(title=f'🔥 Uma nova chama se acende na Code Cave!',
                              description=(f'Seja muito bem-vindo,{member.mention} ao servidor!\n'
                                          f'> Eu sou o **Code Sage**, o grande sábio deste servidor\n\n'
                                          f'**Além disso você sabia que eu sou um projeto Open Source?**'
                                          f'Você pode contribuir visitando o **[repositório do meu criador]({link_repo})**'
                                ),
                              color=discord.Color.blue()

                              )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="🧭 Primeiros Passos",
            value="• Leia as **[regras](#)**\n"
                  "• Escolha seus **[Cargos](#)**\n"
                  "• Apresente-se no **[Chat Geral](#)**",
            inline=True
        )


        embed.add_field(
            name="📺 O que você encontra no Eitech?",
            value=(
                "🚀 **Python & Automação**\n"
                "🧪 **Data Science e IA**\n"
                "🛠️ **Projetos Práticos (como este bot!)**\n"
                "🗣️ **Bate papo ao vivo**\n"
                f"**Clique no botão para conhecer!**"
            ),
            inline=False
        )

        embed.set_footer(
            text=f"Você é o membro nº {len(member.guild.members)} desta jornada.")


        return embed

    @staticmethod
    def welcome_back_message(member: discord.Member) -> discord.Embed:
        """Mensagem para usuários que retornaram ao servidor.

        Args:
            member (discord.Member): Membro que voltou ao servidor.

        Returns:
            discord.Embed: Embed de boas-vindas de retorno.
        """
        link_repo = 'https://github.com/Luis-Hauck/the-code-sage'

        embed = discord.Embed(
            title=f'🔄 O eco dos seus passos retorna à Code Cave!',
            description=(
                f'Bem-vindo de volta, {member.mention}!\n'
                f'> **O Code Sage guardou o seu lugar junto à fogueira.**\n\n'
                f'🧙‍♂️ *Conjurei um feitiço de memória:*\n'
                f'Seus **Cargos**, **XP** e **Itens** antigos foram restaurados com sucesso.\n\n'
                f'Enquanto você esteve fora, continuamos evoluindo! '
                f'Confira as novidades no **[repositório oficial]({link_repo})**.'
            ),
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=member.display_avatar.url)


        embed.add_field(
            name="📺 Enquanto você estava fora...",
            value=(
                "O canal **Eitech** continuou produzindo vídeos de:\n"
                "🚀 **Python & Automação**\n"
                "🧪 **Data Science e IA**\n"
                "🛠️ **Novos Projetos Práticos**\n"
                f"*Clique no botão abaixo para se atualizar!*"
            ),
            inline=False
        )

        embed.set_footer(
            text=f"A comunidade agora conta com {len(member.guild.members)} viajantes."
        )

        return embed


