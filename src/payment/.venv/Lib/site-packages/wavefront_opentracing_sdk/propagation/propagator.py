"""
Abstract Class of Propagator.

@author: Hao Song (songhao@vmware.com)
"""


# pylint: disable=E0012,R0205
class Propagator(object):
    """Abstract Class of Propagator."""

    def extract(self, carrier):
        """
        Extract wavefront span context from the given carrier.

        :param carrier: The carrier to extract the span context from
        :type carrier: object
        :return: Extracted Wavefront Span Context
        :rtype: WavefrontSpanContext
        """
        raise NotImplementedError

    def inject(self, span_context, carrier):
        """
        Inject the given context into the given carrier.

        :param span_context: The span context to serialize
        :type span_context: WavefrontSpanContext
        :param carrier: The carrier to inject the span context into
        :type carrier: object
        """
        raise NotImplementedError
