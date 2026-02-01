import os
import pathlib
import discord
from discord.ext import commands
import logging
from src.app.config import GUILD_ID


from src.database.connection import connect_to_database
from src.repositories.user_repository import UserRepository
from src.repositories.item_repository import ItemRepository
from src.repositories.missions_repository import MissionRepository
from src.repositories.level_rewards_repository import LevelRewardsRepository
from src.services.mission_service import MissionService
from services.leveling_service import LevelingService
from src.services.user_service import UserService
from src.services.sage_service import SageService


logger = logging.getLogger(__name__)


class TheCodeSageBot(commands.Bot):
    """Cliente principal do bot Code Sage.

    Responsável por inicializar repositórios, serviços, carregar cogs e
    sincronizar slash commands com o Discord.
    """
    def __init__(self):
        """Inicializa a instância do bot.

        Configura o prefixo de comandos e as intents necessárias. As
        dependências (repositórios/serviços) são configuradas no setup_hook.
        """
        # Herda da classe pai
        super().__init__(command_prefix='/', # Define o comando padrão
                         intents=discord.Intents.all() # Define as intents do bot
                         )
        self.rewards_repo = None
        self.mission_repo = None
        self.item_repo = None
        self.user_repo = None
        self.db = None
        self.mission_service = None
        self.leveling_service = None
        self.user_service = None
        self.sage_service = None


    async def setup_hook(self):
        """Configura as dependências e carrega os Cogs antes do login.

        Este hook é chamado automaticamente pelo discord.py antes do
        bot efetuar o login. Aqui conectamos ao banco, inicializamos
        repositórios e serviços, carregamos os cogs e sincronizamos os
        comandos de aplicativo (slash commands) no servidor de testes.
        """

        # Conecta ao banco de dados e armazena a conexão na instância do bot
        self.db = await connect_to_database()

        # Inicializa cada repositório explicitamente
        self.user_repo = UserRepository(self.db)
        self.item_repo = ItemRepository(self.db)
        self.mission_repo = MissionRepository(self.db)
        self.rewards_repo = LevelRewardsRepository(self.db)

        # inicializa os services
        self.leveling_service = LevelingService(self.user_repo, self.rewards_repo, self.item_repo)
        self.mission_service = MissionService(self.mission_repo, self.leveling_service,self.user_repo)
        self.user_service = UserService(self.user_repo, self.item_repo)
        self.sage_service = SageService()

        logger.info("Services e Repositories inicializados com sucesso!")

        #Carregamos todos os Cogs da pasta cogs
        current_path = pathlib.Path(__file__).parent
        cogs_path = current_path.parent /'cogs'
        # Percorremos cada arquivo da pasat cogs:

        for filename in os.listdir(cogs_path):
            # Se for um arquivo python e não iniciar com __
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    # Carregamos o cog, usamos [:-3] para retirar .py do arquivo
                    await self.load_extension(f'src.cogs.{filename[:-3]}')
                    logger.info(f'"src.cogs.{filename[:-3]}" carregado com sucesso!')

                except Exception as e:
                    logger.warning(f'Falha ao carregar o cog {filename[:-3]}: {e}')

        # Sincronizamos os slaah commands com o discord

        """
        Sincronizar globalmente:
        
        await self.tree.sync()
        """

        # sincronizar no servidor de testes
        guild_obj = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild_obj)
        await self.tree.sync(guild=guild_obj)

        logger.info(f'Hook criado com sucesso!')


    async def close(self):
        """Finaliza o bot e encerra recursos.

        Fecha a conexão com o banco (se aberta) e delega o encerramento
        ao método da classe base.
        """
        logger.info('Encerrando o bot...')

        if self.db is not None:
            self.db.close()
            logger.info('Conexão com MongoDB encerrada.')

        await super().close()

        logger.info('Bot encerrado com sucesso!')
