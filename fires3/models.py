from dataclasses import dataclass, field
from functools import cached_property
from typing import BinaryIO, Callable, Union


@dataclass(frozen=True)
class Object:
    """Bucket Object class"""

    key: str
    content: BinaryIO
