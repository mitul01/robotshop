"""Console Reporter.

@author: Hao Song (songhao@vmware.com)
"""
from __future__ import print_function

import logging

import wavefront_sdk.common.utils

from ..reporting import reporter

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class ConsoleReporter(reporter.Reporter):
    """Console Reporter.

    Used for print span data to console.
    """

    def report(self, wavefront_span):
        """Print span data to console.

        :param wavefront_span: Wavefront span to be reported
        """
        line_data = wavefront_sdk.common.utils.tracing_span_to_line_data(
            wavefront_span.get_operation_name(),
            int(wavefront_span.get_start_time() * 1000),
            int(wavefront_span.get_duration_time() * 1000),
            self.source, wavefront_span.trace_id, wavefront_span.span_id,
            wavefront_span.get_parents(), wavefront_span.get_follows(),
            wavefront_span.get_tags(), span_logs=wavefront_span.get_logs(),
            default_source='unknown')
        LOGGER.info('Finished span: sampling=%s %s',
                    wavefront_span.context.get_sampling_decision(),
                    line_data)
        if wavefront_span.get_logs():
            span_log_data = wavefront_sdk.common.utils.span_log_to_line_data(
                wavefront_span.trace_id, wavefront_span.span_id,
                wavefront_span.get_logs())
            LOGGER.info('Span Log: %s', span_log_data)

    def get_failure_count(self):
        """No-op."""
        return 0

    def close(self):
        """No-op."""
        return
