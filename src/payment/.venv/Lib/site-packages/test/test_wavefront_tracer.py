"""Unit Tests for Wavefront Tracer.

@author: Hao Song (songhao@vmware.com)
"""
import unittest
import uuid

import opentracing

from wavefront_opentracing_sdk import WavefrontSpanContext
from wavefront_opentracing_sdk import WavefrontTracer
from wavefront_opentracing_sdk.reporting import ConsoleReporter
from wavefront_opentracing_sdk.sampling import ConstantSampler

import wavefront_sdk.common


class TestTracer(unittest.TestCase):
    """Unit Tests for Wavefront Tracer."""

    application_tags = wavefront_sdk.common.ApplicationTags(
        application='app', service='service', cluster='us-west-1',
        shard='primary', custom_tags=[('custom_k', 'custom_v')])

    def test_inject_extract(self):
        """Test Inject / Extract."""
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags,
                                 samplers=[ConstantSampler(True)])
        span = tracer.start_span('test_op')
        self.assertIsNotNone(span)
        span.set_baggage_item('customer', 'test_customer')
        span.set_baggage_item('request_type', 'mobile')
        carrier = {}
        tracer.inject(span.context,
                      opentracing.propagation.Format.TEXT_MAP,
                      carrier)
        span.finish()
        ctx = tracer.extract(opentracing.propagation.Format.TEXT_MAP, carrier)
        self.assertTrue(ctx.is_sampled())
        self.assertTrue(ctx.get_sampling_decision())
        self.assertEqual('test_customer', ctx.get_baggage_item('customer'))
        self.assertEqual('mobile', ctx.get_baggage_item('request_type'))

    def test_sampling(self):
        """Test Sampling."""
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags,
                                 samplers=[ConstantSampler(True)])
        self.assertTrue(tracer.sample('test_op', 1, 0))
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags,
                                 samplers=[ConstantSampler(False)])
        self.assertFalse(tracer.sample('test_op', 1, 0))

    def test_active_span(self):
        """Test Active Span."""
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags)
        span = tracer.start_span('test_op_1')
        self.assertIsNotNone(span)
        span.finish()
        scope = tracer.start_active_span('test_op_2', finish_on_close=True)
        self.assertIsNotNone(scope)
        self.assertIsNotNone(scope.span)
        scope.close()

    def test_global_tags(self):
        """Test Global Tags."""
        global_tags = [('foo1', 'bar1'), ('foo2', 'bar2')]
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags,
                                 global_tags)
        span = tracer.start_span(operation_name='test_op',
                                 tags=[('foo3', 'bar3')])
        self.assertIsNotNone(span)
        self.assertIsNotNone(span.get_tags())
        self.assertIsNotNone(span.get_tags_as_list())
        self.assertIsNotNone(span.get_tags_as_map())
        self.assertEqual(9, len(span.get_tags()))
        self.assertTrue('app' in span.get_tags_as_map().get('application'))
        self.assertTrue('service' in span.get_tags_as_map().get('service'))
        self.assertTrue('us-west-1' in span.get_tags_as_map().get('cluster'))
        self.assertTrue('primary' in span.get_tags_as_map().get('shard'))
        self.assertTrue('custom_v' in span.get_tags_as_map().get('custom_k'))
        self.assertTrue('bar1' in span.get_tags_as_map().get('foo1'))
        self.assertTrue('bar2' in span.get_tags_as_map().get('foo2'))
        self.assertTrue('bar3' in span.get_tags_as_map().get('foo3'))
        span.finish()
        tracer.close()

    def test_global_multi_valued_tags(self):
        """Test Global Multi-valued Tags."""
        global_tags = [('key1', 'val1'), ('key1', 'val2')]
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags,
                                 global_tags)
        span = tracer.start_span(operation_name='test_op')
        self.assertIsNotNone(span)
        self.assertIsNotNone(span.get_tags())
        self.assertIsNotNone(span.get_tags_as_list())
        self.assertIsNotNone(span.get_tags_as_map())
        self.assertEqual(7, len(span.get_tags_as_map()))
        self.assertTrue('app' in span.get_tags_as_map().get('application'))
        self.assertTrue('service' in span.get_tags_as_map().get('service'))
        self.assertTrue('us-west-1' in span.get_tags_as_map().get('cluster'))
        self.assertTrue('primary' in span.get_tags_as_map().get('shard'))
        self.assertTrue('custom_v' in span.get_tags_as_map().get('custom_k'))
        self.assertTrue('val1' in span.get_tags_as_map().get('key1'))
        self.assertTrue('val2' in span.get_tags_as_map().get('key1'))
        span.finish()
        tracer.close()

    def test_baggage_items(self):
        """Test Baggage Items."""
        # Create parentCtx with baggage items
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags)
        baggage_item = {'foo': 'bar', 'user': 'name'}
        parent_ctx = WavefrontSpanContext(trace_id=uuid.uuid1(),
                                          span_id=uuid.uuid1(),
                                          baggage=baggage_item,
                                          decision=True)
        span = tracer.start_span('test_op', child_of=parent_ctx)
        self.assertEqual('bar', span.get_baggage_item('foo'))
        self.assertEqual('name', span.get_baggage_item('user'))

        # Parent and Follows
        baggage_item = {'tracer': 'id', 'db.name': 'name'}
        follows_ctx = WavefrontSpanContext(trace_id=uuid.uuid1(),
                                           span_id=uuid.uuid1(),
                                           baggage=baggage_item,
                                           decision=True)
        span = tracer.start_span(
            'test_op', references=[opentracing.child_of(parent_ctx),
                                   opentracing.child_of(follows_ctx)])
        self.assertEqual('bar', span.get_baggage_item('foo'))
        self.assertEqual('name', span.get_baggage_item('user'))
        self.assertEqual('id', span.get_baggage_item('tracer'))
        self.assertEqual('name', span.get_baggage_item('db.name'))

        # Validate root span
        span = tracer.start_span('test_op')
        self.assertIsNotNone(span.context.baggage)
        self.assertTrue(not bool(span.context.baggage))


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
