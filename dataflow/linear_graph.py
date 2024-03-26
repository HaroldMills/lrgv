from dataflow.connection import Connection
from dataflow.dataflow_error import DataflowError
from dataflow.graph import Graph


class LinearGraph(Graph):


    type_name = None


    def _create_connections(self):

        # Convenience method that a subclass can invoke from
        # `_create_connections` if its graph is just a linear sequence
        # of processors.

        def input_count(processor):
            return len(processor.input_ports)
        
        def output_count(processor):
            return len(processor.output_ports)
        
        def handle_error(message):
            raise DataflowError(
                f'Cannot create linear connections for processor '
                f'graph "{self.name}". {message}')


        processors = self._processors

        if len(processors) == 0:
            return ()
        

        # Check that graph and processors don't have multiple input
        # or output ports.

        if input_count(self) > 1:
            handle_error(f'Graph has more than one input port.')
            
        if output_count(self) > 1:
            handle_error(f'Graph has more than one output port.')

        for processor in processors:
            
            if input_count(processor) > 1:
                handle_error(
                    f'Processor "{processor.name}" has more than one '
                    f'input port.')
            
            if output_count(processor) > 1:
                handle_error(
                    f'Processor "{processor.name}" has more than one '
                    f'output port.')
                

        # Start with no connections.
        connections = []


        # Add connection from graph input port to first processor
        # input port if needed.

        processor = processors[0]

        if input_count(self) == 0:
            # graph has no input ports
            
            if input_count(processor) == 1:
                # first processor has one input port

                handle_error(
                    f'Graph has no input ports but first processor '
                    f'"{processor.name}" has one.')
                
        else:
            # graph has one input port

            if input_count(processor) == 0:
                # first processor has no input ports

                handle_error(
                    f'Graph has one input port but first processor '
                    f'"{processor.name}" has none.')
                
            else:
                # first processor has one input port

                connections.append(
                    Connection(self.input_ports[0], processor.input_ports[0]))
            

        # Add connections between processors. These include a connection
        # from the output port of each processor to the input port of
        # the next processor for all but the last processor.
                
        for i in range(len(processors) - 1):

            source = processors[i]
            dest = processors[i + 1]

            if output_count(source) == 0:
                handle_error(f'Processor "{source.name}" has no output ports.')

            elif input_count(dest) == 0:
                handle_error(f'Processor "{dest.name}" has no input ports.')
                
            else:
                # source processor has one output port and destination
                # processor has one input port
                
                connections.append(
                    Connection(source.output_ports[0], dest.input_ports[0]))
                

        # Add connection from last processor output port to graph
        # output port if needed.
                
        processor = processors[-1]

        if output_count(self) == 0:
            # graph has no output ports
            
            if output_count(processor) == 1:
                # last processor has one output port

                handle_error(
                    f'Graph has no output ports but last processor '
                    f'"{processor.name}" has one.')
                
        else:
            # graph has one output port

            if output_count(processor) == 0:
                # last processor has no input ports

                handle_error(
                    f'Graph has one output port but last processor '
                    f'"{processor.name}" has none.')
                
            else:
                # last processor has one output port

                connections.append(Connection(
                    processor.output_ports[0], self.output_ports[0]))
                

        # Return connections in a tuple.
        return tuple(connections)