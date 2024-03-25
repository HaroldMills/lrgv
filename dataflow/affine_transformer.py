from dataflow.processor import Processor
from dataflow.graph import Graph
from vesper.util.bunch import Bunch


class Scaler(Processor):
    pass


class Offsetter(Processor):
    pass


class AffineTransformer(Graph):


    type_name = 'Affine Transformer'


    def _create_processors(self):

        s = self.settings

        settings = Bunch(scale_factor=s.scale_factor)
        scaler = Scaler('Scaler', settings)

        settings = Bunch(offset=s.offset)
        offsetter = Offsetter('Offsetter', settings)

        return (scaler, offsetter)
    

    def _create_connections(self):

        Connection = ProcessorGraphConnection
        scaler = self._processors_by_name['Scaler']
        offsetter = self._processors_by_name['Offsetter']

        return (

            Connection(
                self.input_ports['Input'],
                scaler.input_ports['Input']),

            Connection(
                scaler.output_ports['Output'],
                offsetter.input_ports['Input']),

            Connection(
                offsetter.output_ports['Output'],
                self.output_ports['Output'])

        )
