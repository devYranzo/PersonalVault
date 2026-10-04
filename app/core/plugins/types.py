from enum import StrEnum

from pydantic import BaseModel


class PluginCapabilities(StrEnum):
    COURSES = "courses"
    ASSIGNMENTS = "assignments"
    EVENTS = "events"
    DOCUMENTS = "documents"


class PluginInfo(BaseModel):
    id: str
    name: str
    version: str
    description: str

    capabilities: list[PluginCapabilities] = []