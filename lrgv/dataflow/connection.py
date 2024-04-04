from dataclasses import dataclass

from lrgv.dataflow.port import Port


@dataclass
class Connection:
    source: Port
    destination: Port
