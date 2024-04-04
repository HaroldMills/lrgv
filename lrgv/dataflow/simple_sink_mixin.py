from lrgv.dataflow import InputPort


class SimpleSinkMixin:


    """
    Mixin class for processor with a single input port named "Input"
    and no output ports.

    This class provides an implementation of the `_create_input_ports`
    method for such processors.
    """

 
    def _create_input_ports(self):
        return (InputPort(self),)
