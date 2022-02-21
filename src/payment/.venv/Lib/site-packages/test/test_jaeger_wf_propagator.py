"""Unit Tests for Jaeger Wavefront Propagator.

@author: Hao Song (songhao@vmware.com)
"""
import unittest
import uuid

from wavefront_opentracing_sdk.propagation import JaegerWavefrontPropagator
from wavefront_opentracing_sdk.span_context import WavefrontSpanContext


class TestJaegerWavefrontPropagator(unittest.TestCase):
    """Unit Tests for Jaeger Wavefront Propagator."""

    jaeger_header = 'uber-trace-id'
    baggage_prefix = 'uberctx-'
    wf_jaeger_propagator = JaegerWavefrontPropagator(
        trace_id_header=jaeger_header, baggage_prefix=baggage_prefix)

    def test_trace_id_extract(self):
        """Test Trace ID Extraction."""
        val = '3871de7e09c53ae8:7499dd16d98ab60e:3771de7e09c55ae8:1'
        headers_text_map = {self.jaeger_header: val}
        ctx = self.wf_jaeger_propagator.extract(headers_text_map)
        self.assertIsNotNone(ctx)
        self.assertEqual(str(ctx.get_trace_id()),
                         '00000000-0000-0000-3871-de7e09c53ae8')
        self.assertEqual(str(ctx.get_span_id()),
                         '00000000-0000-0000-7499-dd16d98ab60e')
        self.assertEqual(ctx.get_baggage_item('parent-id'),
                         '00000000-0000-0000-7499-dd16d98ab60e')
        self.assertTrue(ctx.get_sampling_decision())

    def test_invalid_trace_id_extract(self):
        """Test Invalid Trace ID Extraction."""
        val = ':7499dd16d98ab60e:3771de7e09c55ae8:1'
        headers_text_map = {self.jaeger_header: val}
        ctx = self.wf_jaeger_propagator.extract(headers_text_map)
        self.assertIsNone(ctx)

    def test_trace_id_inject(self):
        """Test Trace ID Injection."""
        trace_id = uuid.UUID('00000000-0000-0000-3871-de7e09c53ae8')
        span_id = uuid.UUID('00000000-0000-0000-7499-dd16d98ab60e')
        headers_text_map = {}
        self.wf_jaeger_propagator.inject(WavefrontSpanContext(
            trace_id, span_id, None, True), headers_text_map)
        self.assertTrue(self.jaeger_header in headers_text_map)
        self.assertEqual(headers_text_map[self.jaeger_header],
                         '3871de7e09c53ae8:7499dd16d98ab60e:null:1')

    def test_jaeger_id_to_wavefront_uuid(self):
        """Test convert from Jaeger ID to Wavefront UUID."""
        hex_str_id = 'ef27b4b9f6e946f5ab2b47bbb24746c5'
        out = JaegerWavefrontPropagator.convert_to_uuid(hex_str_id)
        self.assertEqual(str(out), 'ef27b4b9-f6e9-46f5-ab2b-47bbb24746c5')

    def test_wavefront_uuid_to_jaeger_id_conversion(self):
        """Test convert from Wavefront UUID to Jaeger ID."""
        input = uuid.uuid1()
        hex_str = format(input.int, 'x')
        output = JaegerWavefrontPropagator.convert_to_uuid(hex_str)
        self.assertEqual(input, output)

    def test_jaeger_to_wavefront_id_conversion(self):
        """Test convert between Jaeger and Wavefront ID."""
        hex_str_in = '3871de7e09c53ae8'
        uuid_in = JaegerWavefrontPropagator.convert_to_uuid(hex_str_in)
        hex_str_out = format(uuid_in.int, 'x')
        self.assertEqual(hex_str_in, hex_str_out)


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
