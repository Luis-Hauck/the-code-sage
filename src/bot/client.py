import os
import discord
from discord.ext import commands
import logging
from src.app.config import GUILD_ID
from src.database.connection import connect_to_database


logger = logging.getLogger(__name__)


class TheCodeSageBot(commands.Bot):
    def __init__(self):
        # Herda da classe pai
        super().__init__(command_prefix='/', # Define o comando padrão
                         intents=discord.Intents.all() # Define as intents do bot
                         )
        self.db = None
        self.repositories ={}

    async def setup_hook(self):
        """"O hook é chamado automaticamente antes do bot logar"""

        # Conecta ao banco de dados e armazena a conexão na instância do bot
        self.db = await connect_to_database()

        # Inicializa cada repositório explicitamente
        #self.repositories["user"] = UserRepository(self.db)
        #self.repositories["item"] = ItemRepository(self.db)
        # ... e assim por diante

        #Carregamos todos os Cogs da pasta cogs
        # Percorremos cada arquivo da pasat cogs:
        for filename in os.listdir('./src/cogs'):
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

        if self.db:
            self.db.close()
            logger.info('Conexão com MongoDB encerrada.')

        await super().close()

        logger.info('Bot encerrado com sucesso!')


