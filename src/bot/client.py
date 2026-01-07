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


logger = logging.getLogger(__name__)


class TheCodeSageBot(commands.Bot):
    def __init__(self):
        # Herda da classe pai
        super().__init__(command_prefix='/', # Define o comando padrão
                         intents=discord.Intents.all() # Define as intents do bot
                         )
        self.db = None
        self.mission_service = None
        self.leveling_service = None


    async def setup_hook(self):
        """"O hook é chamado automaticamente antes do bot logar"""

        # Conecta ao banco de dados e armazena a conexão na instância do bot
        self.db = await connect_to_database()

        # Inicializa cada repositório explicitamente
        user_repo = UserRepository(self.db)
        item_repo = ItemRepository(self.db)
        mission_repo = MissionRepository(self.db)
        rewards_repo = LevelRewardsRepository(self.db)

        # inicializa os services
        self.leveling_service = LevelingService(user_repo, rewards_repo, item_repo)
        self.mission_service = MissionService(mission_repo, self.leveling_service,user_repo)

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
        """Hook chamado quando o bot é desligado"""
        logger.info('Encerrando o bot...')

        if self.db is not None:
            self.db.close()
            logger.info('Conexão com MongoDB encerrada.')

        await super().close()

        logger.info('Bot encerrado com sucesso!')


