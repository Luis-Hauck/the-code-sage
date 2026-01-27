from google import genai
from google.genai import types
import logging

from src.app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Intruções para o estilo do personagem Code Sage
SAGE_SYSTEM_INSTRUCTION = (
    "Você é o 'Code Sage', um mago ancestral da programação. "
    "Sua sabedoria é vasta como a nuvem e antiga como o Assembly. "
    "Seu tom é enigmático, sereno e cheio de metáforas"
    "mas você sempre relaciona os conceitos com tecnologia, código e lógica. "
    "Nunca dê a resposta direta e só retorne a charada dentro de."
)


class SageService:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_id = 'gemini-3-flash-preview'

    async def generate_riddle(self, title: str, description: str,image_bytes:bytes=None, difficulty: str = "difícil") -> str:
        """
        Gera a charada da missão para ajudar o usuário
        :param title: Título da missão
        :param description: Descrição da missão
        :param image_bytes: Bits que representama imagem em anexo da missão.
        :param difficulty: Nível de dificuldade da missão, padrão dificil
        :return: O texto da charada
        """



        prompt = (
                f"Analise esta missão de programação:\n"
                f"Título: {title}\n"
                f"Descrição: {description}\n"
                f"Dificuldade: {difficulty}\n\n"
                "TAREFA:\n"
                "1. Crie uma charada curta (máximo 4 linhas) que dê uma dica sobre a solução, mas sem entregar de bandeja.\n"
                "2. Se houver uma imagem anexa, use detalhes visuais dela na charada.\n"
                "3. Retorne só a charada dentro de aspas duplas e sem quebra de texto"

            )

        # Criamos uma lista para os conteúdos enviados
        contents = [prompt]

        # Se tiver imagem, empacotamos ela e adicionamos na lista
        if image_bytes:
            image_part = types.Part.from_bytes(
                data=image_bytes,  # Os bytes crus que vieram do Discord
                mime_type="image/png" 
            )
            contents.append(image_part)



        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    system_instruction=SAGE_SYSTEM_INSTRUCTION

                )
            )

            return response.text

        except Exception as e:

            logger.error(f"O Sábio falhou: {e}", exc_info=True)
            return "O Sábio está meditando em silêncio... (Erro na API)"

