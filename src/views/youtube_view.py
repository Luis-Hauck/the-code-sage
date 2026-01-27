import discord
from discord import ui

# Classe que define os botões da mensagem
class YoutubeView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        # Adiciona o botão de Link
        self.add_item(ui.Button(
            label="Acessar Canal Eitech",
            url="https://www.youtube.com/@Eitech",
            emoji="📺"  ))