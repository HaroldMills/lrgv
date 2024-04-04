from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeVar


T = TypeVar('T')


@dataclass(frozen=True)
class Data:
    items: Sequence[T]
    finished: bool = False
