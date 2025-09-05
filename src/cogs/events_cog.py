import logging
from discord.ext import commands
import discord

logger = logging.getLogger(__name__)

dados_thread = {}

# Criamos a classe dos eventos que herda commands.Cog
class EventsCog(commands.Cog):
    # Recebe o bot para interagirmos com ele
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Abra-kadabra 001001')
        logger.info(f'Abra-kadabra 001001')

    @commands.Cog.listener()
    async def on_member_join(self, member:discord.Member):
        """
            Envia uma mensagem de boas vindas no privado do membro
        Args:
            self():
            member(discord.Member): Recebe as informações do usuário do discord.

        Returns:
            Envia a mensagem de boas vindas ao úsuario.

            Se o úsario tem bloqueio de mensagens diretas retorna um erro.

        """

        await member.send(f'Olá seja bem-vindo ao canal {member.name}')

        # Logica de verificar se um usuario que saiu voltou e ativar ou criar um novo

    @commands.Cog.listener()
    async def on_thread_create(self, thread:discord.Thread):
        # Lógica de criar uma sessão com os dados do criar e a quantidade de pessoas avaliadas
        criador = thread.owner
        if thread.parent_id ==1402409945672060928:
            pass



    @commands.Cog.listener()
    async def on_member_remove(self, member:discord.Member):
        """Logica de inativar o usuário que saiu do servidor"""



# Função responsável por carregar os cogs
async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
    logger.info('Cog de eventos carregado com sucesso!')

