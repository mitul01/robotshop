"""
TextMap Propagator.

@author: Hao Song (songhao@vmware.com)
"""
import uuid

from . import propagator
from .. import span_context


class TextMapPropagator(propagator.Propagator):
    """Propagate contexts within TextMaps."""

    _BAGGAGE_PREFIX = 'wf-ot-'
    _TRACE_ID = _BAGGAGE_PREFIX + 'traceid'
    _SPAN_ID = _BAGGAGE_PREFIX + 'spanid'
    _SAMPLE = _BAGGAGE_PREFIX + 'sample'

    def inject(self, span_context, carrier):
        """
        Inject the given Span Context into TextMap Carrier.

        :param span_context: Wavefront Span Context to be injected
        :type span_context: WavefrontSpanContext
        :param carrier: Carrier
        :type carrier: dict
        """
        # pylint: disable=redefined-outer-name
        if not isinstance(carrier, dict):
            raise TypeError('Carrier not a text map collection.')
        carrier.update({self._TRACE_ID: str(span_context.get_trace_id())})
        carrier.update({self._SPAN_ID: str(span_context.get_span_id())})
        for key, val in span_context.baggage.items():
            carrier.update({self._BAGGAGE_PREFIX + key: val})
        if span_context.is_sampled():
            carrier.update({self._SAMPLE: str(span_context.
                                              get_sampling_decision())})

    def extract(self, carrier):
        """
        Extract wavefront span context from the given carrier.

        :param carrier: Carrier
        :type carrier: dict
        :return: Wavefront Span Context
        :rtype: WavefrontSpanContext
        """
        trace_id = None
        span_id = None
        sampling = None
        baggage = {}
        if not isinstance(carrier, dict):
            raise TypeError('Carrier not a text map collection.')
        for key, val in carrier.items():
            key = key.lower()
            if key == self._TRACE_ID:
                trace_id = uuid.UUID(val)
            elif key == self._SPAN_ID:
                span_id = uuid.UUID(val)
            elif key == self._SAMPLE:
                sampling = bool(val == 'True')
            elif key.startswith(self._BAGGAGE_PREFIX):
                baggage.update({strip_prefix(self._BAGGAGE_PREFIX, key): val})
        if trace_id is None or span_id is None:
            return None
        return span_context.WavefrontSpanContext(trace_id, span_id, baggage,
                                                 sampling)


def strip_prefix(prefix, key):
    """
    Strip the prefix of baggage items.

    :param prefix: Prefix to be stripped.
    :type prefix: str
    :param key: Baggage item to be striped
    :type key: str
    :return: Striped baggage item
    :rtype: str
    """
    return key[len(prefix):]
