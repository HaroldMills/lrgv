from dataclasses import dataclass

# It's important to import from `processor` here rather than from
# `dataflow` to avoid a circular import.
from processor import Processor


@dataclass(frozen=True)
class Port:
    processor: Processor
    name: str
