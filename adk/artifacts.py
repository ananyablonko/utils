from typing import Iterable, Optional, override

from pydantic import Field
from pathlib import Path

from google.adk.artifacts import InMemoryArtifactService
from google.genai import types

from ..ds import PersistentDict, PersistentList
from ..ds.persistent import Pair

class ArtifactList(PersistentList[types.Part]):
    def __init__(self, root: Path, items: Optional[Iterable] = None):
        super().__init__(root=root)
        if items is not None:
            self.extend(items)

class ArtifactDict(PersistentDict[str, ArtifactList]):
    @override
    def hash(self, key: str):
        return key
    
    @override
    def __setitem__(self, key: str, value: list) -> None:
        path = self._get_file_path(key)
        if not path.exists():
            self._inc_len()
        # The PersistentCollection constructor creates the path and the .meta
        ArtifactList(path, value)

    @override
    def _load(self, fp: Path) -> Pair[str, ArtifactList]:
        return Pair[str, ArtifactList](key=str(fp.relative_to(self.root)).replace('\\', '/'), value=ArtifactList(root=fp))
    
    @override
    def _save(self, fp: Path, data: Pair[str, ArtifactList]) -> None:
        return  # the ArtifactList already exists


class FileSystemArtifactService(InMemoryArtifactService):
    artifacts: ArtifactDict = Field(default_factory=lambda: ArtifactDict(root=Path('./.data/')))