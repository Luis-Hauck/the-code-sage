from src.bot.client import TheCodeSageBot
from src.app.config import DISCORD_TOKEN
from src.app.logging_ import setup_logging

setup_logging()

def main():
    bot = TheCodeSageBot()
    bot.run(DISCORD_TOKEN)

if __name__ == '__main__':
    main()



