"""Composite Reporter.

@author: Hao Song (songhao@vmware.com)
"""
from __future__ import absolute_import

from . import reporter


class CompositeReporter(reporter.Reporter):
    """Composite Reporter.

    Used to create multiple reporters, such as create a console
    reporter and Wavefront direct reporter at the same time.
    """

    def __init__(self, *reporters):
        """Construct composite reporter.

        :param reporters: Reporters of composite reporter
        :type reporters: Reporter
        """
        super().__init__()
        self.reporters = reporters

    def report(self, wavefront_span):
        """Each reporter report data.

        :param wavefront_span: Wavefront span to be reported
        """
        for rep in self.reporters:
            rep.report(wavefront_span)

    def get_failure_count(self):
        """Total failure count of all reporters.

        :return: Total failure count
        :rtype: int
        """
        res = 0
        for rep in self.reporters:
            res += rep.get_failure_count()
        return res

    def close(self):
        """Close all reporters inside the composite reporter."""
        for rep in self.reporters:
            rep.close()

    def get_reporters(self):
        """Return a copy so that original list is not modified."""
        return list(self.reporters)
