from dataclasses import dataclass, field
from functools import cached_property
from typing import BinaryIO, Callable, Union


@dataclass(frozen=True)
class Object:
    """Bucket Object class with lazy-loading content"""

    key: str
    content_loader: Callable

    @cached_property
    def content(self) -> BinaryIO:
        return self.content_loader()
