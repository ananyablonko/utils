import sys, pathlib
d = pathlib.Path(__file__).resolve().parent
sys.path.append(str(d))
sys.path = list(set(sys.path))

from .text import prettify, shorten, clean_hebrew
from .tree import BaseTree, BaseNode, MaxDepthExceededError
from .logic import most

__all__ = ["prettify", "shorten", "clean_hebrew", "BaseTree", "BaseNode", "most", "MaxDepthExceededError"]
