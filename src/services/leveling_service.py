import logging
from typing import Tuple

from src.database.models.user import UserModel
from repositories.item_repository import ItemRepository
from src.repositories.user_repository import UserRepository
from src.repositories.level_rewards_repository import LevelRewardsRepository

logger  = logging.getLogger(__name__)


class LevelingService:
    """Cálculo de níveis, progressão e sincronização de cargos."""
    def __init__(self,
                 user_repo: UserRepository,
                 rewards_repo: LevelRewardsRepository,
                 item_repo: ItemRepository
                 ):
        """Inicializa o serviço de nivelamento.

        Args:
            user_repo (UserRepository): Repositório de usuários.
            rewards_repo (LevelRewardsRepository): Repositório de recompensas por nível (cargos).
            item_repo (ItemRepository): Repositório de itens para bônus passivos.
        """
        self.user_repo = user_repo
        self.rewards_repo = rewards_repo
        self.item_repo = item_repo

    # Constante de da dificuldade
    BASE_XP_FACTOR = 150

    def calculate_level(self, total_xp: int) -> int:
        """Calcula o nível atual com base no XP.

        Args:
            total_xp (int): Quantidade de experiência que um usuário tem.

        Returns:
            int: O nível do usuário.
        """

        if total_xp < 0:
            return 0

        # Regra de nível
        level = int((total_xp / self.BASE_XP_FACTOR)**0.5)

        return level

    def xp_for_next_level(self, current_level: int) -> int:
        """Calcula o XP necessário para o próximo nível.

        Args:
            current_level (int): Nível atual do usuário.

        Returns:
            int: A quantidade de XP necessária para o próximo nível.
        """

        next_level = current_level + 1

        return self.BASE_XP_FACTOR * (next_level ** 2)

    def get_user_progress(self, total_xp: int) -> dict:
        """Calcula dados detalhados de progresso para exibição (barras, porcentagens).

        Realiza a matemática de "Piso" e "Teto" para determinar o progresso relativo
        dentro do nível atual.

        Args:
            total_xp (int): XP total acumulado do usuário.

        Returns:
            dict: Dicionário contendo:
                - current_level (int): Nível atual do usuário
                - relative_xp (int): XP conquistado neste nível (ex: 50)
                - needed_xp (int): Tamanho total deste nível (ex: 450)
                - percentage (int): Porcentagem concluída (0-100)
                - xp_floor (int): XP onde este nível começou
                - xp_ceiling (int): XP onde este nível termina
        """
        current_level = self.calculate_level(total_xp)

        # Teto de XP do nível atual
        xp_ceiling = self.xp_for_next_level(current_level)

        # Piso (Fórmula inversa baseada no nível atual)
        xp_floor = self.BASE_XP_FACTOR * (current_level ** 2)

        # Calculos de progresso
        xp_needed = xp_ceiling - xp_floor
        xp_progress = total_xp - xp_floor

        percentage = int((xp_progress / xp_needed) * 100)

        return {
            "current_level": current_level,
            "relative_xp": xp_progress,
            "needed_xp": xp_needed,
            "percentage": percentage,
            "xp_floor": xp_floor,
            "xp_ceiling": xp_ceiling
        }

    async def sync_roles(self, user_id:int, current_level:int, guild):
        """Sincroniza os cargos de nível do usuário conforme seu nível atual.

        Remove cargos de nível antigos e adiciona o cargo correspondente ao nível atual.

        Args:
            user_id (int): ID do usuário.
            current_level (int): Nível atual do usuário.
            guild: Servidor do Discord em que estamos.

        Returns:
            bool: True se um novo cargo de nível foi adicionado; False caso contrário.
        """

        # Cargo alvo
        target_reward = await self.rewards_repo.get_role_for_level(current_level)

        # Lista de cargos
        all_rewards_ids = await self.rewards_repo.get_all_reward_role_ids()

        # Pegamos o usuario pelo id
        member = guild.get_member(user_id)

        if not member:
            logger.info(f'Não foi possível localizar o usuário {user_id}.')
            return False

        roles_to_remove = []

        target_role_id = target_reward.role_id if target_reward else None
        has_target_role = False

        # verificamos cada role do membro, se ele tiver roles de nível diferente do dele colocamos na lista para remover.
        for role in member.roles:

            if role.id == target_role_id:
                has_target_role = True
                continue

            if role.id in all_rewards_ids:
                if role.id != target_role_id:
                    roles_to_remove.append(role)

        # Váriavel para verificar se mudamos algum cargo de nível
        new_role_added = False

        # Removemos as roles que não competem ao nível atual
        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove)
                logger.info(f'Foram removidos {len(roles_to_remove)} cargos antigos de {member.name}')
            except Exception as e:
                logger.error(f'Erro ao remover cargos antigos: {e}')

        # Se ele não tiver o cargo para o nível atual adicionamos ele
        if target_role_id and not has_target_role:
            role_obj = guild.get_role(target_role_id)
            if role_obj:
                try:
                    await member.add_roles(role_obj)
                    logger.info(f'Cargo {target_reward.role_name} adicionado para {member.display_name}')
                    new_role_added = True  # Confirmamos que houve adição de cargo novo
                except Exception as e:
                    logger.error(f"Erro ao adicionar: {e}")
            else:
                logger.warning(f"Cargo ID {target_role_id} não encontrado!")

        return new_role_added

    async def calculate_bonus(self, user: UserModel, base_xp: int, base_coins) -> Tuple[int, int, str]:
        """Calcula bônus de XP e moedas com base em itens equipados.

        Verifica os efeitos passivos do item equipado pelo usuário e aplica multiplicadores
        sobre os valores base de XP e moedas.

        Args:
            user (UserModel): Usuário que receberá os bônus.
            base_xp (int): XP base antes de bônus.
            base_coins (int): Moedas base antes de bônus.

        Returns:
            Tuple[int, int, str]: (xp_final, moedas_finais, texto_descritivo_do_bônus).
        """
        xp_multiplier = 1.0
        coins_multiplier = 1.0
        bonus_text = ""


        if user and user.equipped_item_id:
            item = await self.item_repo.get_by_id(user.equipped_item_id)
            # Verifica se o item existe e tem efeitos passivos
            if item and item.passive_effects:
                for effect in item.passive_effects:
                    if effect.type == "xp_boost":
                        xp_multiplier += effect.multiplier

                    elif effect.type == "coin_boost":
                        coins_multiplier += effect.multiplier

        # Calcula XP final
        final_xp = int(base_xp * xp_multiplier)
        final_coins = int(base_coins * coins_multiplier)

        if xp_multiplier > 1.0 or coins_multiplier > 1.0:
            xp_diff = final_xp - base_xp
            coins_diff = final_coins - base_coins

            bonus_text = str((f"Bônus de XP d o Item: +{xp_diff}\n"
                        f"Bônus de Moedas do Item: +{coins_diff}"))

        return final_xp, final_coins, bonus_text

    async def grant_reward(self, user_id: int, xp_amount:int, coins_amount: int, guild):
        """Aplica XP e moedas ao usuário e verifica nível/cargos.

        A operação é atômica no banco e, após atualizar o saldo, sincroniza os
        cargos de nível no servidor do Discord.

        Args:
            user_id (int): ID do usuário.
            xp_amount (int): Quantidade de XP a adicionar.
            coins_amount (int): Quantidade de moedas a adicionar.
            guild: Objeto Guild onde os cargos serão sincronizados.

        Returns:
            tuple[bool, int | None]: (level_up_ocorreu, nivel_atual) ou (False, None) em erro.
        """

        # Atuzalziamo os dados do usuário
        updated_user = await self.user_repo.add_xp_coins(user_id=user_id,
                                           xp=xp_amount,
                                           coins=coins_amount
                                           )
        # se ele não existir paramos aqui
        if not updated_user:
            logger.warning(f'Não foi possivel localizar o user {user_id}')
            return False, None

        # Verificamos o nível atual
        current_level = self.calculate_level(updated_user.xp)

        # Calculamos o nível antigo
        old_xp = max(0, updated_user.xp - xp_amount)
        old_level = self.calculate_level(old_xp)

        try:
            level_up_occurred = await self.sync_roles(user_id, current_level, guild)

            if level_up_occurred:
                logger.info(f'Level UP! {user_id}: {old_level} -> {current_level}')
                return True, current_level
            else:
                return False, current_level

        except Exception as e:
            logger.info(f'Erro ao sincronizar os cargos: {e}')
            return False, None




