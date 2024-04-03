from dataflow import InputPort, OutputPort


class SimpleProcessorMixin:


    """
    Mixin class for processor with a single input port named "Input"
    and a single output port named "Output".

    This class provides implementations of the `_create_input_ports`
    and `_create_output_ports` methods for such processors.
    """

 
    def _create_input_ports(self):
        return (InputPort(self),)
    

    def _create_output_ports(self):
        return (OutputPort(self),)
