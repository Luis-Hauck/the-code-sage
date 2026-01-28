import logging
from typing import Dict, Tuple, Optional, Any
from datetime import datetime
import asyncio

from repositories.user_repository import UserRepository
from src.repositories.missions_repository import MissionRepository
from src.database.models.mission import MissionStatus, MissionModel, EvaluatorModel, EvaluationRank
from src.services.leveling_service import LevelingService

logger = logging.getLogger(__name__)

# Configuração de recompensas (Pode ir para um config.py depois)
RANK_REWARDS = {
    "S": {"xp": 50, "coins": 125},
    "A": {"xp": 40, "coins": 100},
    "B": {"xp": 30, "coins": 75},
    "C": {"xp": 20, "coins": 50},
    "D": {"xp": 10, "coins": 25},
    "E": {"xp": 0, "coins": 0},
}


class MissionService:
    """Regras de negócio relacionadas às missões."""
    def __init__(self, mission_repo: MissionRepository, leveling_service: LevelingService, user_repo:UserRepository):
        """Inicializa o serviço de missões.

        Args:
            mission_repo (MissionRepository): Repositório de missões.
            leveling_service (LevelingService): Serviço responsável por nível/cargos e bônus.
            user_repo (UserRepository): Repositório de usuários.
        """
        self.mission_repo = mission_repo
        self.leveling_service = leveling_service
        self.user_repo = user_repo

    async def register_mission(self, mission_id: int, title: str, author_id: int) -> bool:
        """Cria a missão assim que a thread é criada no Discord.

        Args:
            mission_id (int): ID da thread (missão) no Discord.
            title (str): Título da thread.
            author_id (int): ID de quem criou a thread.

        Returns:
            bool: True em caso de sucesso, False caso contrário.
        """

        mission = MissionModel(
            _id=mission_id,
            title=title,
            creator_id=author_id,
            created_at=datetime.now(),
            status=MissionStatus.OPEN,
            evaluators=[]
        )

        return await self.mission_repo.create(mission)

    async def evaluate_user(self, mission_id: int, author_id: int, user_id: int, rank: str, guild) -> Tuple[bool, Any]:
        """Lógica do comando /avaliar: valida, premia (Leveling) e registra (Mission).

        Args:
            mission_id (int): ID da thread (missão) no Discord.
            author_id (int): ID de quem criou a thread.
            user_id (int): ID do usuário a ser avaliado.
            rank (str): Nota que o usuário recebeu (S, A, B, C, D, E).
            guild: Guilda onde a thread foi criada.

        Returns:
            Tuple[bool, Any]: (True, dados_da_avaliação) em caso de sucesso ou (False, mensagem_de_erro) em caso de falha.
        """

        # Buscamos o user
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            return False, 'Usuário não encontrado para ser avaliado!'

        # Buscamos a missão
        mission = await self.mission_repo.get_by_id(mission_id)
        if not mission:
            return False, 'Essa missão ainda não foi criada'

        # Somente o autor pode avaliar
        if mission.creator_id != author_id:
            return False, 'Somente o criador da missão pode avaliar'

        # Verifica se quem está sendo avaliado é diferente do autor
        if author_id == user_id:
            return False, 'Você não pode avaliar a si mesmo'

        # Verificamos se úsuario já foi avaliado
        already_evaluated = any(evaluator.user_id == user_id for evaluator in mission.evaluators)
        if already_evaluated:
            return False, 'Este usuário já foi avaliado'

        # Calculamos as recompensas:
        rank_upper = EvaluationRank.get_or_none(rank)

        if not rank_upper:
            return False, f'Selecione uma nota válida: {", ".join(RANK_REWARDS.keys())}'

        base_rewards = RANK_REWARDS.get(rank_upper.value)

        if not base_rewards:
            return False, f'Selecione uma nota válida: {", ".join(RANK_REWARDS.keys())}'

        # Calculo dos bonus
        final_xp, final_coins, bonus_text = await self.leveling_service.calculate_bonus(
            user,
            base_rewards["xp"],
            base_rewards["coins"])


        # Entrega as recompensas
        result, current_level = await self.leveling_service.grant_reward(user_id,
                                                 final_xp,
                                                 final_coins,
                                                 guild)
        if current_level is None:
            return False, 'Erro ao entregar recompensas.'

        # Cria a nova pessoa avaliada
        new_evaluator = EvaluatorModel(
            user_id=user_id,
            username=user.username,
            user_level_at_time=current_level,
            rank=rank_upper,
            xp_earned=final_xp,
            coins_earned=final_coins,
            evaluate_at=datetime.now()
        )

        await self.mission_repo.add_participant(mission_id, new_evaluator)


        return True, {
            "rank": rank_upper,
            "xp": final_xp,
            "coins": final_coins,
            "bonus": bonus_text
        }




    async def close_mission(self, mission_id: int) -> bool:
        """Atualiza o status da missão no banco para CLOSED.

        Args:
            mission_id (int): ID da missão a ser fechada.

        Returns:
            bool: True se foi fechada agora, False caso contrário.
        """

        try:
            # Verifica se já não está fechada (para evitar concorrência)
            current = await self.mission_repo.get_by_id(mission_id)
            if current and current.status == MissionStatus.CLOSED:
                return False

            await self.mission_repo.update_status(
                mission_id=mission_id,
                new_status=MissionStatus.CLOSED,
                completed_at=datetime.now()
            )

            logger.info(f"Missão {mission_id} marcada como finalizada no banco.")
            return True

        except Exception as e:
            logger.error(f"Erro ao finalizar missão {mission_id}: {e}")
            return False



    async def report_evaluation(self, mission_id: int, reporter_id: int, reason: str) -> Tuple[bool, Optional[Dict[str, Any]]] | Tuple[bool, str]:
        """Reporta aos moderadores uma avaliação potencialmente injusta.

        Args:
            mission_id (int): ID da missão.
            reporter_id (int): ID de quem está reportando.
            reason (str): Motivo da reclamação.

        Returns:
            Tuple[bool, Optional[Dict[str, Any]]] | Tuple[bool, str]:
                (True, dados_do_report) em caso de sucesso, ou (False, mensagem_de_erro) em caso de falha.
        """
        mission = await self.mission_repo.get_by_id(mission_id)
        if not mission:
            return False, "Missão não encontrada."

        # Verifica se o reclamante realmente participou
        participant = next((e for e in mission.evaluators if e.user_id == reporter_id), None)
        if not participant:
            return False, 'Você não foi avaliado nesta missão, então não pode reportar.'

        logger.info(f'Ocorreu uma denúncia na missão: {mission.mission_id} o usuário {participant.user_id} reclamou com o motivo: {reason}')
        return True, {
            "mission_title": mission.title,
            "mission_id": mission.mission_id,
            "reporter_id": reporter_id,
            "reporter_name": participant.username,
            "current_rank": participant.rank.value,
            "reason": reason
        }

    async def adjust_evaluation(self, mission_id: int, target_user_id: int, new_rank_str: str, guild) -> Tuple[
        bool, Any]:
        """Ajusta a avaliação de um usuário, recalculando XP e moedas.

        O processo realiza estorno da avaliação anterior e aplica os novos
        valores com base no novo rank informado, incluindo bônus de itens.

        Args:
            mission_id (int): ID da missão.
            target_user_id (int): ID do usuário cuja avaliação será ajustada.
            new_rank_str (str): Novo rank a ser aplicado (S, A, B, C, D, E).
            guild: Guild do Discord onde os cargos podem ser sincronizados, se necessário.

        Returns:
            Tuple[bool, Any]: (True, dados_do_ajuste) em caso de sucesso; (False, mensagem_de_erro) caso contrário.
        """
        # Busca a missão
        mission = await self.mission_repo.get_by_id(mission_id)
        if not mission: return False, "Missão não encontrada."

        # Busca o registro da avaliação antiga
        # Usamos enumerate para saber o índice e atualizar no banco depois se precisar
        old_eval = next((e for e in mission.evaluators if e.user_id == target_user_id), None)

        if not old_eval:
            return False, "Este usuário não possui uma avaliação nesta missão para ser ajustada."

        # Valida Nova Nota
        try:
            new_rank_enum = EvaluationRank(new_rank_str.upper())
        except ValueError:
            return False, "Nota inválida."

        if old_eval.rank == new_rank_enum:
            return False, "A nova nota é igual à atual."

        previous_rank = old_eval.rank

        # Valores Antigos
        xp_to_remove = old_eval.xp_earned
        coins_to_remove = old_eval.coins_earned

        # Valores Novos (Base)
        new_base = RANK_REWARDS.get(new_rank_enum.value)

        # Recalcula Bônus, ponto que o usário pode mudar os itens equipados, próxima versão adcionar os itens que o usuário tinha.
        user = await self.user_repo.get_by_id(target_user_id)
        final_new_xp, final_new_coins, _ = await self.leveling_service.calculate_bonus(user, new_base['xp'], new_base['coins'])

        # Aplica a diferença entre os valores antigos e novos.
        # Ex: Ganhou 50 (C), devia ganhar 500 (S). Delta = 450.
        # Ex: Ganhou 500 (S), devia ganhar 50 (C). Delta = -450.

        xp_diff= final_new_xp - xp_to_remove
        coins_diff = final_new_coins - coins_to_remove

        await self.leveling_service.grant_reward(
            user_id=target_user_id,
            xp_amount=xp_diff,
            coins_amount=coins_diff,
            guild=guild
        )

        # ATUALIZA O BANCO (Substitui o EvaluatorModel antigo pelo novo)
        old_eval.rank = new_rank_enum
        old_eval.xp_earned = final_new_xp
        old_eval.coins_earned = final_new_coins
        old_eval.evaluate_at = datetime.now()


        success = await self.mission_repo.update_evaluator(
                                                           mission_id=mission_id,
                                                           evaluator_model=old_eval)

        if success:
            logger.info(f"Rank ajustado de **{previous_rank.value}** para **{new_rank_enum.value}**.\nAjuste de Saldo: {xp_diff:+d} XP | {coins_diff:+d} Coins na missão {mission_id}.")
            return True, {
                "old_rank": previous_rank,
                "new_rank": new_rank_enum,
                "xp_diff": xp_diff,
                "coins_diff": coins_diff
            }
        else:
            logger.error(f"Erro de banco ao ajustar avaliação na missão {mission_id}")
            return False, "Erro ao ajustar a avalição."