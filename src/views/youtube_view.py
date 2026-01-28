from discord import ui

class YoutubeView(ui.View):
    """
    View que exibe um botão de acesso ao canal do YouTube.

    Mantém o timeout desativado para persistir na mensagem e permitir que
    usuários cliquem no link enquanto a mensagem estiver visível.
    """
    def __init__(self):
        """
        Inicializa a view e adiciona um botão de URL apontando para o canal Eitech.
        """
        super().__init__(timeout=None)

        # Adiciona o botão de Link (URL Button)
        self.add_item(ui.Button(
            label="Acessar Canal Eitech",
            url="https://www.youtube.com/@Eitech_",
            emoji="📺"
        ))