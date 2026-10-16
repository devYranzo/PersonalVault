from abc import ABC, abstractmethod
from collections.abc import Collection
from typing import Generic, TypeVar

from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")
DomainType = TypeVar("DomainType")


class BaseRepository[ModelType, DomainType](
    ABC,
):
    def __init__(self, session: Session) -> None:
        self.session = session

    @abstractmethod
    def to_domain(self, model: ModelType) -> DomainType:
        raise NotImplementedError

    @abstractmethod
    def to_model(self, domain: DomainType) -> ModelType:
        raise NotImplementedError

    def add(self, domain: DomainType) -> DomainType:
        model = self.to_model(domain)

        self.session.add(model)
        self.session.flush()

        return self.to_domain(model)

    def delete(self, model: ModelType) -> None:
        self.session.delete(model)

    def _delete_missing(
        self,
        model_class: type,
        source: str,
        keep_external_ids: Collection[str],
    ) -> int:
        """
        Elimina las filas de `source` cuyo `external_id` no está en
        `keep_external_ids` y devuelve cuántas eran.

        Nunca toca filas de otra fuente. Se borra por lotes para no
        superar el límite de parámetros de SQLite.
        """
        keep = set(keep_external_ids)

        stored = self.session.scalars(
            select(model_class.external_id).where(
                model_class.source == source,
            )
        ).all()

        stale = [
            external_id
            for external_id in stored
            if external_id not in keep
        ]

        removed = 0

        for start in range(0, len(stale), 500):
            batch = stale[start:start + 500]

            result = self.session.execute(
                sql_delete(model_class).where(
                    model_class.source == source,
                    model_class.external_id.in_(batch),
                )
            )

            removed += result.rowcount or 0

        return removed