from dataclasses import dataclass

from dataflow.port import Port


@dataclass(frozen=True)
class InputPort(Port):

    name: str = 'Input'
    connection_required: bool = True

    def __str__(self):
        return f'Processor "{self.processor.name}" input port "{self.name}"'
