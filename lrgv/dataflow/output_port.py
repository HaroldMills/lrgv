from dataclasses import dataclass

from lrgv.dataflow.port import Port


@dataclass(frozen=True)
class OutputPort(Port):

    name: str = 'Output'

    def __str__(self):
        return f'Processor "{self.processor.path}" output port "{self.name}"'
