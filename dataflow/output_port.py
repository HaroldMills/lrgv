from dataclasses import dataclass

from port import Port


@dataclass(frozen=True)
class OutputPort(Port):
    name: str = 'Output'
