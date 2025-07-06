from typing import Optional, Literal, Any
from pydantic import BaseModel, Field
from google.adk.agents import BaseAgent
from datetime import datetime;
from uuid import uuid4

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str = ""
    sender: Literal["user", "agent"] = "agent"
    timestamp: str = Field(default_factory=datetime.now().isoformat)
    done: bool = False

    
def dump_agent(agent: BaseAgent) -> dict[str, Any]:
    """ Assume parent field name and sub_agents field name will remain unchanged """
    exc: dict[str, Any] = {'parent_agent': True}
    exc['sub_agents'] = {"__all__": exc}
    return agent.model_dump(exclude=exc)