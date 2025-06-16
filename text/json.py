from typing import Iterable

def navigate(obj: dict | list, path: Iterable[str | int] | None) -> str | None:
    if path is None:
        return None
    
    current = obj
    err_msg = f"Invalid Path: {list(path)}"
    for key in path:
        match (current, key):
            case (list() as seq, int() as idx) if not isinstance(key, bool):
                if idx < 0 or idx >= len(seq):
                    raise IndexError(f"{err_msg}\nIndex out of range.\nlength={len(seq)}\nindex={idx}")
                current = seq[idx]
            case (dict() as mapping, str() as field):
                if field not in mapping:
                    raise KeyError(f"{err_msg}\nField {field} does not exist.\nfields={list(mapping.keys())}")
                current = mapping[field]
            case (list() as seq, str() as field):
                raise TypeError(f"{err_msg}\nCannot index list with a string.\nlist={seq}\nstring={field}")
            case (dict() as mapping, int() as idx) if not isinstance(key, bool):
                raise TypeError(f"{err_msg}\nCannot index object with an integer.\nobject={mapping}\ninteger={idx}")
            case _:
                raise ValueError(f"{err_msg}\nKeys may only be strings or integer indices!")
    return str(current)