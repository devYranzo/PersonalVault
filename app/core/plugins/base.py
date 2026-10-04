from abc import ABC, abstractmethod

from app.core.models import Assignment, Course, Document, Event
from app.core.plugins.types import PluginInfo


class Plugin(ABC):
    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """
        Devuelve la información del plugin.
        """
        raise NotImplementedError

    @abstractmethod
    def initialize(self) -> None:
        """
        Inicializa el plugin.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> None:
        """
        Libera los recursos utilizados por el plugin.
        """
        raise NotImplementedError

    def connect(self) -> None:
        """
        Conecta el plugin con su servicio externo.

        No todos los plugins necesitan conexión.
        """

    def disconnect(self) -> None:
        """
        Desconecta el plugin del servicio externo.
        """

    def is_connected(self) -> bool:
        """
        Indica si el plugin está conectado a su servicio externo.
        """
        return False

    def get_courses(self) -> list[Course]:
        """
        Devuelve los cursos disponibles.
        """
        return []

    def get_assignments(self) -> list[Assignment]:
        """
        Devuelve las tareas disponibles.
        """
        return []

    def get_events(self) -> list[Event]:
        """
        Devuelve los eventos disponibles.
        """
        return []

    def get_documents(self) -> list[Document]:
        """
        Devuelve los documentos disponibles.
        """
        return []