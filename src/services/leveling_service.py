import logging

from src.repositories.user_repository import UserRepository
from src.repositories.level_rewards_repository import LevelRewardsRepository

logger  = logging.getLogger(__name__)


class LevelingService:
    def __init__(self,
                 user_repo: UserRepository,
                 rewards_repo: LevelRewardsRepository
                 ):
        self.user_repo = user_repo
        self.rewards_repo = rewards_repo

    # Constante de da dificuldade
    BASE_XP_FACTOR = 150

    def calculate_level(self, total_xp:int) -> int:
        """
        Calcula o nível atual com base no XP
        :param total_xp: Quantidade de experiência que um usuário tem.
        :return: O nível do usuário
        """

        if total_xp < 0:
            return 0

        # Regra de nível
        level = int((total_xp / self.BASE_XP_FACTOR)**0.5)

        return level

    def xp_for_next_level(self, current_level:int) -> int:
        """
        Calcula o xp necessário para o próximo nível.
        :param current_level: Níverl atual do usuário.
        :return: A quantidade de xp necessária apra o próximo nível.
        """

        next_level = current_level + 1

        return self.BASE_XP_FACTOR * (next_level ** 2)

    async def sync_roles(self, user_id, nivel_atual, guild):
        """
        Verica o cargo atual remove qualquer outro de nível antigo.
        :param guild: Servidor do discord em que estamos.
        :param user_id: ID do usuário.
        :param nivel_atual: Nível atual do usário
        :return:
        """

        # Cargo alvo
        target_reward = await self.rewards_repo.get_role_for_level(nivel_atual)

        # Lista de cargos
        all_rewards_ids = await self.rewards_repo.get_all_reward_role_ids()

        # Pegamos o usuario pelo id
        member = guild.get_member(user_id)

        if not member:
            logger.info(f'Não foi possível localizar o usuário {user_id}.')
            return

        roles_to_remove = []

        target_role_id = target_reward.role_id if target_reward else None

        # verificamos cada role do membro, se ele tiver roles de nível diferente do dele colocamos na lista para remover.
        for role in member.roles:
            if role.id in all_rewards_ids:
                if role.id != target_role_id:
                    roles_to_remove.append(role)


        # Removemos as roles que não competem ao nível atual
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)
            logger.info(f'Foram removidos {len(roles_to_remove)} cargos antigos de {member.name}')

        if target_reward:
            # verificamos se já não tem o cargo
            has_role = any(r.id == target_role_id for r in member.roles)

            if not has_role:
                role_obj = guild.get_role(target_role_id) # verifcamos se esse cargo existe no servidor
                if role_obj:
                    await  member.add_roles(role_obj)
                    logger.info(f'Cargo {target_reward.role_name} adcionado ao usuário {member.dysplay_name}')

                else:
                    logger.warning(f"Cargo ID {target_role_id} não encontrado no Discord!")


    async def grant_reward(self, user_id: int, xp_amount:int, coins_amount: int, guild):
        """
        Aplica XP e Moedas de forma atômica e verifica Level Up.
        :param user_id: ID do usuário
        :param xp_amount: Quantidade de xp obtida.
        :param coins_amount:
        :param guild:
        """

        # Atuzalziamo os dados do usuário
        updated_user = await self.user_repo.add_xp_coins(user_id=user_id,
                                           xp=xp_amount,
                                           coins=coins_amount
                                           )
        # se ele não existir paramos aqui
        if not updated_user:
            logger.warning(f'Não foi possivel localizar o user {user_id}')
            return

        # verificamos a qtd anterior de xp
        old_xp = max(0, updated_user.xp - xp_amount)

        # calculamos o nível aintigo e o atual
        old_level = self.calculate_level(old_xp)
        new_level = self.calculate_level(updated_user.xp)

        # Se o novo nível for maior que o antigo subimos ele e damos um novo cargo
        if new_level > old_level:
            logger.info(f'Level UP! {user_id}: {old_level} -> {new_level}')
            await self.sync_roles(user_id, new_level, guild)





