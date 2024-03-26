from dataclasses import dataclass

from dataflow.port import Port


@dataclass
class Connection:
    source: Port
    destination: Port
