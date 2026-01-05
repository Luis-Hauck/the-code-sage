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
    def __init__(self, mission_repo: MissionRepository, leveling_service: LevelingService, user_repo:UserRepository):
        self.mission_repo = mission_repo
        self.leveling_service = leveling_service
        self.user_repo = user_repo

    async def register_mission(self, mission_id: int, title: str, author_id:int) -> bool:
        """
        Cria a missão assim que a thread é criada no Discord
        :param mission_id: ID da thread(missão) no Discord;
        :param title: Título da thread;
        :param author_id: ID de quem criou a thread;
        :return: (True/False, Mensagem).
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

    async def evaluate_user(self,mission_id:int, author_id, user_id, rank:str, guild) -> Tuple[bool, Any]:
        """
        Lógica do comando /avaliar.
        Valida, Premia (Leveling) e Registra (Mission).
        :param mission_id: ID da thread(missão) no Discord;
        :param author_id:ID de quem criou a thread;
        :param user_id: ID do úsuario a ser avaliado;
        :param rank: Nota que o úsuario recebeu.
        :param guild: Guilda onde a thread foi criada.
        :return: (True/False, Mensagem)
        """

        # Buscamos o user
        user = await self.user_repo.get_by_id(user_id)

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
        rank_upper = EvaluationRank(rank.upper())
        base_rewards = RANK_REWARDS.get(rank_upper)

        if not base_rewards:
            return False, f'Selecione uma nota válida: {", ".join(RANK_REWARDS.keys())}'

        # Calculo dos bonus
        final_xp, final_coins, bonus_text = await self.leveling_service.calculate_bonus(
            user,
            base_rewards["xp"],
            base_rewards["coins"])


        # Entrega as recompensas
        await self.leveling_service.grant_reward(user_id,
                                                 final_xp,
                                                 final_coins,
                                                 guild)

        # Nível após a missão
        current_level = int(self.leveling_service.calculate_level(user.xp+final_xp))

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




    async def close_mission(self, mission_id: int):
        """
        Atualiza o status da missão no banco para CLOSED.
        :param mission_id: ID da missão a ser fechada.
        :return: True se foi fechada agora, False caso contrário
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
        """
        Envia um alerta para os moderadores sobre uma avaliação injusta.
        :param mission_id: ID da missão;
        :param reporter_id: ID de quem reportou a missão;
        :param reason: Motivo da reclamação;
        :return: (True, {dados_do_report}) ou (False, "Mensagem de erro")
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
            "current_rank": participant.rank,
            "reason": reason
        }

    async def adjust_evaluation(self, mission_id: int, target_user_id: int, new_rank_str: str, guild) -> Tuple[
        bool, Any]:
        """
        Altera a nota de um usuário, recalculando XP e Coins (Estorno + Novo Depósito).
        :param mission_id:
        :param target_user_id:
        :param new_rank_str:
        :param guild:
        :return:
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
        old_eval.evaluated_at = datetime.now()  # Opcional: atualizar data


        success = await self.mission_repo.update_evaluator(
                                                           mission_id=mission_id,
                                                           evaluator_model=old_eval)

        if success:
            logger.info(f"Rank ajustado de **{old_eval.rank.value}** para **{new_rank_enum.value}**.\nAjuste de Saldo: {xp_diff:+d} XP | {coins_diff:+d} Coins na missão {mission_id}.")
            return True, {
                "old_rank": old_eval.rank.value,
                "new_rank": new_rank_enum,
                "xp_diff": xp_diff,
                "coins_diff": coins_diff
            }
        else:
            logger.error(f"Erro de banco ao ajustar avaliação na missão {mission_id}")
            return False, "Erro ao ajustar a avalição."