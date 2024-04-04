from lrgv.dataflow import Processor, SimpleSinkMixin


class SimpleSink(SimpleSinkMixin, Processor):


    """
    Processor with a single input port named "Input" and no output ports.

    To make the implementation of subclasses of this class as easy
    as possible, the class offers the simplified processing methods
    `_process_items` and `_process_item`. `_process_items` is invoked
    from the default implementation of the `_process` method, and
    `_process_item` is invoked from the default implementation of the
    `_process_items` method. A subclass will typically override either
    `_process_items` or `_process_item` but not both.
    """


    def _process(self, input_data):

        input = input_data.get('Input')

        if input is not None:
        
            self._process_items(input.items, input.finished)

            if input.finished:
                self._state = Processor.STATE_FINISHED

        return {}
    

    def _process_items(self, items, finished):

        item_count = len(items)

        for item_num, item in enumerate(items):
            input_finished = finished and item_num == item_count - 1
            self._process_item(item, input_finished)
    

    def _process_item(self, item, finished):
        raise NotImplementedError()
