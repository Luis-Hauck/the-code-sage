import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.database.models.user import UserModel
from src.utils.repositories.user_repository import UserRepository, UserStatus

# Marca todos os testes neste arquivo para serem executados com asyncio
pytestmark = pytest.mark.asyncio

    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.users = mock_collection

        _id=5,
        username='teste',
        joined_at=datetime.today(),
        xp=0,
        role_ids=[],
        inventory=[]


    user_repo = UserRepository(db=mock_db)


    assert result is True





