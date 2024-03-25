from dataclasses import dataclass

from port import Port


@dataclass
class Connection:
    source: Port
    destination: Port
