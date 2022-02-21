"""Wavefront Tracer.

@author: Hao Song (songhao@vmware.com)
"""
from __future__ import division

import logging
import re
import time
import uuid

import opentracing
import opentracing.scope_managers
from opentracing.tags import COMPONENT, HTTP_STATUS_CODE, SPAN_KIND

from wavefront_pyformance import delta
from wavefront_pyformance import tagged_registry
from wavefront_pyformance import wavefront_histogram
from wavefront_pyformance import wavefront_reporter

import wavefront_sdk.common
from wavefront_sdk.common import constants

from .propagation import registry
from .reporting import CompositeReporter
from .reporting import WavefrontSpanReporter
from .sampling.sampler import Sampler
from .span import WavefrontSpan
from .span_context import WavefrontSpanContext

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class WavefrontTracer(opentracing.Tracer):
    """Wavefront Tracer."""

    DURATION_SUFFIX = '.duration.micros'
    ERROR_SUFFIX = '.error'
    INVOCATION_SUFFIX = '.invocation'
    OPERATION_NAME_TAG = 'operationName'
    OPENTRACING_COMPONENT = 'opentracing'
    PYTHON_COMPONENT = 'python'
    TOTAL_TIME_SUFFIX = '.total_time.millis'
    WAVEFRONT_GENERATED_COMPONENT = 'wavefront-generated'

    # pylint: disable=too-many-arguments
    def __init__(self, reporter, application_tags, global_tags=None,
                 samplers=None, report_frequency_millis=60000,
                 red_metrics_custom_tag_keys=None):
        """Construct Wavefront Tracer.

        :param reporter: Reporter
        :type reporter: :class:`Reporter`
        :param application_tags: Application Tags
        :type application_tags: :class:`ApplicationTags`
        :param global_tags: Global tags for the tracer
        :type global_tags: list of pair
        :param samplers: Samplers for the tracer
        :type samplers: list of samplers
        :type red_metrics_custom_tag_keys: Custom RED metrics tags.
        :param red_metrics_custom_tag_keys: set of str
        """
        super().__init__(
            opentracing.scope_managers.ThreadLocalScopeManager())
        self._reporter = reporter
        self._tags = global_tags or []
        self._tags.extend(application_tags.get_as_list())
        self._samplers = samplers
        self.registry = registry.PropagatorRegistry()
        self.single_valued_tag_keys = {constants.APPLICATION_TAG_KEY,
                                       constants.SERVICE_TAG_KEY,
                                       constants.CLUSTER_TAG_KEY,
                                       constants.SHARD_TAG_KEY}
        self.report_frequency_millis = report_frequency_millis
        self.red_metrics_custom_tag_keys = {SPAN_KIND}
        if red_metrics_custom_tag_keys:
            self.red_metrics_custom_tag_keys. \
                update(red_metrics_custom_tag_keys)
        wf_span_reporter = self.get_wavefront_span_reporter(reporter)
        if wf_span_reporter is not None:
            self.wf_internal_reporter, self.wf_derived_reporter, self. \
                heartbeater_service = self. \
                instantiate_wavefront_stats_reporter(wf_span_reporter,
                                                     application_tags)
            wf_span_reporter.set_metrics_reporter(self.wf_internal_reporter)
        else:
            self.wf_internal_reporter = None
            self.wf_derived_reporter = None
            self.heartbeater_service = None

    # pylint: disable=too-many-arguments,too-many-branches,too-many-locals
    def start_span(self, operation_name=None, child_of=None, references=None,
                   tags=None, start_time=None, ignore_active_span=False):
        r"""
        Start and return a new :class:`Span` representing a unit of work.

        :param operation_name: Operation Name
        :type operation_name: str
        :param child_of: (optional) a WavefrontSpan or WavefrontSpanContext
            instance representing the parent in a REFERENCE_CHILD_OF reference.
            If specified, the `references` parameter must be omitted.
        :type child_of: WavefrontSpanContext or WavefrontSpan
        :param references: (optional) references that identify one or more
            parent :class:`SpanContext`\ s. (See the Reference documentation
            for detail).
        :type references: `list` of `opentracing.Reference`
        :param tags: optional span tags (either list of (tag_key, tag_value)
            pairs or a dictionary).
        :type tags: dict or list of pair
        :param start_time: an explicit Span start time as a unix timestamp per
            :meth:`time.time()`
        :type start_time: float
        :param ignore_active_span: an explicit flag that ignores the current
            active :class:`Scope` and creates a root :class:`Span`.
        :type ignore_active_span: bool
        :return: an already-started :class:`WavefrontSpan` instance.
        :rtype: WavefrontSpan
        """
        parents = []
        follows = []
        baggage = {}
        tags = list(tags.items()) if isinstance(tags, dict) else tags
        tags = tags or []
        span_tag_keys = {span_tag[0] for span_tag in tags}
        for tag in self._tags:
            if not (tag[0] in span_tag_keys and
                    tag[0] in self.single_valued_tag_keys):
                tags.append(tag)
        start_time = start_time or time.time()

        parent = None
        if child_of is not None:
            parent = child_of
            # allow both Span and SpanContext to be passed as child_of
            if isinstance(parent, WavefrontSpan):
                parent = child_of.context
            parents.append(parent.get_span_id())
        # references filed will be omitted if child_of field is not None
        elif parent is None and references:
            # allow both single Reference and list of Reference to be passed
            if not isinstance(references, list):
                references = [references]
            for reference in references:
                if isinstance(reference, opentracing.Reference):
                    reference_ctx = reference.referenced_context
                    # allow both Span and SpanContext to be passed as reference
                    if isinstance(reference_ctx, WavefrontSpan):
                        reference_ctx = reference_ctx.context
                    if parent is None:
                        parent = reference_ctx
                    if reference.type == opentracing.ReferenceType.CHILD_OF:
                        parents.append(reference_ctx.get_span_id())
                        baggage.update(reference_ctx.baggage)
                    elif (reference.type ==
                          opentracing.ReferenceType.FOLLOWS_FROM):
                        follows.append(reference_ctx.get_span_id())
                        baggage.update(reference_ctx.baggage)
        if parent is None or not parent.has_trace:
            if not ignore_active_span and self.active_span is not None:
                parents.append(self.active_span.span_id)
                trace_id = self.active_span.trace_id
                span_id = uuid.uuid1()
            else:
                trace_id = uuid.uuid1()
                span_id = trace_id
        else:
            trace_id = parent.trace_id
            span_id = uuid.uuid1()
        if parent and parent.baggage:
            baggage.update(dict(parent.baggage))
        sampling = None if parent is None else parent.get_sampling_decision()
        span_ctx = WavefrontSpanContext(trace_id, span_id, baggage, sampling)
        if not span_ctx.is_sampled():
            # this indicates a root span and that no decision has been
            # inherited from a parent span. perform head based sampling as no
            # sampling decision has been obtained for this span yet.
            decision = self.sample(operation_name,
                                   get_least_significant_bits(trace_id),
                                   0)
            span_ctx = span_ctx.with_sampling_decision(decision)
        return WavefrontSpan(self, operation_name, span_ctx, start_time,
                             parents, follows, tags)

    # pylint: disable=too-many-arguments
    def start_active_span(self, operation_name, child_of=None, references=None,
                          tags=None, start_time=None, ignore_active_span=False,
                          finish_on_close=True):
        r"""Return a newly started and activated :class:`Scope`.

        :param operation_name: Operation Name
        :type operation_name: str
        :param child_of: Parent Span
        :type child_of: WavefrontSpanContext or WavefrontSpan
        :param references: (optional) references that identify one or more
            parent :class:`SpanContext`\ s. (See the Reference documentation
            for detail).
        :type references: `list` of `opentracing.Reference`
        :param tags: optional span tags (either list of (tag_key, tag_value)
            pairs or a dictionary).
        :type tags: dict or list of pairs
        :param start_time: an explicit Span start time as a unix timestamp per
            :meth:`time.time()`
        :type start_time: float
        :param ignore_active_span: an explicit flag that ignores the current
            active :class:`Scope` and creates a root :class:`Span`.
        :type ignore_active_span: bool
        :param finish_on_close:
        :type finish_on_close:
        :return: a :class:`Scope`, already registered via the
            :class:`ScopeManager`.
        :rtype: opentracing.Scope
        """
        return self.scope_manager.activate(self.start_span(operation_name,
                                                           child_of,
                                                           references,
                                                           tags,
                                                           start_time,
                                                           ignore_active_span),
                                           finish_on_close)

    # pylint: disable=redefined-builtin
    def inject(self, span_context, format, carrier):
        """Inject `span_context` into `carrier`.

        The type of `carrier` is determined by `format`. See the
        :class:`Format` class/namespace for the built-in OpenTracing formats.

        Implementations *must* raise :exc:`UnsupportedFormatException` if
        `format` is unknown or disallowed.

        :param span_context: the :class:`SpanContext` instance to inject
        :type span_context: SpanContext

        :param format: a python object instance that represents a
            given carrier format. `format` may be of any type, and
            `format` equality is defined by python ``==`` equality.
        :type format: Format
        :param carrier: the format-specific carrier object to inject into
        """
        propagator = self.registry.get(format)
        if not propagator:
            raise opentracing.UnsupportedFormatException(
                'Invalid format ' + str(format))
        if isinstance(span_context, WavefrontSpan):
            # be flexible and allow Span as argument, not only SpanContext
            span_context = span_context.context
        if not isinstance(span_context, WavefrontSpanContext):
            raise TypeError(
                'Expecting WavefrontSpanContext, not ' + type(span_context))
        propagator.inject(span_context, carrier)

    # pylint: disable=redefined-builtin
    def extract(self, format, carrier):
        """Return a :class:`SpanContext` instance extracted from a `carrier`.

        :param format: a python object instance that represents a
            given carrier format. `format` may be of any type, and
            `format` equality is defined by python ``==`` equality.
        :type format: opentracing.Format
        :param carrier: the format-specific carrier object to extract from
        :type carrier: dict
        :return: a :class:`SpanContext` extracted from `carrier` or ``None`` if
            no such :class:`SpanContext` could be found.
        :rtype: SpanContext
        """
        propagator = self.registry.get(format)
        if not propagator:
            raise opentracing.UnsupportedFormatException(
                'Invalid format ' + str(format))
        return propagator.extract(carrier)

    def close(self):
        """Close the reporter to close the tracer."""
        self._reporter.close()
        if self.wf_internal_reporter is not None:
            self.wf_internal_reporter.stop()
        if self.wf_derived_reporter is not None:
            self.wf_derived_reporter.stop()
        if self.heartbeater_service is not None:
            self.heartbeater_service.close()

    def report_span(self, span):
        """Report span through the reporter."""
        self._reporter.report(span)

    def sample(self, operation_name, trace_id, duration):
        """Return the decision of sampling."""
        if not self._samplers:
            return True
        early_sampling = duration == 0
        for sampler in self._samplers:
            if not isinstance(sampler, Sampler):
                continue
            do_sample = early_sampling == sampler.is_early()
            if do_sample and sampler.sample(
                    operation_name,
                    get_least_significant_bits(trace_id),
                    duration):
                if LOGGER.isEnabledFor(logging.DEBUG):
                    LOGGER.debug('%s=true op=%s', sampler.__class__.__name__,
                                 operation_name)
                return True
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug('%s=false op=%s', sampler.__class__.__name__,
                             operation_name)
        return False

    def report_wavefront_generated_data(self, span):
        """Report Wavefront generated data from spans."""
        if self.wf_derived_reporter is None:
            # WavefrontSpanReporter not set, so no tracing spans will be
            # reported as metrics/histograms.
            return
        # Need to sanitize metric name as application, service and operation
        # names can have spaces and other invalid metric name characters.
        point_tags = {}
        span_tags = span.get_tags_as_map()

        if self.red_metrics_custom_tag_keys:
            for key in self.red_metrics_custom_tag_keys:
                if key in span_tags:
                    point_tags.update({key: span_tags.get(key)[0]})
        # Set default value of span.kind tag.
        point_tags.setdefault(SPAN_KIND, constants.NULL_TAG_VAL)

        for key in self.single_valued_tag_keys:
            if key in span_tags:
                point_tags.update({key: span_tags.get(key)[0]})
        point_tags.update({COMPONENT: span_tags.get(COMPONENT)[0]})

        # Propagate http status if the span has error.
        if HTTP_STATUS_CODE in span_tags:
            point_tags.update(
                {HTTP_STATUS_CODE: span_tags.get(HTTP_STATUS_CODE)[0]})

        if self.heartbeater_service:
            self.heartbeater_service.report_custom_tags(point_tags)

        # Add operation tag after sending RED heartbeat.
        point_tags.update({self.OPERATION_NAME_TAG: span.get_operation_name()})
        application_service_prefix = (
            'tracing.derived.{}.{}.'.format(
                span_tags.get(constants.APPLICATION_TAG_KEY)[0],
                span_tags.get(constants.SERVICE_TAG_KEY)[0]))

        if span.is_error():
            delta.delta_counter(self.wf_derived_reporter.registry,
                                self.sanitize(application_service_prefix +
                                              span.get_operation_name() +
                                              self.ERROR_SUFFIX),
                                point_tags).inc()

        delta.delta_counter(self.wf_derived_reporter.registry,
                            self.sanitize(application_service_prefix +
                                          span.get_operation_name() +
                                          self.INVOCATION_SUFFIX),
                            point_tags).inc()
        # Convert from secs to millis and add to duration counter.
        span_duration_millis = span.get_duration_time() * 1000
        delta.delta_counter(self.wf_derived_reporter.registry,
                            self.sanitize(application_service_prefix +
                                          span.get_operation_name() +
                                          self.TOTAL_TIME_SUFFIX),
                            point_tags).inc(span_duration_millis)
        # Convert from millis to micros and add to histogram.
        span_duration_micros = span_duration_millis * 1000
        if span.is_error():
            error_point_tags = dict(point_tags)
            error_point_tags.update({'error': 'true'})
            wavefront_histogram.wavefront_histogram(
                self.wf_derived_reporter.registry,
                self.sanitize(application_service_prefix +
                              span.get_operation_name() +
                              self.DURATION_SUFFIX),
                error_point_tags).add(span_duration_micros)
        else:
            wavefront_histogram.wavefront_histogram(
                self.wf_derived_reporter.registry,
                self.sanitize(application_service_prefix +
                              span.get_operation_name() +
                              self.DURATION_SUFFIX),
                point_tags).add(span_duration_micros)

    # pylint: disable=invalid-name
    def instantiate_wavefront_stats_reporter(self, wf_span_reporter,
                                             application_tags):
        """Instantiate WavefrontReporter and Heartbeater Service."""
        # pylint: disable=fixme
        # TODO: this helper method should go in Tier 1 SDK
        wf_internal_reporter = wavefront_reporter.WavefrontReporter(
            prefix="~sdk.python.opentracing.",
            source=wf_span_reporter.source,
            registry=tagged_registry.TaggedRegistry(),
            reporting_interval=60,
            tags=dict(application_tags.get_as_list())
        ).report_minute_distribution()
        wf_internal_reporter.wavefront_client = (
            wf_span_reporter.get_wavefront_sender())
        wf_internal_reporter.start()

        wf_derived_reporter = wavefront_reporter.WavefrontReporter(
            source=wf_span_reporter.source,
            registry=tagged_registry.TaggedRegistry(),
            reporting_interval=self.report_frequency_millis / 1000,
            tags=dict(application_tags.get_as_list())
        ).report_minute_distribution()
        wf_derived_reporter.wavefront_client = (
            wf_span_reporter.get_wavefront_sender())
        wf_derived_reporter.start()

        heartbeater_service = wavefront_sdk.common.HeartbeaterService(
            wavefront_client=wf_span_reporter.get_wavefront_sender(),
            application_tags=application_tags,
            components=[self.WAVEFRONT_GENERATED_COMPONENT,
                        self.OPENTRACING_COMPONENT,
                        self.PYTHON_COMPONENT],
            source=wf_span_reporter.source)
        return wf_internal_reporter, wf_derived_reporter, heartbeater_service

    @staticmethod
    def get_wavefront_span_reporter(reporter):
        """Get WavefrontSpanReporter from a given reporter."""
        if isinstance(reporter, WavefrontSpanReporter):
            return reporter
        if isinstance(reporter, CompositeReporter):
            for item in reporter.get_reporters():
                if isinstance(item, WavefrontSpanReporter):
                    return item
        return None

    @staticmethod
    def sanitize(string):
        """Sanitize a string, replace whitespace with "-".

        @param string: Input string
        @return: Sanitized string
        """
        whitespace_sanitized = re.sub(r'[\s]+', '-', string)
        if '"' in whitespace_sanitized:
            return re.sub(r'[\"]+', '\\\\\"', whitespace_sanitized)
        return whitespace_sanitized


def get_least_significant_bits(uuid_val):
    """Equivalent to getLeastSignificantBits() in Java."""
    lsb_s = ''.join(str(uuid_val).split('-')[-2:])
    lsb = int(lsb_s, 16)
    if int(lsb_s[0], 16) > 7:
        lsb = lsb - 0x10000000000000000
    return lsb


def get_most_significant_bits(uuid_val):
    """Equivalent to getMostSignificantBits() in Java."""
    msb_s = ''.join(str(uuid_val).split('-')[:3])
    msb = int(msb_s, 16)
    if int(msb_s[0], 16) > 7:
        msb = msb - 0x10000000000000000
    return msb
