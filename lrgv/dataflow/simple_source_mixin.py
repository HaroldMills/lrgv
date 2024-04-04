from lrgv.dataflow import OutputPort


class SimpleSourceMixin:


    """
    Mixin class for processor with no input ports and a single output
    port named "Output".

    This class provides an implementation of the `_create_output_ports`
    method for such processors.
    """

 
    def _create_output_ports(self):
        return (OutputPort(self),)
