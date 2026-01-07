import logging
from discord.ext import commands
import discord
from datetime import datetime

from src.app.config import MISSION_CHANNEL_ID
from src.database.models.user import UserModel, UserStatus
from src.utils.embeds import MissionEmbeds, create_error_embed, create_info_embed

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
        Registra um novo membro no servidor,e se for alguém que retornou ativa ele.
        :param member: Objeto do membro que entrou.
        :return:
        """
        try:
            user_repo = self.bot.mission_service.user_repo

            user = UserModel(_id=member.id,
                             username=member.name,
                             xp=0,
                             coins=0,
                             inventory={},
                             equipped_item_id=None,
                             status=UserStatus.ACTIVE,
                             joined_at=datetime.now(),
                             role_ids=[]
                             )

            # Verifica se já existe
            exists = await user_repo.get_by_id(member.id)
            if not exists:
                await user_repo.create(user)
                await member.send(f'Olá seja bem-vindo ao servidor {member.name}')
            else:
                # Se o usuário já esxistia só atualiza o status para ativo
                await user_repo.update_status(member.id, UserStatus.ACTIVE)
                await member.send(f'Olá seja bem-vindo novamente {member.nick}')

        except Exception as e:
            logger.warning(f'Não foi possível registrar ou atualizar o usuário {member.id}: {e}', exc_info=True)


    @commands.Cog.listener()
    async def on_thread_create(self, thread:discord.Thread):
        # Lógica de criar uma sessão com os dados do criar e a quantidade de pessoas avaliadas
        if thread.parent_id == MISSION_CHANNEL_ID:

            # Tentamos pegar o conteúdo da mensagem inicial
            try:

                starter_message = await thread.fetch_message(thread.id)
                description = starter_message.content
            except Exception as e:
                logger.warning(f'Não foi possível pegar a mensagem da missão com id {thread.id}: {e}')

            service = self.bot.mission_service
            author_id = thread.owner_id

            if author_id:
                sucess = await service.register_mission(
                    mission_id=thread.id,
                    author_id=author_id,
                    title=thread.name,
                )

                if sucess:
                    embeb = MissionEmbeds.mission_start(riddle_text=description)
                    await thread.send(embed=embeb)
                    logger.info(f'Missão {thread.id} registrada no banco.')
                else:
                    logger.warning(f'Erro ao registrar missão {thread.id} no banco.')
        else:
            logger.warning('Não foi possível localizar o canal.')



    @commands.Cog.listener()
    async def on_member_remove(self, member:discord.Member):
        """Logica de inativar o usuário que saiu do servidor"""
        user_repo = self.bot.mission_service.user_repo
        await user_repo.update_status(member.id, UserStatus.INACTIVE)




# Função responsável por carregar os cogs
async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
    logger.info('Cog de eventos carregado com sucesso!')

