"""Wavefront Span Reporter.

@author: Hao Song (songhao@vmware.com)
"""
import logging
try:
    from queue import Queue, Full, Empty
except ImportError:
    from Queue import Queue, Full, Empty
import random
import socket
import threading

from pyformance import meters

from wavefront_sdk.common.utils import get_sem_ver

from . import reporter


# pylint: disable=too-many-instance-attributes
class WavefrontSpanReporter(reporter.Reporter):
    """Wavefront Span Reporter."""

    def __init__(self, client, source=None, max_queue_size=50000,
                 log_percent=0.1):
        """Construct Wavefront Span Reporter.

        :param client: Wavefront Client
        :type client: WavefrontProxyClient or WavefrontDirectClient
        :param source: Source of the reporter
        :type source: str
        :param max_queue_size: Max queue size of in-memory buffer. Incoming
        spans are dropped if buffer is full.
        :type max_queue_size: int
        :param log_percent: Set the percent of log messages to be logged.
        Defaults to 10%.
        :type log_percent: float
        :
        """
        self.sender = client
        source = source or socket.gethostname()
        self._stop = False
        self._max_queue_size = max_queue_size
        self._log_percent = log_percent
        self._span_buffer = Queue(maxsize=self._max_queue_size)
        self._metrics_reporter = self._registry = self.span_received = \
            self.spans_dropped = self.report_errors = None
        super().__init__(source)
        self.sending_thread = threading.Thread(target=self.run,
                                               name="wavefront_span_reporter")
        self.sending_thread.setDaemon(True)
        self.sending_thread.start()

    def run(self):
        """Target for span sending thread."""
        while not self._stop:
            try:
                wavefront_span = self._span_buffer.get(True, None)
                self.send(wavefront_span)
            except (AttributeError, TypeError, Empty):
                logging.error('Error processing buffer.')

    def send(self, wavefront_span):
        """Report span data via Wavefront Client.

        :param wavefront_span: Wavefront Span to be reported.
        """
        try:
            self.sender.send_span(
                wavefront_span.get_operation_name(),
                int(wavefront_span.get_start_time() * 1000),
                int(wavefront_span.get_duration_time() * 1000), self.source,
                wavefront_span.trace_id, wavefront_span.span_id,
                wavefront_span.get_parents(), wavefront_span.get_follows(),
                wavefront_span.get_tags(), span_logs=wavefront_span.get_logs())
        except (AttributeError, TypeError):
            if self.report_errors:
                self.report_errors.inc()
            if self.spans_dropped:
                self.spans_dropped.inc()
            if self._logging_allowed():
                logging.error('Error reporting spans.')

    def _logging_allowed(self):
        return random.uniform(0, 1) <= self._log_percent

    def report(self, wavefront_span):
        """Report span data via Wavefront Client.

        :param wavefront_span: Wavefront Span to be reported.
        """
        try:
            if self.span_received:
                self.span_received.inc()
            self._span_buffer.put(wavefront_span)
        except (AttributeError, TypeError, Full):
            if self.spans_dropped:
                self.spans_dropped.inc()
            if self._logging_allowed():
                logging.error('Buffer full, dropping span: %s, %s',
                              wavefront_span.get_operation_name(),
                              wavefront_span.span_id)
                if self.spans_dropped:
                    logging.warning('Total spans dropped: %d',
                                    self.spans_dropped.get_count())

    def set_metrics_reporter(self, wavefront_reporter):
        """Set Wavefront Reporter for internal metrics.

        :param wavefront_reporter: Wavefront Reporter
        """
        self._metrics_reporter = wavefront_reporter
        self._registry = wavefront_reporter.registry
        self._registry.gauge('version', self.CustomGauge(
                lambda: get_sem_ver('wavefront-opentracing-sdk-python')))
        self._registry.gauge("reporter.queue.size",
                             self.CustomGauge(self._span_buffer.qsize))
        self._registry.gauge("reporter.queue.remaining_capacity", self.
                             CustomGauge(self._get_span_buffer_remain_size))
        self.span_received = self._registry.counter("reporter.spans.received")
        self.spans_dropped = self._registry.counter("reporter.spans.dropped")
        self.report_errors = self._registry.counter("reporter.spans.errors")

    def _get_span_buffer_remain_size(self):
        """Calculate remain size of span buffer."""
        return self._max_queue_size - self._span_buffer.qsize()

    def get_failure_count(self):
        """Get failure count from wavefront client.

        :return: Failure count
        :rtype: int
        """
        return self.sender.get_failure_count()

    def close(self):
        """Close the wavefront client."""
        self._stop = True
        self.sending_thread.join(10)
        self.sender.close()

    def get_source(self):
        """Get the source of WavefrontSpanReporter."""
        return self.source

    def get_wavefront_sender(self):
        """Get the Wavefront Sender."""
        return self.sender

    # pylint: disable=too-few-public-methods
    class CustomGauge(meters.Gauge):
        """Custom Gauge for monitoring span buffer queue."""

        def __init__(self, get_val):
            """Construct CustomGauge.

            :param get_val: Method returns a value.
            """
            self.get_val = get_val

        def get_value(self):
            """Get value from input method."""
            return self.get_val()
