import discord
from src.app.config import MISSION_CHANNEL_ID
from src.utils.embeds import create_error_embed

async def is_mission_channel(interaction: discord.Interaction) -> bool:
    """
    Verifica se o comando está sendo usado dentro de uma Thread de Missão válida.
    Se não estiver, já envia a mensagem de erro e retorna False.
    """
    # Verifica se é Thread e se o pai é o canal de missões
    if not isinstance(interaction.channel, discord.Thread) or interaction.channel.parent_id != MISSION_CHANNEL_ID:
        wrong_channel_embed = create_error_embed(
            title='Você não pode usar esse comando aqui!',
            message='Esse comando só pode ser usado dentro de uma missão'
        )
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=wrong_channel_embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=wrong_channel_embed, ephemeral=True)

        return False

    return True