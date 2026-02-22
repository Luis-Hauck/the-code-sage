import discord
import httpx
import logging
import tempfile
from src.app.config import MISSION_CHANNEL_ID
from src.utils.embeds import create_error_embed


logger = logging.getLogger(__name__)
# Silencia o log de requisições do httpx
logging.getLogger("httpx").setLevel(logging.WARNING)

async def is_mission_channel(interaction: discord.Interaction) -> bool:
    """
    Verifica se o comando está sendo usado dentro de uma Thread de Missão válida.
    Se não estiver, já envia a mensagem de erro e retorna False.
    Args:
        interaction (discord.Interaction): Interação do comando.
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


async def download_direct_cert(url: str, suffix: str):
    if not url:
        return None
    display_url = f"{url[:35]}... (URL Protegida)"
    logger.info(f"Iniciando download de: {display_url}")
    try:
        # 'follow_redirects=True' garante que o Python siga o link seguro até o arquivo final
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(response.content)
            temp_file.close()
            return temp_file.name
    except Exception as e:
        logger.error(f"Erro ao baixar certificado com Hash: {e}")
        return None