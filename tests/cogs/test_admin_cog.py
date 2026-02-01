import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import discord
from datetime import datetime

from src.cogs.admin_cog import AdminCog
from src.database.models.mission import EvaluationRank


@pytest.fixture
def mock_bot():
    """Cria um bot com a estrutura de serviços mockada."""
    bot = MagicMock()
    # Hierarquia: bot -> mission_service -> user_repo / adjust_evaluation
    bot.mission_service = MagicMock()
    bot.mission_service.user_repo = MagicMock()

    # Configura métodos async
    bot.mission_service.user_repo.create = AsyncMock()
    bot.mission_service.user_repo.get_by_id = AsyncMock()
    bot.mission_service.adjust_evaluation = AsyncMock()

    return bot


@pytest.fixture
def mock_interaction():
    """Cria uma interação completa do Discord mockada."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.channel.id = 100
    interaction.guild = MagicMock()
    return interaction


@pytest.fixture
def cog(mock_bot):
    """Instancia o Cog injetando o bot mockado."""
    return AdminCog(mock_bot)



@pytest.mark.asyncio
async def test_sync_users_mixed_scenario(cog, mock_bot, mock_interaction):
    """
    Testa a sincronização com:
    - 1 Humano novo (Deve criar)
    - 1 Humano existente (Deve ignorar)
    - 1 Bot (Deve pular)
    """
    repo = mock_bot.mission_service.user_repo

    # Membro Novo
    new_human = MagicMock(spec=discord.Member)
    new_human.bot = False
    new_human.id = 101
    new_human.name = "Novato"
    new_human.joined_at = datetime.now()

    # Membro Existente
    old_human = MagicMock(spec=discord.Member)
    old_human.bot = False
    old_human.id = 102
    old_human.name = "Veterano"
    old_human.joined_at = datetime.now()

    # bot
    robot = MagicMock(spec=discord.Member)
    robot.bot = True
    robot.id = 999

    mock_interaction.guild.members = [new_human, old_human, robot]

    # get_by_id chamado para 101 retorna None (Novo)
    # get_by_id chamado para 102 retorna Objeto (Existente)
    async def get_by_id_side_effect(user_id):
        if user_id == 101: return None
        if user_id == 102: return MagicMock()  # Usuário existe
        return None

    repo.get_by_id.side_effect = get_by_id_side_effect

    await cog.sync_users.callback(cog, mock_interaction)

    # Create deve ser chamado APENAS 1 vez (para o new_human)
    repo.create.assert_awaited_once()

    # Verifica argumentos do create
    args, _ = repo.create.await_args
    assert args[0].user_id == 101

    # Verifica a mensagem final (deve contar 1 novo e 1 ignorado)
    mock_interaction.followup.send.assert_awaited_once()
    msg_args, _ = mock_interaction.followup.send.await_args
    assert "Cadastrados: 1" in msg_args[0]
    assert "Já existiam: 1" in msg_args[0]


# --- TESTES DE ADJUST RANK ---

@pytest.mark.asyncio
@patch("src.cogs.admin_cog.is_mission_channel")  # Patch na função auxiliar
async def test_adjust_rank_success(mock_is_channel, cog, mock_bot, mock_interaction):
    """
    Testa o fluxo de sucesso do ajuste de rank.
    """
    # 1. Setup
    mock_is_channel.return_value = True  # Simula que estamos num canal de missão

    # Dados de sucesso que o Service retornaria
    fake_data = {
        "old_rank": EvaluationRank.C,
        "new_rank": EvaluationRank.S,
        "xp_diff": 50,
        "coins_diff": 100
    }
    mock_bot.mission_service.adjust_evaluation.return_value = (True, fake_data)

    target_user = MagicMock(spec=discord.Member)
    target_user.id = 555
    target_user.display_name = "TargetUser"

    # 2. Execução
    await cog.adjust_rank.callback(cog, mock_interaction, target_user, fake_data['new_rank'])

    # 3. Asserções
    # Verificou se é canal de missão?
    mock_is_channel.assert_called_once_with(mock_interaction)

    # Chamou o defer?
    mock_interaction.response.defer.assert_awaited_once()

    # Chamou o service corretamente?
    mock_bot.mission_service.adjust_evaluation.assert_awaited_with(
        mock_interaction.channel.id,  # 100
        target_user.id,  # 555
        fake_data['new_rank'],
        mock_interaction.guild
    )

    # Enviou o Embed de sucesso?
    mock_interaction.followup.send.assert_awaited_once()
    call_kwargs = mock_interaction.followup.send.await_args.kwargs
    assert "embed" in call_kwargs  # Garante que enviou um embed





