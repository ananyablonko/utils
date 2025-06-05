from typing import Optional, Generator, Any, Self, override
from pydantic import BaseModel, PrivateAttr, computed_field, Field

class MaxDepthExceededError(Exception):
    pass

class BaseNode(BaseModel):
    name: str = Field(frozen=True)
    children: list[Self] = Field(default_factory=list)
    parent: Optional[Self] = Field(default=None, repr=False, exclude=True)

    def __str__(self):
        return f"{self.__class__.__name__}({self.__repr_str__(', ')})"
    
    def __eq__(self, other: Self):
        return self.name == other.name

    @property
    def index(self) -> Optional[int]:
        if self.parent:
            return self.parent.children.index(self)

    @index.setter
    def index(self, new_index: int) -> None:
        if self.index is None or self.parent is None:
            raise ValueError("Cannot set index to a node with no parent!")
        self.parent.children.pop(self.index)
        self.parent.children.insert(new_index, self)

    @property
    def depth(self) -> int:
        return len(self.uid)

    @computed_field
    @property
    def uid(self) -> list[int]:
        current = self
        uid = []
        while current.parent is not None:
            uid.append(current.index or 0)
            current = current.parent
        return uid[::-1]
    


class BaseTree[Tn: BaseNode](BaseModel):
    __max_depth: Optional[int] = PrivateAttr(None)
    __nodes: dict[str, Tn] = PrivateAttr(default_factory=dict)
    __name: str = PrivateAttr()

    """Override these in subclasses"""
    _node_type: type[Tn] = PrivateAttr()

    def __init__(self, name: str, *, max_depth: Optional[int] = None, root: Optional[Tn | dict[str, Any]] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.__name = name
        self.__max_depth = max_depth
        if root is None:
            self.__nodes[name] = self._node_type(name=name)
            return
        
        if isinstance(root, dict):
            root = self._node_type(**root)
        
        def setup_node(node: Tn, parent: Optional[Tn] = None):
            self.__nodes[node.name] = node
            node.parent = parent
            for child in node.children:
                setup_node(child, node)
        
        setup_node(root)
    
    def insert(self, parent_name: str, node_name: str, index: Optional[int] = None, **kwargs) -> None:
        if parent_name is not None and parent_name not in self:
            raise KeyError(f"Parent node '{parent_name}' does not exist")

        node = self._node_type(name=node_name, parent=self.get(parent_name), **kwargs)
        self._insert(node, index)
    """End Override"""

    def __getitem__(self, node_name: str) -> Tn:
        return self.__nodes[node_name]

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(root='{self.name}', nodes={self.root})"

    def __iter__(self) -> Generator[Tn, None, None]:
        def _traverse(node: Tn) -> Generator[Tn, None, None]:
            yield node
            for child in node.children:
                yield from _traverse(child)

        yield from _traverse(self.root)

    def __setitem__(self, node_name: str, node: dict | Tn) -> None:
        """ This method is dangerous to use. TODO(Anan): make it easy to inherit without introspection shenanigans"""
        insert_argname = list(self.insert.__annotations__.keys())[1]
        node_argname = insert_argname.split('_')[0]

        if isinstance(node, dict):
            if node_name != node[insert_argname]:
                raise ValueError(f"{insert_argname} must be consistent with {node_argname}['{insert_argname}']")

            self.insert(**node)
            return

        if node_name != node.name:
            raise ValueError(f"{insert_argname} must be consistent with {node_argname}.name")

        self._insert(node, index=None)

    def __contains__(self, node_name: str) -> bool:
        return node_name in self.__nodes

    @computed_field
    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, new_name: str) -> None:
        self.rename_node(self.__name, new_name)
        self.__name = new_name

    @computed_field
    @property
    def root(self) -> Tn:
        return self[self.name]

    @computed_field
    @property
    def max_depth(self) -> Optional[int]:
        return self.__max_depth

    @max_depth.setter
    def max_depth(self, new_max: Optional[int]) -> None:
        if (
            new_max is not None
            and (self.__max_depth is None or new_max < self.__max_depth)
            and any(node.depth > new_max for node in self)
        ):
            raise MaxDepthExceededError("Cannot set max_depth lower than current depth. Delete deeper nodes first.")

        self.__max_depth = new_max

    def pop(self, node_name: str) -> Tn:
        if node_name not in self:
            raise KeyError(f"Node '{node_name}' does not exist")

        node = self[node_name]
        if node.parent is None or node.index is None:
            raise ValueError(f"Cannot pop root node {node_name}!")

        node.parent.children.pop(node.index)
        for child in node.children.copy():
            self.pop(child.name)
        return self.__nodes.pop(node_name)

    def get(self, node_name: Optional[str], default: Any = None) -> Tn | Any:
        return self[node_name] if node_name is not None and node_name in self else default

    def rename_node(self, node_name: str, new_name: str) -> None:
        node = self[node_name]
        if new_name == node_name:
            return

        if new_name in self:
            raise ValueError(f"Node with name '{new_name}' already exists")

        # Update the dictionary key and the node name
        self.__nodes[new_name] = self.__nodes.pop(node_name)
        node.__dict__['name'] = new_name

    def _insert(self, node: Tn, index: Optional[int]) -> None:
        if node.name in self:
            raise ValueError(f"Node with name '{node.name}' already exists")

        if self.max_depth is not None and node.parent and node.parent.depth >= self.max_depth:
            raise MaxDepthExceededError(f"Cannot insert node: maximum depth of {self.max_depth} exceeded")

        self.__nodes[node.name] = node
        if node.parent:
            if index is None:
                node.parent.children.append(node)
            else:
                node.parent.children.insert(index, node)

class Tree(BaseTree[BaseNode]):
    _node_type: type[BaseNode] = BaseNode

    @override
    def __init__(self, name: str, *, max_depth: Optional[int] = None, **kwargs) -> None:
        super().__init__(name=name, max_depth=max_depth, **kwargs)

    @override
    def insert(self, parent_name: str, node_name: str, *, index: Optional[int] = None) -> None:
        return super().insert(parent_name, node_name, index=index)

