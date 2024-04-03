from dataflow import Data, Processor, SimpleProcessorMixin


class SimpleProcessor(SimpleProcessorMixin, Processor):


    """
    Processor with a single input port named "Input" and a single
    output port named "Output".
     
    To make the implementation of subclasses of this class as easy
    as possible, the class offers the simplified processing methods
    `_process_items` and `_process_item`. `_process_items` is invoked
    from the default implementation of the `_process` method, and
    `_process_item` is invoked from the default implementation of the
    `_process_items` method. A subclass will typically override either
    `_process_items` or `_process_item` but not both.
    """


    def _process(self, input_data):

        # The default implementation of this method assumes that this
        # processor produces no output items if it receives no input
        # items.

        input = input_data.get('Input')

        if input is None:
            return {}
        
        output_items = self._process_items(input.items, input.finished)
        output_data = Data(output_items, input.finished)

        if input.finished:
            self._state = Processor.STATE_FINISHED

        return {'Output': output_data}
    

    def _process_items(self, items, finished):

        # The default implementation of this method assumes that this
        # processor produces exactly one output for each input.

        item_count = len(items)

        def process_item(item, item_num):
            input_finished = finished and item_num == item_count - 1
            return self._process_item(item, input_finished)

        return tuple(process_item(item, i) for i, item in enumerate(items))
    

    def _process_item(self, item, finished):
        raise NotImplementedError()
