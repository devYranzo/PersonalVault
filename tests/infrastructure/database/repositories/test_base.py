import pytest

from app.infrastructure.database.repositories.base import (
    BaseRepository,
)


def test_base_repository_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        BaseRepository()