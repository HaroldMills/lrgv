from dataflow.dataflow_error import DataflowError
from vesper.util.bunch import Bunch


# TODO: Consider supporting a variable number of inputs or outputs.
# For example, multiplexer and demultiplexer signal processors might
# multiplex and demultiplex arbitrary numbers of signal channels.

# TODO: Consider how to deal with unconnected outputs. Some processors
# might have outputs that are sometimes unconnected, and that could
# run more efficiently if they did not need to compute the output.
# A processor might be told via an argument to its `connect` method
# which of its outputs will be unconnected so that it can plan its
# computations accordingly.

# TODO: Consider how to optimize forests of processor graphs to
# eliminate redundant computations, for example if two waveform
# measurements compute the same spectrogram. This would require
# defining an equivalence relation on processors that takes into
# account their classes, their settings, and their inputs.

# TODO: Consider storing input and output settings in port objects.
# This would require unfreezing port objects.

# TODO: Consider keeping track of whether input and output are
# finished in port objects. This would require unfreezing pott objects.

# TODO: Consider allowing `_process` method to read input items
# from input port objects, and write output items to output port
# objects.

# TODO: Add `Processor.STATE_INTERRUPTED` and implement `interrupt`
# method.

# TODO: Complete docstrings.

# TODO: Write more unit tests.


'''
A processor *finishes* when it finishes all of its processing and
transitions to the "finished" state. A processor typically finishes
when (1) all of its inputs are finished, (2) it has finished all of
the processing that it will perform, and (3) it has output all of its
output data and indicated that all of its outputs are finished. Once
a processor enters the "finished" state, its life is complete.
'''


'''
Processor use cases:

* Signal processing. In this case input and output items are sample
  buffers, with an associated channel count and sample rate and
  perhaps sample array shape. Good examples of this are the
  Vesper Recorder and Hear Birds Again.

* Detection. In this case input and output items can vary quite a
  lot. They can be logit vectors, for example, or
  (species_name, start_index, end_index) tuples. Good examples of
  this are the Old Bird NFC detectors and Nighthawk.

* Measurement. A measurement takes a single input item and produces
  a single output item, a measurement value computed from the input
  item. Measurements can be graphs, and several members of a set of
  measurement graphs can contain common processors, e.g. processors
  that compute a spectrogram. It would be good to be able to take
  an arbitrary set of measurements and construct a processor graph
  that can compute all of the measurement values efficiently, e.g.
  computing an input spectrogram only once although its value is
  used by multiple measurements. Consider how to deal with something
  like multiple solar event time measurements here.

* File processing. In this case input and output items are file paths.
  A good example of this is the LRGV archiver.
'''

'''
Dataflow package design requirements:

* Must support processing of various types of sequences, including sequences
  of audio data buffers, detections, and clip file names.

* *Processors* have *input ports* and *output ports through which input
  and output data flow.

* The inputs and outputs of multiple processors are connected in
  *processor graphs*.

* All processor types are discoverable plugins.

* Pocessors propagate certain information from input ports to output ports,
  such as audio channel count and sample rate.

* A processor input can be *optional*. If it is not optional it is
  *required*.

* A processor output can be *unconnected*, in which case it does not
  have to be computed.

* Supports both real-time and non-real-time audio processing.

* Supports pausing and resuming real-time audio playback.
'''

'''
Design:

* A *processor* has *processor settings* that are specified at
  initialization. Processors are instances of the `Processor` class
  and its subclasses.

* A processor has zero or more *input ports* through which *input data*
  flow. The input data are a sequence of items of the same type. An input
  data sequence has zero or more *input settings* (e.g. audio channel
  count and sample rate) that describe it. A processor input port is
  said to be *unconnected* if the settings of its input data are unknown,
  and *connected* if they are known. A processor is *connected* if and
  only if all of its inputs are connected.
  
  A processor may not require that all of its input ports be connected in
  order to function. If input for a port is not required, it is said to
  be *optional*.

* A processor has zero or more *output ports* through which *output data*
  flow out of it. The output data are a sequence of items of the same type.
  An output data sequence has zero or more *output settings* (e.g. audio
  channel count and sample rate) that describe it. The settings of a
  processor output are determined automatically by the processor from
  the settings of the processor and its inputs, and are known if and
  only if the processor is connected.

* A processor passes through a sequence of *states* over the course of
  its life. In most cases, the transition from one state to the next is
  initiated by a call to a processor method.
  
* After initialization, a processor is in the *unconnected* state. In
  this state the processor's processor settings are known but its
  input and output settings are not.

* The `Processor.connect` method specifies input settings for the input
  ports of a processor, and also which output ports will be unconnected.
  A processor is not obliged to compute output data for an unconnected
  output port. The `Processor.connect` method transitions a processor
  from the `unconnected` state to the `connected` state. In the
  `connected` state a processor's processor settings and its input
  and output settings are known.

* The `Processor.start` method transitions a processor from the
  `connected` state to the `running` state. In the `running` state,
  the processor is connected and any required internal I/O (e.g.
  for real-time audio input or output) is running.

* The `Processor.process` method accepts input data and returns
  output data. If the method finishes all of the processing that
  the processor will perform, it transitions the processor from the
  `running` state to the `finished` state.

* The `Processor.stop` method stops any internal I/O and transitions
  the processor to the `finished` state.

* Once a processor is in the `finished` state, its life is finished.

* A *processor graph* is a particular type of processor that manages
  a graph of processors. It is implemented in the `ProcessorGraph`
  subclass of the `Processor` class. Calls to `ProcessorGraph` methods
  (e.g. `connect`, `start`, `process`, and `stop`) translate into
  coordinated calls to the methods of the processors of the graph.
'''

'''
Design notes:

* It's important to distinguish between input and output *ports* and
  input and output *data*. The idea is that data flow through ports.
  A port is a class-level concept, while data are an instance level
  concept. A `Processor` class declares its input and output ports
  in its plugin descriptor. A `Processor` instance receives
  information about its input and output data
'''

'''
Processor graph insights:

* A graph input port might connect directly to a graph output port.

* It is a good idea for graph input and output ports to be graph
  nodes, just like processors are. This allows the use of one type
  of edge specification for all connections. It also makes it
  easy to specify that an input port connects to multiple
  processor inputs, or that it connects directly to an output port.

* It is a good idea to support the definition of classes for
  processor graphs for which the graph is fixed, i.e. that
  create a fixed set of processors in their initializers
  and connect the processors in a fixed way. The initializer
  creates settings for the processors from its settings.

* It is also a good idea to support the more flexible specification
  of processor graphs via graph settings. This supports a different
  set of use cases than the definition in code of processor graph
  classes whose graphs are fixed. One possible way to support the
  more flexible type of processor would be to use metaprogramming to
  construct new processor graph classes from settings. Another way
  might be to have a processor graph class, say
  `ConfigurableProcessorGraph`, whose settings specify a processor
  graph. Some aspects of these approaches are murky to me.
  Would the metaprogramming approach really work, for example?
  Would classes created in that way be accessible as plugins?
  Is the `ConfigurableProcessorGraph` approach consistent with
  use of the processor class attributes `type_name`, `input_ports`,
  and `output_ports`? Are the class attributes `type_name`,
  `input_ports`, and `output_ports` really a good idea? 

* I think the last insight is probably relevant to the settings package,
  too.
'''


class Processor:

    """
    Processor that computes zero or more output sequences from
    zero or more input sequences.
    """


    type_name = 'Processor'

    # In the future, something like the following could specify the
    # settings type of a `Processor` subclass. The settings type could
    # be used to check the settings provided to the initializer, construct
    # a GUI for editing the settings, etc.
    # settings_type = None
    

    STATE_UNCONNECTED = 'unconnected'
    STATE_CONNECTED = 'connected'
    STATE_RUNNING = 'running'
    STATE_FINISHED = 'finished'


    @staticmethod
    def parse_settings(mapping):
        raise NotImplementedError()


    def __init__(self, name, settings=None):
        
        self._name = name

        if settings is None:
            self._settings = Bunch()
        else:
            self._settings = settings

        self._input_ports = self._create_input_ports()

        self._input_ports_by_name = {p.name: p for p in self._input_ports}

        self._output_ports = self._create_output_ports()

        self._output_ports_by_name = {p.name: p for p in self._output_ports}

        # Mapping from connected input port name to input settings.
        # The mapping does not include items for unconnected input ports.
        # This attribute is set by the `connect` method.
        self._input_settings = None

        # Mapping from output port name to output settings. This attribute
        # is set by the `connect` method.
        self._output_settings = None

        # Mapping from connected input port name to boolean indicating
        # whether or not input for that port is finished. The mapping
        # does not include items for unconnected input ports. This
        # attribute is set by the `connect` method.
        self._input_finished = None

        self._state = Processor.STATE_UNCONNECTED


    def _create_input_ports(self):
        return ()
    

    def _create_output_ports(self):
        return ()
    

    @property
    def name(self):
        return self._name
    

    @property
    def settings(self):
        return self._settings
    

    @property
    def input_ports(self):
        return self._input_ports
    

    @property
    def output_ports(self):
        return self._output_ports
    

    @property
    def state(self):
        return self._state
    

    @property
    def unconnected(self):
        return self._state == Processor.STATE_UNCONNECTED
    

    @property
    def connected(self):
        return self._state == Processor.STATE_CONNECTED
    

    @property
    def running(self):
        return self._state == Processor.STATE_RUNNING
    

    @property
    def finished(self):
        return self._state == Processor.STATE_FINISHED       
        

    def get_input_port(self, port_name):
        return self._input_ports_by_name[port_name]
    

    def get_output_port(self, port_name):
        return self._output_ports_by_name[port_name]
    

    def get_input_settings(self, port_name):
        return self._input_settings[port_name]
    

    def get_output_settings(self, port_name):
       return self._output_settings[port_name]


    def connect(self, input_settings=None):
        
        # Note that `input_settings` informs a processor which of
        # its inputs are connected. It includes an item for a
        # processor input if and only if the processor will receive
        # data through that input.

        self._check_state('connect', Processor.STATE_UNCONNECTED)

        # Get input settings.
        if input_settings is None:
            self._input_settings = {}
        else:
            self._input_settings = input_settings

        self._check_input_settings()

        self._output_settings = self._connect()

        names = frozenset(self._input_settings.keys())
        self._input_finished = {
            p.name: False for p in self.input_ports if p.name in names
        }

        self._state = Processor.STATE_CONNECTED


    def _check_state(self, operation, required_state):
        if self.state != required_state:
            raise DataflowError(
                f'Attempt to {operation} processor "{self.name}" in '
                f'"{self.state}" state. Processor must be in '
                f'"{required_state}" state.')


    def _check_input_settings(self):

        valid_port_names = frozenset(p.name for p in self.input_ports)

        for port_name in self._input_settings.keys():
            if not port_name in valid_port_names:
                raise ValueError(
                    f'Unrecognized input port name "{port_name}" in '
                    f'input settings for processor "{self.name}".')
            
        required_port_names = tuple(
            p.name for p in self.input_ports if p.connection_required)
        
        specified_port_names = frozenset(self._input_settings.keys())

        for port_name in required_port_names:
            if not port_name in specified_port_names:
                raise ValueError(
                    f'Input settings not specified for processor '
                    f'"{self.name}" port "{port_name}" for which '
                    f'connection is required.')
            

    def _connect(self):

        """
        Gets mapping from output port name to output settings.

        This method is responsible for propagating input data settings
        (e.g. signal channel count and sample rate) through a processor
        to its output settings. It is also responsible for performing
        any additional subclass-specific processing that must happen
        at connection time.

        The default implementation returns a mapping from output port
        name to empty output settings. The mapping includes an item
        for every output port, regardless of whether or not it is
        connected.
        """

        return {p.name: Bunch() for p in self.output_ports}
    

    def start(self):
        self._check_state('start', Processor.STATE_CONNECTED)
        self._start()
        self._state = Processor.STATE_RUNNING


    def _start(self):
        pass


    def process(self, input_data={}):

        """
        Processes input data and returns output data.

        A processor must be in the "running" state when this method
        is invoked. The method must transition to the "finished" state
        when processing finishes.

        Parameters
        ----------
        input_data : Mapping[str, Data]
            mapping from input port name to `Data`.

            For each value of the mapping, the `items` property is a
            sequence of input items and the `finished` property is
            `True` if and only if the input is finished.

        Returns
        -------
        Mapping[str, Data]
            mapping from output port name to `Data`.

            For each value of the mapping, the `items` property is a
            sequence of output items and the `finished` property is
            `True` if and only if the output is finished.

        Raises
        ------
        DataflowError
            if this processor is not in the `"running"` state.

        ValueError
            if the specified input data includes items for an input
            sequence that was previously indicated to be finished,
            or if it indicates that a sequence that was previously
            indicated to be finished is not finished.
        """

        self._check_state('process with', Processor.STATE_RUNNING)
        
        self._check_input_data(input_data)
                
        return self._process(input_data)


    def _check_input_data(self, input_data):

        for name, data in input_data.items():

            if self._input_finished[name]:
                # input already finished

                if len(data.items) != 0:
                    # input data includes new items
                     
                    raise ValueError(
                        f'Input items received for processor "{self.name}" '
                        f'input "{name}" after input finished.')
                
                if not data.finished:
                    # input data indicates that input is not finished

                    raise ValueError(
                        f'Input data for processor "{self.name}" '
                        f'input port "{name}" indicate that input is not '
                        f'finished, but previous input data indicated '
                        f'that it was.')


    def _process(self, input_data):

        """
        Processes input data and returns output data.

        The processor is guaranteed to be in the "running" state
        when this method runs. It must transition to the "finished"
        state during the run if processing finishes. At latest,
        processing must finish in the first call to this method in
        which all processor inputs have finished.

        Parameters
        ----------
        input_data : Mapping[str, Data]
            mapping from input port name to `Data`.

            For each value of the mapping, the `items` property is a
            sequence of input items and the `finished` property is
            `True` if and only if the input is finished.

        Returns
        -------
        Mapping[str, Data]
            mapping from output port name to `Data`.

            For each value of the mapping, the `items` property is a
            sequence of output items and the `finished` property is
            `True` if and only if the output is finished.
        """

        pass
