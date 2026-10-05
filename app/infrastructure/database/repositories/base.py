from abc import ABC, abstractmethod
from typing import Generic, TypeVar

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