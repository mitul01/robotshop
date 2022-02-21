"""Wavefront Span Context.

@author: Hao Song (songhao@vmware.com)
"""
import opentracing


class WavefrontSpanContext(opentracing.SpanContext):
    """Wavefront Span Context."""

    def __init__(self, trace_id, span_id, baggage=None, decision=None):
        """Construct Wavefront Span Context.

        :param trace_id: Trace ID
        :type trace_id: uuid.UUID
        :param span_id: Span ID
        :type span_id: uuid.UUID
        :param baggage: Baggage
        :type baggage: dict
        :param decision: Decision of sampling
        :type decision: bool
        """
        self.trace_id = trace_id
        self.span_id = span_id
        self._baggage = baggage or opentracing.SpanContext.EMPTY_BAGGAGE
        self._sampling_decision = decision

    @property
    def baggage(self):
        """Baggage of WavefrontSpan."""
        return self._baggage or opentracing.SpanContext.EMPTY_BAGGAGE

    def get_baggage_item(self, key):
        """Get baggage item with key.

        :param key: Baggage key
        :return: Baggage value
        :rtype: str
        """
        return self._baggage.get(key)

    def with_baggage_item(self, key, value):
        """Create new span context with new dict of baggage and append item.

        :param key: key of the baggage item
        :type key: str
        :param value: value of the baggage item
        :type value: str
        :return: Span context itself
        :rtype: WavefrontSpanContext
        """
        baggage = dict(self._baggage)
        baggage[key] = value
        return WavefrontSpanContext(self.trace_id, self.span_id, baggage,
                                    self._sampling_decision)

    def with_sampling_decision(self, decision):
        """Create new span context with new decision of sampling.

        :param decision: Decision of sampling
        :type decision: bool
        :return: Span context itself
        :rtype: WavefrontSpanContext
        """
        return WavefrontSpanContext(self.trace_id, self.span_id, self.baggage,
                                    decision)

    def get_trace_id(self):
        """Get trace id from span context.

        :return: trace id of span context
        :rtype: uuid.UUID
        """
        return self.trace_id

    def get_span_id(self):
        """Get span id from span context.

        :return: span id of span context
        :rtype: uuid.UUID
        """
        return self.span_id

    def is_sampled(self):
        """Check sampling enabled or not."""
        return self._sampling_decision is not None

    def get_sampling_decision(self):
        """Get decision of sampling."""
        return self._sampling_decision

    @property
    def has_trace(self):
        """Return whether span context has both trace id and span id.

        :return: whether span context has both trace id and span id
        :rtype: bool
        """
        return self.trace_id and self.span_id

    def __str__(self):
        """Override __str__ func.

        :return: span context to string
        :rtype: str
        """
        return ('WavefrontSpanContext{{traceId={0.trace_id}, '
                'spanId={0.span_id}}}'.format(self))
