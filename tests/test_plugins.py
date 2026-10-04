from app.plugins.example import ExamplePlugin


def test_example_plugin() -> None:
    plugin = ExamplePlugin()

    assert plugin.info.id == "example"
    assert plugin.info.name == "Example Plugin"

    courses = plugin.get_courses()
    assignments = plugin.get_assignments()

    assert len(courses) == 2
    assert len(assignments) == 2

    assert courses[0].name == "Programación"
    assert assignments[0].title == "Práctica de Python"