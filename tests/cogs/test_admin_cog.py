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
    bot.user_service = MagicMock() # Added user_service

    # Configura métodos async
    bot.mission_service.adjust_evaluation = AsyncMock()
    bot.user_service.sync_guild_users = AsyncMock() # Added sync_guild_users

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
    # Configura o retorno do Service
    # (created_count, ignored_count)
    mock_bot.user_service.sync_guild_users.return_value = (1, 1)

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

    await cog.sync_users.callback(cog, mock_interaction)

    # Verifica se o service foi chamado corretamente
    mock_bot.user_service.sync_guild_users.assert_awaited_once()

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
    # Passamos "S" (string) para simular o input real
    await cog.adjust_rank.callback(cog, mock_interaction, target_user, "S")

    # 3. Asserções
    # Verificou se é canal de missão?
    mock_is_channel.assert_called_once_with(mock_interaction)

    # Chamou o defer?
    mock_interaction.response.defer.assert_awaited_once()

    # Chamou o service corretamente?
    mock_bot.mission_service.adjust_evaluation.assert_awaited_with(
        mock_interaction.channel.id,  # 100
        target_user.id,  # 555
        "S",
        mock_interaction.guild
    )

    # Enviou o Embed de sucesso?
    mock_interaction.followup.send.assert_awaited_once()
    call_kwargs = mock_interaction.followup.send.await_args.kwargs
    assert "embed" in call_kwargs  # Garante que enviou um embed





