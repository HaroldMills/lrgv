from dataclasses import dataclass

from port import Port


@dataclass(frozen=True)
class InputPort(Port):
    name: str = 'Input'
    connection_required: bool = True
