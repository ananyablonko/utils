from typing import Optional, Unpack
from pydantic import BaseModel, Field


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