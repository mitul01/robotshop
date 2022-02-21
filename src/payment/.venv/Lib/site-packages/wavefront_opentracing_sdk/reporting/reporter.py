"""
Abstract Class of Reporter.

@author: Hao Song (songhao@vmware.com)
"""


class Reporter:
    """Tracing span data reporter."""

    def __init__(self, source=None):
        """
        Construct reporter.

        :param source: Source of the reporter
        :type source: str
        """
        self.source = source

    def report(self, wavefront_span):
        """
        Report tracing span.

        :param wavefront_span: Wavefront span to be reported
        :type wavefront_span: wavefront_opentracing_python_sdk.WavefrontSpan
        """
        raise NotImplementedError

    def get_failure_count(self):
        """
        Get failure count of the reporter.

        :return: Failure count
        :rtype: int
        """
        raise NotImplementedError

    def close(self):
        """Close the reporter."""
        raise NotImplementedError
