from dataclasses import dataclass

from lrgv.dataflow.processor import Processor


@dataclass(frozen=True)
class Port:
    processor: Processor
    name: str
