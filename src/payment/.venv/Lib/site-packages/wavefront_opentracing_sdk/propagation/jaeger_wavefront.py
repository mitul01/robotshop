"""
Jaeger Wavefront Propagator.

@author: Hao Song (songhao@vmware.com)
"""
import uuid

from wavefront_opentracing_sdk.propagation.textmap import strip_prefix

from . import propagator
from .. import span_context


class JaegerWavefrontPropagator(propagator.Propagator):
    """Propagate Jaeger headers to/from a WavefrontSpanContext.

    Essentially allows for extracting Jaeger HTTP headers and creating a
    WavefrontSpanContext or injecting Jaeger aware HTTP headers from a
    WavefrontSpanContext.
    """

    _BAGGAGE_PREFIX = 'baggage-'
    _TRACE_ID_KEY = 'trace-id'
    _PARENT_ID_KEY = 'parent-id'
    _SAMPLING_DECISION_KEY = 'sampling-decision'

    def __init__(self, trace_id_header=_TRACE_ID_KEY,
                 baggage_prefix=_BAGGAGE_PREFIX):
        """Construct Jaeger Wavefront Propagator."""
        self.trace_id_header = trace_id_header
        self.baggage_prefix = baggage_prefix

    @staticmethod
    def context_from_trace_id_header(value):
        """Extract traceId, spanId, parentId and samplingDecision.

        From the 'uber-trace-id' HTTP header value that's in the format
        traceId:spanId:parentId:samplingDecision.

        :param value: 'uber-trace-id' header value
        :type value: str
        :return: extracted string list with ids
        :rtype: list[str]
        """
        if not value:
            return None
        header = value.split(':')
        if len(header) != 4:
            return None
        if not header[0]:
            return None
        return header

    def context_to_trace_id_header(self, span_ctx):
        """Extract traceId and spanId from a WavefrontSpanContext.

        And constructs a Jaeger client compatible header of the form
        traceId:spanId:parentId:samplingDecision.

        :param span_ctx: Wavefront Span Context to be injected
        :type span_ctx: WavefrontSpanContext
        :return: formatted header as string
        :rtype: str
        """
        trace_id = format(span_ctx.get_trace_id().int, 'x')
        span_id = format(span_ctx.get_span_id().int, 'x')
        sampling_decision = span_ctx.get_sampling_decision()
        parent_id = span_ctx.get_baggage_item(self._PARENT_ID_KEY)
        if not parent_id:
            parent_id = 'null'
        if not sampling_decision:
            sampling_decision = False
        return '{}:{}:{}:{}'.format(str(trace_id), str(span_id), parent_id,
                                    '1' if sampling_decision else '0')

    @staticmethod
    def convert_to_uuid(hex_id):
        """Construct UUID for traceId/spanId represented as hexString.

        Consisting of (low + high) 64 bits.

        :param hex_id: hexString form of traceId/spanId
        :type hex_id: str
        :return: UUID for traceId/spanId as expected by WavefrontSpanContext
        :rtype: uuid.UUID
        """
        id_low = int(hex_id, 16)
        return uuid.UUID(int=id_low)

    def inject(self, span_context, carrier):
        """
        Inject the given Span Context into TextMap Carrier.

        :param span_context: Wavefront Span Context to be injected
        :type span_context: WavefrontSpanContext
        :param carrier: Carrier
        :type carrier: dict
        """
        # pylint: disable=redefined-outer-name
        carrier.update({
            self.trace_id_header:
                self.context_to_trace_id_header(span_context)})
        for key, val in span_context.baggage.items():
            carrier.update({self.baggage_prefix + key: val})
        if span_context.is_sampled():
            carrier.update(
                {self._SAMPLING_DECISION_KEY: str(span_context.
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
        parent_id = None
        sampling_decision = None
        baggage = {}
        if not isinstance(carrier, dict):
            raise TypeError('Carrier is not a text map collection.')
        for key, val in carrier.items():
            key = key.lower()
            if key == self.trace_id_header:
                trace_data = self.context_from_trace_id_header(val)
                if not trace_data:
                    continue
                trace_id = self.convert_to_uuid(trace_data[0])
                span_id = self.convert_to_uuid(trace_data[1])
                parent_id = str(span_id)
                sampling_decision = trace_data[3] == '1'
            elif key.startswith(self.baggage_prefix.lower()):
                baggage.update({strip_prefix(self.baggage_prefix, key): val})
        if trace_id is None or span_id is None:
            return None
        if parent_id and parent_id.lower() != 'null':
            baggage.update({self._PARENT_ID_KEY: parent_id})
        return span_context.WavefrontSpanContext(trace_id, span_id, baggage,
                                                 sampling_decision)
