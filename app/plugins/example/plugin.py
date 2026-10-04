from app.core.models import Assignment, Course
from app.core.plugins import Plugin, PluginCapabilities, PluginInfo


class ExamplePlugin(Plugin):
    """
    Plugin de prueba.

    Simula un proveedor externo sin realizar ninguna
    conexión a Internet.
    """

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            id="example",
            name="Example Plugin",
            version="0.1.0",
            description="Plugin utilizado para probar la arquitectura.",
            capabilities=[
                PluginCapabilities.COURSES,
                PluginCapabilities.ASSIGNMENTS,
            ],
        )

    def initialize(self) -> None:
        print(f"[{self.info.id}] Plugin inicializado")

    def shutdown(self) -> None:
        print(f"[{self.info.id}] Plugin detenido")

    def connect(self) -> None:
        print(f"[{self.info.id}] Conectado")

    def disconnect(self) -> None:
        print(f"[{self.info.id}] Desconectado")

    def get_courses(self) -> list[Course]:
        return [
            Course(
                id="course-1",
                name="Programación",
                description="Curso de programación",
                source=self.info.id,
                external_id="example-course-1",
            ),
            Course(
                id="course-2",
                name="Matemáticas",
                description="Curso de matemáticas",
                source=self.info.id,
                external_id="example-course-2",
            ),
        ]

    def get_assignments(self) -> list[Assignment]:
        return [
            Assignment(
                id="assignment-1",
                title="Práctica de Python",
                description="Crear una aplicación utilizando Python.",
                course_id="course-1",
                course_name="Programación",
                source=self.info.id,
                external_id="example-assignment-1",
            ),
            Assignment(
                id="assignment-2",
                title="Ejercicios del tema 3",
                description="Resolver los ejercicios del tema 3.",
                course_id="course-2",
                course_name="Matemáticas",
                source=self.info.id,
                external_id="example-assignment-2",
            ),
        ]