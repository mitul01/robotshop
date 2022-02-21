"""Wavefront Span.

@author: Hao Song (songhao@vmware.com)
"""
import numbers
import threading
import time

import opentracing
import opentracing.ext.tags

import wavefront_sdk.common.utils
from wavefront_sdk.entities.tracing import span_log


# pylint: disable=too-many-instance-attributes
class WavefrontSpan(opentracing.Span):
    """Wavefront Span."""

    # pylint: disable=too-many-arguments
    def __init__(self, tracer, operation_name, context, start_time, parents,
                 follows, tags):
        """Construct Wavefront Span.

        :param tracer: Tracer that create this span
        :type tracer: wavefront_opentracing_python_sdk.WavefrontTracer
        :param operation_name: Operation Name
        :type operation_name: str
        :param context: Span Context
        :type context: wavefront_opentracing_python_sdk.WavefrontSpanContext
        :param start_time: an explicit Span start time as a unix timestamp per
            :meth:`time.time()`
        :type start_time: float
        :param parents: List of UUIDs of parents span
        :type parents: list of uuid.UUID
        :param follows: List of UUIDs of follows span
        :type follows: list of uuid.UUID
        :param tags: Tags of the span
        :type tags: list of tuple
        """
        super().__init__(tracer=tracer, context=context)
        self._context = context
        self.operation_name = operation_name
        self.start_time = start_time
        self.duration_time = 0
        self.parents = parents
        self.follows = follows
        self._finished = False
        self._is_error = False
        self._force_sampling = None
        self.update_lock = threading.Lock()
        self.tags = []
        self.logs = []
        for tag in tags:
            if isinstance(tag, tuple):
                self.set_tag(tag[0], tag[1])
        if opentracing.ext.tags.COMPONENT not in self.tags:
            self.set_tag(opentracing.ext.tags.COMPONENT, "none")
        self._spans_discarded = None if tracer.wf_internal_reporter is None \
            else tracer.wf_internal_reporter.registry.\
            counter("spans.discarded")

    @property
    def context(self):
        """Get WavefrontSpanContext of WavefrontSpan.

        :return: Span context of current span.
        :rtype: wavefront_opentracing_python_sdk.WavefrontSpanContext
        """
        return self._context

    def set_tag(self, key, value):
        """Set tag of span.

        :param key: key of the tag
        :type key: str
        :param value: value of the tag
        :type value: str
        :return: span itself
        :rtype: WavefrontSpan
        """
        with self.update_lock:
            if not wavefront_sdk.common.utils.is_blank(key) and value:
                self.tags.append((key, str(value)))
                # allow span to be reported if sampling.priority is > 0.
                if (key is opentracing.ext.tags.SAMPLING_PRIORITY
                        and isinstance(value, numbers.Number)):
                    self._force_sampling = value > 0
                    self._context = self._context.with_sampling_decision(
                        self._force_sampling)
                # allow span to be reported if debug is set to true.
                if (not self._force_sampling
                        and key == "debug"
                        and str(value).lower() == "true"):
                    force_sampling = True
                    self._context = self._context.with_sampling_decision(
                        force_sampling)
                if key is opentracing.ext.tags.ERROR:
                    self._is_error = True
                # allow span to be reported if error tag is set.
                if (not self._force_sampling
                        and key is opentracing.ext.tags.ERROR
                        and isinstance(value, bool)):
                    force_sampling = True
                    self._context = self._context.with_sampling_decision(
                        force_sampling)
        return self

    def log_kv(self, key_values, timestamp=None):
        """Add a log record to the span.

        :param key_values: A dict of string keys and values of any type can be
        transferred to string by str()
        :type key_values: dict
        :param timestamp: A unix timestamp per :meth:`time.time()`; current
            time if ``None``
        :type timestamp: float
        :return: span itself
        :rtype: WavefrontSpan
        """
        if key_values:
            fields = {k: str(v) for k, v in key_values.items()}
            with self.update_lock:
                self.logs.append(span_log.SpanLog(
                    timestamp=timestamp or int(time.time() * 1E6),
                    fields=fields))

    def set_baggage_item(self, key, value):
        """Replace span context with the updated dict of baggage.

        :param key: key of the baggage item
        :type key: str
        :param value: value of the baggage item
        :type value: str
        :return: span itself
        :rtype: WavefrontSpan
        """
        new_context = self._context.with_baggage_item(key=key, value=value)
        with self.update_lock:
            self._context = new_context
        return self

    def get_baggage_item(self, key):
        """Get baggage item with given key.

        :param key: Key of baggage item
        :type key: str
        :return: Baggage item value
        :rtype: str
        """
        return self._context.get_baggage_item(key)

    def set_operation_name(self, operation_name):
        """Update operation name.

        :param operation_name: Operation Name
        :type operation_name: str
        :return: Span itself
        :rtype: WavefrontSpan
        """
        with self.update_lock:
            self.operation_name = operation_name
        return self

    def finish(self, finish_time=None):
        """Call finish to finish current span, and report it.

        :param finish_time: Finish time, unix timestamp
        :type finish_time: float
        """
        if finish_time:
            self._do_finish(finish_time - self.start_time)
        else:
            self._do_finish(time.time() - self.start_time)

    def _do_finish(self, duration_time):
        """Mark span as finished and send it via reporter.

        :param duration_time: Duration time in seconds
        :type duration_time: float
        """
        with self.update_lock:
            if self._finished:
                return
            self.duration_time = duration_time
            self._finished = True
        # perform another sampling for duration based samplers
        if not self._force_sampling and (
                not self._context.is_sampled() or
                not self._context.get_sampling_decision()):
            if self.tracer.sample(
                    self.operation_name,
                    self.trace_id,
                    duration_time):
                self._context = self._context.with_sampling_decision(True)

        # only report spans if the sampling decision allows it
        if (self._context.is_sampled()
                and self._context.get_sampling_decision()):
            self.tracer.report_span(self)
        elif self._spans_discarded:
            self._spans_discarded.inc()
        # irrespective of sampling, report wavefront-generated
        # metrics/histograms to Wavefront
        self.tracer.report_wavefront_generated_data(self)

    @property
    def trace_id(self):
        """Get trace id.

        :return: Trace id
        :rtype: uuid.UUID
        """
        return self._context.trace_id

    @property
    def span_id(self):
        """Get span id.

        :return: Span id
        :rtype: uuid.UUID
        """
        return self._context.span_id

    def get_operation_name(self):
        """Get operation name.

        :return: Operation name.
        :rtype: str
        """
        return self.operation_name

    def get_start_time(self):
        """Get span start time.

        :return: Span start time, unix timestamp.
        :rtype: float
        """
        return self.start_time

    def get_duration_time(self):
        """Get span duration time.

        :return: Span duration time in seconds.
        :rtype: float
        """
        return self.duration_time

    def get_parents(self):
        """Get list of parents span's id.

        :return: list of parents span's id
        :rtype: list of uuid.UUID
        """
        if not self.parents:
            return []
        return self.parents

    def get_follows(self):
        """Get list of follows span's id.

        :return: list of follows span's id
        :rtype: list of uuid.UUID
        """
        if not self.follows:
            return []
        return self.follows

    def get_tags(self):
        """Get tags of span.

        :return: list of tags
        :rtype: list of pair
        """
        if not self.tags:
            return []
        return self.tags

    def get_logs(self):
        """Get logs of span.

        :return: list of SpanLog
        :rtype: list of SpanLog
        """
        return self.logs or []

    def get_tags_as_list(self):
        """Get tags in list format.

        :return: list of tags
        :rtype: list of pair
        """
        return self.get_tags()

    def get_tags_as_map(self):
        """Get tags in map format.

        :return: tags in map format: {key: [list_of_val]}
        :rtype: dict of {str : list}
        """
        if not self.tags:
            return {}
        tag_map = {}
        for key, val in self.tags:
            if key not in tag_map:
                tag_map[key] = [val]
            else:
                tag_map[key].append(val)
        return tag_map

    def is_error(self):
        """Get if the span is error or not."""
        return self._is_error
