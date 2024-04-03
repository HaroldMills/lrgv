from dataflow import Data, Processor, SimpleSourceMixin


class SimpleSource(SimpleSourceMixin, Processor):


    """
    Processor with no input ports and a single output port named
    "Output".
    
    To make the implementation of subclasses of this class as easy
    as possible, the class offers the simplified processing methods
    `_process_items` and `_process_item`. `_process_items` is invoked
    from the default implementation of the `_process` method, and
    `_process_item` is invoked from the default implementation of the
    `_process_items` method. A subclass will typically override either
    `_process_items` or `_process_item` but not both.
    """


    def _process(self, _):

        output_items, finished = self._process_items()
        output_data = Data(output_items, finished)

        if finished:
            self._state = Processor.STATE_FINISHED

        return {'Output': output_data}
    

    def _process_items(self):
        output_item, finished = self._process_item()
        return (output_item,), finished
    

    def _process_item(self):
        raise NotImplementedError()
