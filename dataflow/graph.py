from collections import defaultdict

from dataflow.dataflow_error import DataflowError
from dataflow.processor import Processor


# TODO: Consider supporting direct connections from graph input ports
# to graph output ports. Currently one can work around the lack of
# support for such connections using processors that copy their inputs
# to their outputs, but that feels a little kludgy.

# TODO: Add `_create_connnections_from_pairs` method that one can invoke
# like this:
#
# return self._create_connections_from_pairs((
#     (self, scaler),
#     ((scaler, 'Output'), offsetter),
#     (offsetter, (self, 'Output')),
# ))

# TODO: Add `_create_connections_from_yaml` method that one can invoke
# like this:
#
# return self._create_connections_from_yaml('''[
#     [Affine Transformer, Scaler],
#     [[Scaler, Output], Offsetter],
#     [Offsetter, [Affine Transformer, Output]]
# ]''')

# TODO: Consider relaxing uniqueness requirement for processor names.
# It can be difficult to ensure when there are lots of processors and
# when there are nested graphs. It allows processors to be represented
# by name in connections, which is helpful, but this is not always
# needed. It also helps ensure clear log messages.

# TODO: Consider moving linear connection to a new `LinearGraph`
# subclass of `Graph`.

# TODO: Consider implementing a `GraphSet` subclass of `Graph` that
# allows a set of closed (i.e. with no inputs or outputs) graphs to
# be manipulated as a unit.

# TODO: Complete docstrings.

# TODO: Implement more unit tests.
    

'''
Example YAML specification of a new `ProcessorGraph` subclass:

type_name: Affine Transformer

input_ports:

    - name: Input
      connection_required: True

output_ports:

    - name: Output
    
processors:

    - name: Scaler
      type: Scaler
      settings:
          scale_factor: 2

    - name: Offsetter
      type: Offsetter
      settings:
          offset: 1

connections:

    - source: Input
      destination: [Scaler, Input]

    - source: Scaler
      destination: Offsetter

    - source: Offsetter
      destination: Output
'''


class Graph(Processor):


    type_name = None


    def __init__(self, name, settings):

        super().__init__(name, settings)

        # Sequence of processor objects, of type `Processor`. The
        # processors must be ordered so that no processor follows
        # another processor for which it produces output.
        self._processors = tuple(self._create_processors())

        self._check_processors()

        # Get mapping from processor name to processor, including this
        # graph.
        self._processors_by_name = {p.name: p for p in self._processors}
        self._processors_by_name[self.name] = self

        # Get connections for this graph.
        self._connections = tuple(self._create_connections())

        self._check_connections()

        # Get mapping from connection destination to connection source.
        self._sources = {
            c.destination: c.source
            for c in self._connections
        }

        # Get mapping from processor to set of processor ports that are
        # connection destinations. For an internal processor the ports
        # are its connected input ports. For the graph the ports are
        # its output ports.
        self._destinations = defaultdict(set)
        for c in self._connections:
            d = c.destination
            self._destinations[d.processor].add(d)


    def _create_processors(self):
        raise NotImplementedError()
    

    def _check_processors(self):

        # Processor requirements:
        #
        # * The names of a graph and its processors must all be unique.

        names = set()

        for p in self._processors:

            name = p.name

            if name == self.name:
                raise DataflowError(
                    f'Processor "{name}" has same name as processor '
                    f'graph of which it would be a part. The names of a '
                    f'graph and its processors must all be unique.')
            
            elif name in names:
                raise DataflowError(
                    f'Two processors for processor graph "{self.name}" '
                    f'have the same name "{name}". The names of a '
                    f'graph and its processors must all be unique.')
            
            names.add(name)


    def _create_connections(self):

        """
        Gets the internal connections of this graph.

        Returns
        -------
        connections : Sequence[Connection]
            the internal connections of this graph.

            Each connection represents an edge of the processor graph,
            connecting a *source* to a *destination*. A source can be a
            graph input or a processor output, and a destination can be
            a processor input or a graph output. Currently a graph input
            cannot be connected directly to a graph output, though that
            may change in the future. The processor of a connection's
            source must differ from that of its destination.
        """

        return ()

    
    def _check_connections(self):

        # Connection requirements:
        #
        # * The processor of each connection source and destination
        #   must be either one of the processors of this graph or the
        #   graph itself.
        #
        # * The source of each connection must either be an input
        #   port of this graph or an output port of one of its
        #   processors.
        #
        # * The destination of each connection must either be an
        #   output port of this graph or an input port of one of its
        #   processors.
        #
        # * A graph input port cannot be connected directly to a
        #   graph output port.
        #
        # * An output port of a processor cannot be connected to
        #   an input port of the same processor.
        #   
        # * Each processor input port for which input is required
        #   and each graph output port must have a source.
        #
        # * No destination can be connected to more than one source.

        all_sources = self._get_valid_connection_sources()
        all_destinations = self._get_valid_connection_destinations()
        required_destinations = self._get_required_connection_destinations()

        connected_destinations = set()

        for c in self._connections:

            if c.source not in all_sources:
                raise DataflowError(
                    f'Unrecognized connection source "{c.source}" '
                    f'for processor graph "{self.name}".')
            
            if c.destination not in all_destinations:
                raise DataflowError(
                    f'Unrecognized connection destination "{c.destination}" '
                    f'for processor graph "{self.name}".')
            
            if c.source.processor is self and c.destination.processor is self:
                raise DataflowError(
                    f'Direct connection specified from input port '
                    f'"{c.source.name}" to output port '
                    f'"{c.destination.name}" for processor graph '
                    f'"{self.name}". Such connections are not currently '
                    f'supported.')
            
            if c.source.processor is c.destination.processor and \
                    c.source.processor is not self:
                raise DataflowError(
                    f'Connection specified from processor '
                    f'"{c.source.processor.name}" output port '
                    f'"{c.source.name}" to input port '
                    f'"{c.destination.name}" of same processor. '
                    f'A processor output port can only be connected '
                    f'to an input port of a different processor.')
            
            if c.destination in connected_destinations:
                raise DataflowError(
                    f'Connection destination "{c.destination}" specified '
                    f'in more than one connection for processor graph '
                    f'"{self.name}". A given destination can be specified '
                    f'for only one connection.')
            
            connected_destinations.add(c.destination)

        unconnected_required_destinations = \
            required_destinations - connected_destinations
        
        if len(unconnected_required_destinations) != 0:
            
            strings = [str(d) for d in unconnected_required_destinations]
            destinations = '{' + ', '.join(strings) + '}'
            
            raise DataflowError(
                f'Required connection destinations '
                f'{destinations} are unconnected '
                f'for processor graph "{self.name}". All processor '
                f'input ports that require input and all graph output '
                f'ports must be connected.')


    def _get_valid_connection_sources(self):

        graph_input_ports = frozenset(self.input_ports)
        
        processor_output_ports = \
            [frozenset(p.output_ports) for p in self._processors]
        
        return graph_input_ports.union(*processor_output_ports)
    

    def _get_valid_connection_destinations(self):

        graph_output_ports = frozenset(self.output_ports)
        
        processor_input_ports = \
            [frozenset(p.input_ports) for p in self._processors]
        
        return graph_output_ports.union(*processor_input_ports)
    

    def _get_required_connection_destinations(self):

        graph_output_ports = frozenset(self.output_ports)
        
        def get_required_input_ports(processor):
            return frozenset(
                p for p in processor.input_ports if p.connection_required)
        
        required_processor_input_ports = \
            [get_required_input_ports(p) for p in self._processors]
        
        return graph_output_ports.union(*required_processor_input_ports)
            

    def _connect(self):

        # Initialize source settings mapping with input settings.
        # Mapping is from source port (graph input port or processor
        # output port) to settings.
        source_settings = {
            self.get_input_port(name): settings
            for name, settings in self._input_settings.items()
        }

        def get_settings(destinations):

            def get_source_settings(destination):
                source = self._sources[destination]
                return source_settings[source]
        
            return {d.name: get_source_settings(d) for d in destinations}

        # Connect processors in order. Provide each processor with
        # input settings obtained from source settings accumulated
        # so far and add resulting processor output settings to
        # `source_settings`.
        for processor in self._processors:

            input_settings = get_settings(processor.input_ports)

            processor.connect(input_settings)

            output_settings = {
                p: processor.get_output_settings(p.name)
                for p in processor.output_ports
            }

            source_settings |= output_settings

        # Get graph output settings from accumulated source settings.
        return get_settings(self.output_ports)


    def _start(self):

        # Start processors in reverse order so that each processor
        # starts before the processors that produce its inputs.
        for processor in reversed(self._processors):
            processor.start()

        self._unfinished_processors = set(self._processors)


    def _process(self, input_data):

        # Initialize source data mapping with input data. Mapping
        # is from source port to data.
        source_data = {
            self.get_input_port(name): data
            for name, data in input_data.items()
        }

        def get_data(processor):

            def get_source_data(destination):
                source = self._sources[destination]
                return source_data[source]
            
            destinations = self._destinations[processor]
            return {d.name: get_source_data(d) for d in destinations}
        

        for processor in self._processors:

            # Get processor input data from accumulated source data.
            input_data = get_data(processor)

            # Process input data.
            output_data = processor.process(input_data)

            # Add output data to `source_data`.
            source_data |= {
                p: output_data[p.name]
                for p in processor.output_ports
            }

            # Remove processor from `self._unfinished_processors` if
            # it has finished.
            if processor.finished:
                self._unfinished_processors.remove(processor)

        # Transition to finished state if all processors have finished.
        if len(self._unfinished_processors) == 0:
            self._state = Processor.STATE_FINISHED

        # Get graph output data from accumulated source data.
        return get_data(self)
