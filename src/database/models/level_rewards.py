from pydantic import BaseModel

class LevelRewardsModel(BaseModel):
    """
    Representa um nível de recompensa, nesse nível ganha x cargo.

    Attributes:
        level_required: Nível requerido apra o cargo.
        role_id: ID do cargo.
        role_name: Nome do cargo.
    """

    level_required:int
    role_id:int
    role_name:str

    class Config:
        populate_by_name = True