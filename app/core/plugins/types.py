from enum import StrEnum

from pydantic import BaseModel, Field


class PluginCapabilities(StrEnum):
    COURSES = "courses"
    ASSIGNMENTS = "assignments"
    EVENTS = "events"
    DOCUMENTS = "documents"


class PluginStatus(StrEnum):
    DISCOVERED = "discovered"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class PluginInfo(BaseModel):
    id: str
    name: str
    version: str
    description: str

    capabilities: list[PluginCapabilities] = Field(
        default_factory=list
    )