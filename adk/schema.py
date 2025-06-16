from typing import Optional
from pydantic import BaseModel

class SingleValue[T](BaseModel):
    """
    Workaround for RootModel bugs (e.g. doesn't work with dict).
    Also has a nicer serialization.
    """
    value: T

    def __init__(self, value: Optional[T] = None, *args):
        if len(args) < 1:
            if value is None:
                raise ValueError(f"No arg given -> value cannot be None!, got {value=}")
        else:
            if len(args) > 1:
                raise ValueError(f"arg must be a single value, got {args}")
            if value is not None:
                raise ValueError(f"arg given - value must be None!, got {value=}")
            
            value = args[0]

        super().__init__(value=value)

    def model_dump(self, *args, **kwargs) -> T:
        return self.value