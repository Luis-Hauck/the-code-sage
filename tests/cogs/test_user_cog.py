import pytest
from unittest.mock import MagicMock, AsyncMock
import discord
from src.cogs.user_cog import UserCog

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.user_service = MagicMock()
    # Configura métodos async do service
    bot.user_service.get_user_profile = AsyncMock()
    bot.user_service.get_user_inventory = AsyncMock()
    bot.user_service.equip_item = AsyncMock()
    bot.user_service.unequip_item = AsyncMock()
    return bot

@pytest.fixture
def mock_interaction():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.user.id = 123
    interaction.guild = MagicMock()
    return interaction

@pytest.fixture
def cog(mock_bot):
    return UserCog(mock_bot)

@pytest.mark.asyncio
async def test_view_profile_success(cog, mock_bot, mock_interaction):
    # Setup
    fake_profile = {
        "username": "Tester",
        "current_level": 5,
        "current_xp": 500,
        "xp_next_level": 1000,
        "progress_percent": 50,
        "coin_balance": 100,
        "equipped_item_name": "Espada de Madeira"
    }
    mock_bot.user_service.get_user_profile.return_value = fake_profile

    # Execução
    await cog.view_profile.callback(cog, mock_interaction)

    # Asserções
    mock_bot.user_service.get_user_profile.assert_awaited_once_with(123, mock_interaction.guild)
    mock_interaction.followup.send.assert_awaited_once()
    # Verifica se enviou embed
    kwargs = mock_interaction.followup.send.await_args.kwargs
    assert "embed" in kwargs

@pytest.mark.asyncio
async def test_view_inventory_empty(cog, mock_bot, mock_interaction):
    # Setup: inventory vazio
    mock_bot.user_service.get_user_inventory.return_value = ("Tester", "Nada", [])

    # Execução
    await cog.view_inventory.callback(cog, mock_interaction)

    # Asserções
    mock_bot.user_service.get_user_inventory.assert_awaited_once_with(123)
    mock_interaction.followup.send.assert_awaited_once()
    # Verifica mensagem de erro/aviso no embed
    kwargs = mock_interaction.followup.send.await_args.kwargs
    embed = kwargs['embed']
    assert embed.title == 'Seu inventário está vazio!'

@pytest.mark.asyncio
async def test_equip_item_success(cog, mock_bot, mock_interaction):
    # Setup
    mock_bot.user_service.equip_item.return_value = (True, "Sucesso")

    # Execução
    await cog.equip_item.callback(cog, mock_interaction, item=99)

    # Asserções
    mock_bot.user_service.equip_item.assert_awaited_once_with(user_id=123, item_id=99)
    mock_interaction.followup.send.assert_awaited_once()
    kwargs = mock_interaction.followup.send.await_args.kwargs
    embed = kwargs['embed']
    assert embed.title == 'Item equipado com sucesso!'

@pytest.mark.asyncio
async def test_unequip_item_failure(cog, mock_bot, mock_interaction):
    # Setup: falha ao desequipar
    mock_bot.user_service.unequip_item.return_value = (False, "Erro ao desequipar")

    # Execução
    await cog.unequip_item.callback(cog, mock_interaction)

    # Asserções
    mock_bot.user_service.unequip_item.assert_awaited_once_with(123)
    kwargs = mock_interaction.followup.send.await_args.kwargs
    embed = kwargs['embed']
    assert embed.title == 'Falha ao desequipar o item'
