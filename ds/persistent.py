from pydantic import BaseModel
from pathlib import Path
from typing import Any, Optional, Iterator, Iterable
import shutil
import typing
import pickle

_undefined = object()

class PersistentCollection(BaseModel):
    class Metadata(BaseModel):
        length: int
        root: str
    
    root: Path

    def model_post_init(self, context) -> None:
        """Initialize root folder and metadata"""
        super().model_post_init(context)
        self._meta = self.root / '.meta'
        self.__filesystem_setup()

    def __len__(self) -> int:
        return self.Metadata.model_validate_json(self._meta.read_text()).length

    def clear(self) -> None:
        shutil.rmtree(self.root)
        self.__filesystem_setup()

    def delete(self) -> None:
        shutil.rmtree(self.root)

    def _len_delta(self, delta: int = 1) -> None:
        meta = self._read_meta()
        meta.length = meta.length + delta
        self._meta.write_text(meta.model_dump_json())

    def _read_meta(self) -> Metadata:
        return self.Metadata.model_validate_json(self._meta.read_text())
    
    def _write_meta(self, metadata: Metadata) -> None:
        self._meta.write_text(metadata.model_dump_json())

    def __filesystem_setup(self) -> None:
        if self.root.exists():
            return
        self.root.mkdir(parents=True)
        self._write_meta(self.Metadata(length=0, root=str(self.root)))
        


class Pair[Tk, Tv](BaseModel):
    key: Tk
    value: Tv

    def to_tuple(self) -> tuple[Tk, Tv]:
            return (self.key, self.value)

class PersistentDict[Tk, Tv](PersistentCollection):
    def hash(self, key: Tk) -> str:
        raise NotImplementedError()
    
    def __contains__(self, key: Tk) -> bool:
        return self._get_file_path(key).exists()
    
    def __setitem__(self, key: Tk, value: Tv) -> None:
        file_path = self._get_file_path(key)
        if not file_path.exists():
            self._len_delta()
            file_path.parent.mkdir(parents=True, exist_ok=True)

        self._save(file_path, Pair[Tk, Tv](key=key, value=value))
    
    def __getitem__(self, key: Tk) -> Tv:
        file_path = self._get_file_path(key)
        if not file_path.exists():
            raise KeyError(key)
        pair = self._load(file_path)
        assert pair.key == key
        return pair.value
    
    def __iter__(self) -> Iterator[Tk]:
        yield from self.keys()
    
    def get(self, key: Tk, defaultvalue: Optional[Tv] = None) -> Optional[Tv]:
        return self[key] if key in self else defaultvalue
    
    def pop(self, key: Tk, defaultvalue: Optional[Tv] = _undefined) -> Optional[Tv]:
        if key not in self:
            if defaultvalue is not _undefined:
                return defaultvalue
            raise KeyError(key)
        
        file_path = self._get_file_path(key)
        value = self._load(file_path).value
        file_path.unlink()

        self._len_delta(-1)

        return value
    
    def update(self, other: Optional[Any] = None, **kwargs) -> None:
        """Update the dict with key-value pairs from another dict or iterable of pairs"""
        if other is None:
            for key, value in kwargs.items():
                self[typing.cast(Tk, key)] = value
            return
        
        if hasattr(other, 'keys'):
            for key in other.keys():
                self[key] = other[key]
        else:
            for key, value in other:
                self[key] = value
        
    def keys(self) -> Iterator[Tk]:
        yield from (p[0] for p in self.items())

    def values(self) -> Iterator[Tv]:
        yield from (p[1] for p in self.items())

    def items(self) -> Iterator[tuple[Tk, Tv]]:
        yield from (self._load(f).to_tuple() for f in self.root.rglob('*') if f.is_file() and f != self._meta)

    def _load(self, fp: Path) -> Pair[Tk, Tv]:
        return Pair[Tk, Tv].model_validate(pickle.loads(fp.read_bytes()))
    
    def _save(self, fp: Path, data: Pair[Tk, Tv]) -> None:
        fp.write_bytes(pickle.dumps(data.model_dump()))
    
    def _get_file_path(self, key: Tk) -> Path:
        return self.root / self.hash(key)

    
class PersistentList[T](PersistentCollection):
    def __setitem__(self, idx: int, item: T) -> None:
        idx = self._validate_index(idx)
        self._get_file_path(idx).write_bytes(pickle.dumps(item))
    
    def __getitem__(self, idx: int) -> T:
        idx = self._validate_index(idx)
        return pickle.loads(self._get_file_path(idx).read_bytes())
    
    def __iter__(self):
        yield from (self[i] for i in range(len(self)))
    
    def append(self, item: T) -> None:
        self._get_file_path(len(self)).write_bytes(pickle.dumps(item))
        self._len_delta()
    
    def insert(self, idx: int, item: T) -> None:
        current_len = len(self)
        idx = max(0, current_len + idx) if idx < 0 else min(idx, current_len)
        self._shift_files(idx, 1)
        self._get_file_path(idx).write_bytes(pickle.dumps(item))
        self._len_delta()
    
    def pop(self, idx: int = -1) -> T:
        current_len = len(self)
        if current_len == 0:
            raise IndexError("pop from empty list")
        
        if idx < 0:
            idx = current_len + idx
        if idx < 0 or idx >= current_len:
            raise IndexError("pop index out of range")
        
        item = self[idx]
        
        file_path = self._get_file_path(idx)
        file_path.unlink()
        
        self._shift_files(idx + 1, -1)
        self._len_delta(-1)
        return item
    
    def remove(self, item: T) -> None:
        for i in range(len(self)):
            if self[i] == item:
                self.pop(i)
                return
        raise ValueError(f"{item} not in list")
    
    def extend(self, items: Iterable[T]) -> None:
        for item in items:
            self.append(item)

    def _get_file_path(self, idx: int) -> Path:
        return self.root / str(idx)
    
    def _shift_files(self, start_idx: int, shift: int) -> None:
        start_to_end = range(start_idx, len(self))
        for i in (start_to_end if shift < 0 else reversed(start_to_end)):
            old_path = self._get_file_path(i)
            if old_path.exists():
                new_path = self._get_file_path(i + shift)
                old_path.rename(new_path)

    def _validate_index(self, idx: int) -> int:
        if idx < 0:
            idx = len(self) + idx
        if idx < 0 or idx >= len(self):
            raise IndexError("list index out of range")
        return idx
