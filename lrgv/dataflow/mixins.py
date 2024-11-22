import itertools

from lrgv.dataflow import Data, InputPort, OutputPort, Processor


'''
This module contains some speculative and incomplete mixin classes
for the dataflow package. They are not currently used anywhere, but
I decided to commit them to the repository for safekeeping while I
work on other things for a while.

I'd like to make it easier to implement processors (including graphs)
that have a single input and process one input item at a time.
`SimpleProcessor` already does this to some extent with its
`_process_item` method.

I'd like to support this common use case better, though. For example,
I'd like to be able to run a graph with a single input on a sequence of
input items and have it invoke a custom error handler (one that logs a
warning, say) whenever the processing of an input item raises an exception.
The exception should interrupt the processing of that particular input,
but not the processing of any of the others. (Or perhaps the error handler
should decide that, perhaps returning if processing should continue or
raising an exception if it should not).

Where would such an error handler live? For `SimpleProcessor` I can
imagine adding a `_handle_item_error` method. What would we do for
graphs? Do we need a `SimpleGraph` class? Do we need to move the
`_process_items` and `_process_item` methods of `SimpleProcessor`
in their own mixin class that can be used with graphs? Perhaps the
class could be called `ItemwiseProcessorMixin`.

Maybe we would have these:

    SingleInputMixin
        Implements `_create_input_ports`.

    SingleOutputMixin
        Implements `_create_output_ports`.

    SingleInputOutputMixin(SingleInputMixin, SingleOutputMixin)

    ItemwiseProcessorMixin
        Implements `_process` for itemwise processor with one input and
        one output. Provides `_process_item` method to be overridden by
        subclasses.

    ItemwiseGraphMixin
        Implements `_process` for itemwise graph with one input and one
        output. Provides `_will_process_item`, `_did_process_item`, and
        `_handle_item_error` item processing hooks. Default implementations
        of first two methods do nothing. Third method receives a raised
        exception as an argument. It can respond to the exception, say
        by logging a warning, and either re-raise the exception or return.
        There is no return value. [What about the scenario where a graph
        comprises several processors that operate independently on each
        input item, and we don't want an exception raised by one processor
        to prevent processing by the others?]

I think `SimpleProcessor` as it is is a little confusing. The kind of
simplicity that inspires the name is having a single input port named
"Input" and a single output port named "Output", but processing one
input item at a time is a kind of simplicity, too. It only makes sense
to process one input item at a time if you only have one input port,
so the second kind of simplicity is dependent on the first.


Desiderata:

* Consider separating provision of common port configurations from
  provision of itemwise processing.

* Support itemwise processing with both single-item and multi-item output.

* Support per-item message logging for itemwise processing.

* Support flexible error handling for itemwise processing, including
  for both graphs


Possible simplifications to consider:

* A processor has no input port or one input port named "Input".

* A processor has no output port or one output port named "Output".

* All processors process a single input item at a time.

What processors have more than one input or more than one output?

Multiple input processors:
    * Summer
    * Multiplier
    * Multiplexer

Multiple output processors:

    * Demultiplexer
    * Processor that outputs real and imaginary parts of complex signal
      separately.

Are there processors that really need to process more than one input
at a time, for example to operate efficiently?
'''


chain = itertools.chain.from_iterable


class SingleInputMixin:

    """
    Mixin class for processor with a single input port named "Input".

    This class provides an implementation of the `_create_input_ports`
    method for such processors.
    """

    def _create_input_ports(self):
        return (InputPort(self),)


class SingleOutputMixin:

    """
    Mixin class for processor with a single output port named "Output".

    This class provides an implementation of the `_create_output_ports`
    method for such processors.
    """

    def _create_output_ports(self):
        return (OutputPort(self),)
    

class SingleInputSingleOutputMixin(SingleInputMixin, SingleOutputMixin):

    """
    Mixin class for processor with a single input port named "Input"
    and a single output port named "Output".

    This class provides an implementation of the `_create_input_ports`
    and `_create_output_ports` methods for such processors.
    """

    pass


class ItemwiseProcessorMixin:


    """
    Mixin class for processor with a single input port and a single
    output port that processes one input item at a time.
    
    To implement itemwise processing, a class can inherit from this class
    and implement its `_process_item` method.

    This class is for use by itemwise processors that do not necessarily
    produce one output item for each input item. For itemwise processors
    that produce exactly one output item for each input item, use
    `ItemwiseOneToOneProcessorMixin` instead.

    This class implements the `Processor._process` method to delegate
    item processing to a `_process_item` method one item at a time.
    """


    def _process(self, input_data):

        # Get the name of this processor's single input port.
        input_name = self.input_ports[0].name

        input = input_data.get(input_name)

        if input is None:
            return {}
        
        item_count = len(input.items)

        def process_item(item, item_num):
            finished = input.finished and item_num == item_count - 1
            return self._process_item(item, finished)

        # Given an input item, the `_process_item` method returns a
        # sequence of output items (possibly empty) for it. Get the output
        # item sequences for the current input items and flatten them to
        # make a single output item tuple.
        output_items = tuple(itertools.chain.from_iterable(
            process_item(item, i) for i, item in enumerate(input.items)))
        
        output_data = Data(output_items, input.finished)

        if input.finished:
            self._state = Processor.STATE_FINISHED

        # Get the name of this processor's single output port.
        output_name = self.output_ports[0].name

        return {output_name: output_data}
    

    def _process_item(self, item, finished):

        """
        Processes one input item to produce zero or more output items.

        Subclasses should implement this method.

        The processor is in the "running" state when this method is
        called. All processor state transitions are handled by the
        caller.

        Parameters
        ----------
        item : Any
            the input item to process.

        finished : bool
            `True` if and only if `item` is the final input item.
            

        Returns
        -------
        Sequence[Any]
            the sequence of output items (possibly empty) that result
            from processing `item`.
        """

        raise NotImplementedError()


class ItemwiseOneToOneProcessorMixin:


    """
    Mixin class for processor with a single input and a single output
    that processes one input item at a time and produces one output
    item for each input item.
    
    This class implements the `Processor._process` method to delegate
    item processing to a `_process_item` method one item at a time.
    """


    def _process(self, input_data):

        # Get the name of this processor's single input port.
        input_name = self.input_ports[0].name

        input = input_data.get(input_name)

        if input is None:
            return {}
        
        item_count = len(input.items)

        def process_item(item, item_num):
            finished = input.finished and item_num == item_count - 1
            return self._process_item(item, finished)

        # Given an input item, the `_process_item` method returns a
        # single output item for it. Get the output items in a tuple.
        output_items = \
            tuple(process_item(item, i) for i, item in enumerate(input.items))
        
        output_data = Data(output_items, input.finished)

        if input.finished:
            self._state = Processor.STATE_FINISHED

        # Get the name of this processor's single output port.
        output_name = self.output_ports[0].name

        return {output_name: output_data}
    

    def _process_item(self, item, finished):

        """
        Processes one input item to produce one output item.

        Subclasses should implement this method.

        The processor is in the "running" state when this method is
        called. All processor state transitions are handled by the
        caller.

        Parameters
        ----------
        item : Any
            the input item to process.

        finished : bool
            `True` if and only if `item` is the final input item.
            

        Returns
        -------
        Any
            the output item that results from processing `item`.
        """

        raise NotImplementedError()
    

class SingleOutputSource(SingleOutputMixin):
    pass


class SingleInputSingleOutputProcessor(SingleInputSingleOutputMixin):
    pass


class SingleInputSink(SingleInputMixin):
    pass


class ItemwiseSource(SingleOutputMixin):
    pass


class ItemwiseProcessor(SingleInputSingleOutputMixin, ItemwiseProcessorMixin):
    pass


class ItemwiseOneToOneProcessor(
        SingleInputSingleOutputMixin, ItemwiseOneToOneProcessorMixin):
    pass


class ItemwiseSink(SingleInputMixin, ItemwiseProcessorMixin):
    pass
