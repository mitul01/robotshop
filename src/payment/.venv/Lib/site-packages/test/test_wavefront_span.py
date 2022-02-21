"""Unit Tests for Wavefront Span.

@author: Hao Song (songhao@vmware.com)
"""
import datetime
import time
import unittest
import uuid

import freezegun

import opentracing.ext.tags
from opentracing.tags import HTTP_STATUS_CODE

try:
    import mock
except ImportError:
    from unittest import mock

from wavefront_opentracing_sdk import WavefrontSpanContext
from wavefront_opentracing_sdk import WavefrontTracer
from wavefront_opentracing_sdk.reporting import ConsoleReporter
from wavefront_opentracing_sdk.reporting import WavefrontSpanReporter
from wavefront_opentracing_sdk.sampling import ConstantSampler

import wavefront_sdk
from wavefront_sdk.common.constants import NULL_TAG_VAL


class TestSpan(unittest.TestCase):
    """Unit Tests for Wavefront Span."""

    application_tags = wavefront_sdk.common.ApplicationTags(
        application='app', service='service', cluster='us-west-1',
        shard='primary', custom_tags=[('custom_k', 'custom_v')])

    def test_ignore_active_span(self):
        """Test Ignore Active Span."""
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags)
        scope = tracer.start_active_span('test_op')
        active_span = scope.span

        # Span created with ignore_active_span=False by default.
        child_span = tracer.start_span(
            operation_name='child_op',
            ignore_active_span=False)
        active_trace_id = str(active_span.trace_id)
        child_trace_id = str(child_span.trace_id)
        self.assertEqual(active_trace_id, child_trace_id)
        child_span.finish()

        # Span created with ignore_active_span=True.
        child_span = tracer.start_span(
            operation_name='child_op',
            ignore_active_span=True)
        child_trace_id = str(child_span.trace_id)
        self.assertNotEqual(active_trace_id, child_trace_id)
        child_span.finish()

        scope.close()
        tracer.close()

    def test_multi_valued_tags(self):
        """Test Multi-valued Tags."""
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags)
        span = tracer.start_span('test_op', tags=[
            ('key1', 'val1'), ('key1', 'val2'),
            ('application', 'new_app')])
        self.assertIsNotNone(span)
        self.assertIsNotNone(span.get_tags())
        self.assertIsNotNone(span.get_tags_as_list())
        self.assertIsNotNone(span.get_tags_as_map())
        self.assertEqual(7, len(span.get_tags_as_map()))
        self.assertTrue('new_app' in span.get_tags_as_map().get('application'))
        self.assertTrue('service' in span.get_tags_as_map().get('service'))
        self.assertTrue('us-west-1' in span.get_tags_as_map().get('cluster'))
        self.assertTrue('primary' in span.get_tags_as_map().get('shard'))
        self.assertTrue('custom_v' in span.get_tags_as_map().get('custom_k'))
        self.assertTrue('val1' in span.get_tags_as_map().get('key1'))
        self.assertTrue('val2' in span.get_tags_as_map().get('key1'))
        span.finish()
        tracer.close()

    def test_tags_as_dict(self):
        """Test Multi-valued Tags."""
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags)
        span = tracer.start_span('test_op', tags={
            'key1': 'val1', 'application': 'new_app'})
        self.assertIsNotNone(span)
        self.assertIsNotNone(span.get_tags())
        self.assertIsNotNone(span.get_tags_as_list())
        self.assertIsNotNone(span.get_tags_as_map())
        self.assertEqual(7, len(span.get_tags_as_map()))
        self.assertTrue('new_app' in span.get_tags_as_map().get('application'))
        self.assertTrue('service' in span.get_tags_as_map().get('service'))
        self.assertTrue('us-west-1' in span.get_tags_as_map().get('cluster'))
        self.assertTrue('primary' in span.get_tags_as_map().get('shard'))
        self.assertTrue('custom_v' in span.get_tags_as_map().get('custom_k'))
        self.assertTrue('val1' in span.get_tags_as_map().get('key1'))
        span.finish()
        tracer.close()

    def test_forced_sampling(self):
        """Test span with forced sampling."""
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags,
                                 samplers=[ConstantSampler(False)])
        span = tracer.start_span('test_op')
        self.assertIsNotNone(span)
        self.assertIsNotNone(span.context)
        self.assertIsNotNone(span.context.get_sampling_decision())
        self.assertFalse(span.context.get_sampling_decision())

        span.set_tag(opentracing.ext.tags.SAMPLING_PRIORITY, 1)
        self.assertIsNotNone(span.context.get_sampling_decision())
        self.assertTrue(span.context.get_sampling_decision())

        span = tracer.start_span('test_op')
        self.assertIsNotNone(span)
        self.assertIsNotNone(span.context)
        self.assertIsNotNone(span.context.get_sampling_decision())
        self.assertFalse(span.context.get_sampling_decision())

        span.set_tag(opentracing.ext.tags.ERROR, True)
        self.assertIsNotNone(span.context.get_sampling_decision())
        self.assertTrue(span.context.get_sampling_decision())

        span = tracer.start_span('test_op')
        self.assertIsNotNone(span)
        self.assertIsNotNone(span.context)
        self.assertIsNotNone(span.context.get_sampling_decision())
        self.assertFalse(span.context.get_sampling_decision())

        span.set_tag("debug", True)
        self.assertIsNotNone(span.context.get_sampling_decision())
        self.assertTrue(span.context.get_sampling_decision())

        span = tracer.start_span('test_op')
        self.assertIsNotNone(span)
        self.assertIsNotNone(span.context)
        self.assertIsNotNone(span.context.get_sampling_decision())
        self.assertFalse(span.context.get_sampling_decision())

        span.set_tag("debug", "true")
        self.assertIsNotNone(span.context.get_sampling_decision())
        self.assertTrue(span.context.get_sampling_decision())

    def test_root_sampling(self):
        """Test root span with sampling."""
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags,
                                 samplers=[ConstantSampler(False)])
        span = tracer.start_span('test_op')
        self.assertIsNotNone(span)
        self.assertIsNotNone(span.context)
        self.assertEqual(0, len(span.get_parents()))
        self.assertEqual(0, len(span.get_follows()))
        self.assertIsNotNone(span.context.get_sampling_decision())
        self.assertFalse(span.context.get_sampling_decision())

        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags,
                                 samplers=[ConstantSampler(True)])
        span = tracer.start_span('test_op')
        self.assertIsNotNone(span)
        self.assertIsNotNone(span.context)
        self.assertEqual(0, len(span.get_parents()))
        self.assertEqual(0, len(span.get_follows()))
        self.assertIsNotNone(span.context.get_sampling_decision())
        self.assertTrue(span.context.get_sampling_decision())

    def test_positive_child_sampling(self):
        """Test child span with positive sampling."""
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags,
                                 samplers=[ConstantSampler(False)])
        parent_ctx = WavefrontSpanContext(trace_id=uuid.uuid1(),
                                          span_id=uuid.uuid1(),
                                          decision=True)
        span = tracer.start_span('test_op', child_of=parent_ctx)
        self.assertFalse(tracer.sample(span.operation_name, span.trace_id, 0))
        self.assertIsNotNone(span)
        self.assertEqual(parent_ctx.trace_id, span.trace_id)
        self.assertTrue(span.context.is_sampled())
        self.assertIsNotNone(span.context.get_sampling_decision())
        self.assertTrue(span.context.get_sampling_decision())

    def test_negative_child_sampling(self):
        """Test child span with positive sampling."""
        tracer = WavefrontTracer(ConsoleReporter(), self.application_tags,
                                 samplers=[ConstantSampler(True)])
        parent_ctx = WavefrontSpanContext(trace_id=uuid.uuid1(),
                                          span_id=uuid.uuid1(),
                                          decision=False)
        span = tracer.start_span('test_op', child_of=parent_ctx)
        self.assertTrue(tracer.sample(span.operation_name, span.trace_id, 0))
        self.assertIsNotNone(span)
        self.assertEqual(parent_ctx.trace_id, span.trace_id)
        self.assertTrue(span.context.is_sampled())
        self.assertIsNotNone(span.context.get_sampling_decision())
        self.assertFalse(span.context.get_sampling_decision())

    @mock.patch('wavefront_sdk.proxy.WavefrontProxyClient')
    def test_valid_wavefront_span(self, wf_sender):
        """Test wavefront generated data."""
        operation_name = 'dummy_op'
        source = 'wavefront_source'
        wf_sender = wf_sender()
        tracer = WavefrontTracer(WavefrontSpanReporter(wf_sender, source),
                                 self.application_tags,
                                 samplers=[ConstantSampler(True)],
                                 report_frequency_millis=500)
        with freezegun.freeze_time(
                datetime.datetime(year=1, month=1, day=1)) as frozen_datetime:
            span = tracer.start_active_span(operation_name,
                                            tags=[('application', 'new_app')])
            span.close()
            frozen_datetime.tick(delta=datetime.timedelta(seconds=61))
            time.sleep(1)
            tracer.close()
        wf_sender.assert_has_calls([
            mock.call.send_span(
                operation_name, mock.ANY, 0, source, mock.ANY, mock.ANY, [],
                [], [('application', 'new_app'),
                     ('service', 'service'),
                     ('cluster', 'us-west-1'),
                     ('shard', 'primary'),
                     ('custom_k', 'custom_v'),
                     ('component', 'none')],
                span_logs=[]),
            mock.call.send_delta_counter(
                name='∆tracing.derived.new_app.service.{}.invocation.'
                     'count'.format(operation_name),
                source=source,
                tags={'application': 'new_app',
                      'service': 'service',
                      'cluster': 'us-west-1',
                      'shard': 'primary',
                      'custom_k': 'custom_v',
                      'component': 'none',
                      'operationName': operation_name,
                      'span.kind': NULL_TAG_VAL},
                value=1),
            mock.call.send_delta_counter(
                name='∆tracing.derived.new_app.service.{}.total_time.millis.'
                     'count'.format(operation_name),
                source=source,
                tags={'application': 'new_app', 'service': 'service',
                      'cluster': 'us-west-1', 'shard': 'primary',
                      'custom_k': 'custom_v', 'component': 'none',
                      'operationName': 'dummy_op', 'span.kind': NULL_TAG_VAL},
                value=mock.ANY),
            mock.call.send_metric(
                '~component.heartbeat', 1.0, mock.ANY,
                source,
                {'application': 'app',
                 'cluster': 'us-west-1',
                 'service': 'service', 'shard': 'primary',
                 'custom_k': 'custom_v',
                 'component': 'wavefront-generated'}),
            mock.call.send_distribution(
                centroids=mock.ANY,
                histogram_granularities={'!M'},
                name='tracing.derived.new_app.service.{}.duration.'
                     'micros'.format(operation_name),
                source=source,
                tags={'application': 'new_app',
                      'service': 'service',
                      'cluster': 'us-west-1',
                      'shard': 'primary',
                      'custom_k': 'custom_v',
                      'component': 'none',
                      'operationName': operation_name,
                      'span.kind': NULL_TAG_VAL},
                timestamp=mock.ANY)
        ], any_order=True)

    @mock.patch('wavefront_sdk.proxy.WavefrontProxyClient')
    def test_custom_red_metrics_tags(self, wf_sender):
        """Test custom RED metrics tags."""
        operation_name = 'dummy_op'
        source = 'wavefront_source'
        wf_sender = wf_sender()
        tracer = WavefrontTracer(WavefrontSpanReporter(wf_sender, source),
                                 self.application_tags,
                                 samplers=[ConstantSampler(True)],
                                 report_frequency_millis=500,
                                 red_metrics_custom_tag_keys={'env', 'tenant'})
        with freezegun.freeze_time(
                datetime.datetime(year=1, month=1, day=1)) as frozen_datetime:
            span = tracer.start_active_span(operation_name=operation_name,
                                            tags=[('tenant', 'tenant1'),
                                                  ('env', 'staging'),
                                                  (HTTP_STATUS_CODE, '200')])
            span.close()
            frozen_datetime.tick(delta=datetime.timedelta(seconds=61))
            time.sleep(1)
            tracer.close()
        wf_sender.assert_has_calls([
            mock.call.send_span(
                operation_name, mock.ANY, 0, source, mock.ANY, mock.ANY, [],
                [], [('tenant', 'tenant1'),
                     ('env', 'staging'),
                     (HTTP_STATUS_CODE, '200'),
                     ('application', 'app'),
                     ('service', 'service'),
                     ('cluster', 'us-west-1'),
                     ('shard', 'primary'),
                     ('custom_k', 'custom_v'),
                     ('component', 'none')],
                span_logs=[]),
            mock.call.send_delta_counter(
                name='∆tracing.derived.app.service.{}.invocation.'
                     'count'.format(operation_name),
                source=source,
                tags={'application': 'app',
                      'service': 'service',
                      'cluster': 'us-west-1',
                      'shard': 'primary',
                      'component': 'none',
                      'custom_k': 'custom_v',
                      HTTP_STATUS_CODE: '200',
                      'operationName': operation_name,
                      'tenant': 'tenant1',
                      'env': 'staging',
                      'span.kind': NULL_TAG_VAL},
                value=1),
            mock.call.send_delta_counter(
                name='∆tracing.derived.app.service.{}.total_time.millis.'
                     'count'.format(operation_name),
                source=source,
                tags={'application': 'app', 'service': 'service',
                      'cluster': 'us-west-1', 'shard': 'primary',
                      'component': 'none',
                      'custom_k': 'custom_v',
                      HTTP_STATUS_CODE: '200',
                      'operationName': 'dummy_op',
                      'tenant': 'tenant1', 'env': 'staging',
                      'span.kind': NULL_TAG_VAL},
                value=mock.ANY),
            mock.call.send_metric(
                '~component.heartbeat', 1.0, mock.ANY,
                source,
                {'application': 'app',
                 'cluster': 'us-west-1',
                 'service': 'service', 'shard': 'primary',
                 'custom_k': 'custom_v',
                 'component': 'wavefront-generated'}),
            mock.call.send_distribution(
                centroids=mock.ANY,
                histogram_granularities={'!M'},
                name='tracing.derived.app.service.{}.duration.'
                     'micros'.format(operation_name),
                source=source,
                tags={'application': 'app',
                      'service': 'service',
                      'cluster': 'us-west-1',
                      'shard': 'primary',
                      'component': 'none',
                      'custom_k': 'custom_v',
                      HTTP_STATUS_CODE: '200',
                      'operationName': operation_name,
                      'tenant': 'tenant1',
                      'env': 'staging',
                      'span.kind': NULL_TAG_VAL},
                timestamp=mock.ANY)
        ], any_order=True)

    @mock.patch('wavefront_sdk.proxy.WavefrontProxyClient')
    def test_error_span_duration_histogram(self, wf_sender):
        """Test duration histogram generated from error span."""
        operation_name = 'dummy_op'
        source = 'wavefront_source'
        wf_sender = wf_sender()
        tracer = WavefrontTracer(WavefrontSpanReporter(wf_sender, source),
                                 self.application_tags,
                                 report_frequency_millis=500)
        with freezegun.freeze_time(
                datetime.datetime(year=1, month=1, day=1)) as frozen_datetime:
            span = tracer.start_active_span(operation_name=operation_name,
                                            tags=[('tenant', 'tenant1'),
                                                  ('env', 'staging')])
            span.span.set_tag(opentracing.ext.tags.ERROR, True)
            span.close()
            frozen_datetime.tick(delta=datetime.timedelta(seconds=61))
            time.sleep(1)
            tracer.close()
        wf_sender.assert_has_calls([
            mock.call.send_distribution(
                centroids=mock.ANY,
                histogram_granularities={'!M'},
                name='tracing.derived.app.service.{}.duration.'
                     'micros'.format(operation_name),
                source=source,
                tags={'application': 'app',
                      'service': 'service',
                      'cluster': 'us-west-1',
                      'shard': 'primary',
                      'error': 'true',
                      'custom_k': 'custom_v',
                      'component': 'none',
                      'operationName': operation_name,
                      'span.kind': NULL_TAG_VAL},
                timestamp=mock.ANY)
        ], any_order=True)


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
