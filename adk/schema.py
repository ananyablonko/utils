from typing import Literal, Any
from pydantic import BaseModel, Field, field_serializer, field_validator
from google.adk.agents import BaseAgent
from datetime import datetime;
from uuid import uuid4

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str = ""
    sender: Literal["user", "agent"] = "agent"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    done: bool = False

class LiveMessage(Message):
    inline_data: bytes = b""
    mime_type: str = "text/plain"
    interrupted: bool = False

    @field_serializer('inline_data')
    def serialize_inline_data(self, inline_data: bytes, _):
        return inline_data.decode()
    
    @field_validator('inline_data', mode='before')
    def deserialize_inline_data(cls, data: str | bytes):
        return data.encode() if isinstance(data, str) else data

    def model_post_init(self, context: Any) -> None:
        super().model_post_init(context)
        if self.is_audio and self.content:
            raise ValueError("Found text content in audio message!")
        if self.is_text and self.inline_data:
            raise ValueError("Found audio content in text message!")

    @property
    def is_text(self) -> bool:
        return self.mime_type.startswith("text")

    @property
    def is_audio(self) -> bool:
        return self.mime_type.startswith("audio")


def dump_agent(agent: BaseAgent) -> dict[str, Any]:
    """ Assume parent field name and sub_agents field name will remain unchanged """
    exc: dict[str, Any] = {'parent_agent': True}
    exc['sub_agents'] = {"__all__": exc}
    return agent.model_dump(exclude=exc)