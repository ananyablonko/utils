from typing import Iterable, Iterator, Optional, override

from pydantic import Field
from pathlib import Path

from google.adk.artifacts import InMemoryArtifactService
from google.genai import types

from utils.common.ds import PersistentDict, PersistentList
from utils.common.ds.persistent import Pair

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
            self._len_delta()
        # The PersistentCollection constructor creates the path and the .meta
        ArtifactList(path, value)

    @override
    def _load(self, fp: Path) -> Pair[str, ArtifactList]:
        return Pair[str, ArtifactList](key=str(fp.relative_to(self.root)).replace('\\', '/'), value=ArtifactList(root=fp))
    
    @override
    def _save(self, fp: Path, data: Pair[str, ArtifactList]) -> None:
        return  # the ArtifactList already exists
    
    @override
    def items(self) -> Iterator[tuple[str, ArtifactList]]:
        yield from (self._load(f.parent).to_tuple() for f in self.root.rglob('*') if f != self._meta and f.name == self._meta.name)


class FileSystemArtifactService(InMemoryArtifactService):
    artifacts: ArtifactDict = Field(default_factory=lambda: ArtifactDict(root=Path('.')))
    def __init__(self, root: str):
        super().__init__(artifacts=ArtifactDict(root=Path(root)))  # type: ignore

    def get_artifact_path(self, app_name: str, user_id: str, session_id: str, filename: str) -> Optional[str]:
        path = self._artifact_path(app_name, user_id, session_id, filename)
        versions = self.artifacts.get(path)
        if not versions:
            return None
        return str((self.artifacts.root / path / str(len(versions) - 1)).resolve())
    