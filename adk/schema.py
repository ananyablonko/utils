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

class SingleValue[T](BaseModel):
    """
    Workaround for RootModel bugs (e.g. doesn't work with dict).
    Also has a nicer serialization.
    """
    value: T

    def __init__(self, value: Optional[T] = None, **kwargs):
        if kwargs == {} and value is None:
            raise ValueError(f"No value or kwarg given! Input cannot be None!")
        elif value is not None and kwargs:
            raise ValueError(f"Specifiy either one of value or a kwarg, not both! {value=}, {kwargs=}")
        elif len(kwargs) > 1:
            raise ValueError(f"Too many keyword arguments! {kwargs=}")
        elif value is None:
            _, value = kwargs.popitem()

        super().__init__(value=value)

    def model_dump(self, *args, **kwargs) -> T:
        return self.value
    
    def model_dump_json(self, *args, **kwargs) -> str:
        return str(self.value)
    
def dump_agent(agent: BaseAgent) -> dict[str, Any]:
    """ Assume parent field name and sub_agents field name will remain unchanged """
    exc: dict[str, Any] = {'parent_agent': True}
    exc['sub_agents'] = {"__all__": exc}
    return agent.model_dump(exclude=exc)