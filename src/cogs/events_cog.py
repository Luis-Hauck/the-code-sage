import asyncio
import logging
from discord.ext import commands
import discord
from datetime import datetime

from services.sage_service import SageService
from services.mission_service import MissionService
from src.app.config import MISSION_CHANNEL_ID
from src.database.models.user import UserModel, UserStatus
from src.utils.embeds import MissionEmbeds, CodeSageEmbeds
from src.views.youtube_view import YoutubeView

logger = logging.getLogger(__name__)


# Criamos a classe dos eventos que herda commands.Cog
class EventsCog(commands.Cog):
    """Eventos globais do servidor (entradas, saídas e threads)."""
    # Recebe o bot para interagirmos com ele
    def __init__(self, bot:commands.Bot):
        """Inicializa o Cog de eventos.

        Args:
            bot (commands.Bot): Instância principal do bot.
        """
        self.bot = bot
        self.sage_service: SageService = bot.sage_service
        self.mission_service: MissionService = bot.mission_service

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f'Bot Ligado!')

    @commands.Cog.listener()
    async def on_member_join(self, member:discord.Member):
        """Registra um novo membro no servidor ou reativa quem retornou.
        Insere novos membros no banco de dados e envia um embed de boas-vindas.

        Args:
            member (discord.Member): Membro que entrou no servidor.
        """
        try:
            user_repo = self.mission_service.user_repo

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
                welcome_embed = CodeSageEmbeds.welcome_message(member=member)
                await member.send(embed=welcome_embed,
                                  view=YoutubeView())
            else:
                # Se o usuário já existia só atualiza o status para ativo
                await user_repo.update_status(member.id, UserStatus.ACTIVE)
                welcome_back_embed = CodeSageEmbeds.welcome_back_message(member=member)
                await member.send(embed=welcome_back_embed,
                                  view=YoutubeView())

                # Adiciona os cargos antigos do servidor
                for role_id in exists.role_ids:
                    role_obj = member.guild.get_role(role_id)

                    if role_obj:
                        try:
                            await member.add_roles(role_obj, reason="Restaurando cargos antigos")
                        except discord.Forbidden:
                            print(f"Sem permissão para dar o cargo {role_id}")

        except Exception as e:
            logger.warning(f'Não foi possível registrar ou atualizar o usuário {member.id}: {e}', exc_info=True)


    @commands.Cog.listener()
    async def on_thread_create(self, thread:discord.Thread):
        """
        Evento que capta uma nova thread criada no servidor e registra no banco.
        Além de enviar uma embed na thread.
        Args:
            thread (discord.Thread): Representa uma thread criada no servidor.
        """
        # Lógica de criar uma sessão com os dados do criar e a quantidade de pessoas avaliadas
        if thread.parent_id == MISSION_CHANNEL_ID:
            description = ''

            # Tentamos pegar o conteúdo da mensagem inicial
            try:
                # Aguardamos um pouco para que a mensagem seja criada
                await asyncio.sleep(1)

                starter_message = await thread.fetch_message(thread.id)
                description = starter_message.content

                # Se não estiver no cache busca no histórico
                if not starter_message:
                    async for message in thread.history(limit=1, oldest_first=True):
                        starter_message = message
                        break
                # Se encontrou a mensagem extrai texto e imagem
                if starter_message:
                    if starter_message.content:
                        description = starter_message.content

                # Verifica se tem anexos e se o primeiro é uma imagem
                if starter_message.attachments:
                    first_attachment = starter_message.attachments[0]
                    if first_attachment.content_type and first_attachment.content_type.startswith('image/'):
                        image_bytes = await first_attachment.read()

            except Exception as e:
                logger.warning(f'Não foi possível pegar a mensagem da missão com id {thread.id}: {e}')

            service = self.mission_service
            author_id = thread.owner_id

            if author_id:
                sucess = await service.register_mission(
                    mission_id=thread.id,
                    author_id=author_id,
                    title=thread.name,
                )

                if sucess:
                    riddle_text = await self.sage_service.generate_riddle(
                        title=thread.name,
                        description=description,
                        image_bytes=image_bytes
                    )
                    embeb = MissionEmbeds.mission_start(riddle_text=riddle_text)
                    await thread.send(embed=embeb)
                    logger.info(f'Missão {thread.id} registrada no banco.')
                else:
                    logger.warning(f'Erro ao registrar missão {thread.id} no banco.')
        else:
            logger.warning('Não foi possível localizar o canal.')



    @commands.Cog.listener()
    async def on_member_remove(self, member:discord.Member):
        """
        Evento que captura quando um membro sai do servidor.
        Atualiza seu status no banco de dados e adciona os cargos antigos.
        Args:
            member (discord.Member): Membro que saiu do servidor.
        """
        # Logica de inativar o usuário que saiu do servidor
        user_repo = self.mission_service.user_repo
        await user_repo.update_status(member.id, UserStatus.INACTIVE)

        # Salvamos os cargos atuais caso o usário volte
        for role in member.roles:
            if not role.is_default() and not role.is_bot_managed():
                await user_repo.add_role(member.id, role.id)
                logger.info(f'{member.name} Saiu do servidor e guardamos os seus cargos')




# Função responsável por carregar os cogs
async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
    logger.info('Cog de eventos carregado com sucesso!')

