"""Duration Sampler.

Sampler that allows spans above a given duration in milliseconds to be
reported.

@author: Hao Song (songhao@vmware.com)
"""

from . import sampler


class DurationSampler(sampler.Sampler):
    """Tracing span duration sampler."""

    def __init__(self, duration):
        """Set up duration sampler."""
        self._duration = None
        self.set_duration(duration)

    def sample(self, operation_name, trace_id, duration):
        """Perform sampling."""
        return duration > self._duration

    def is_early(self):
        """Return False."""
        return False

    def set_duration(self, duration):
        """Set the duration for this sampler."""
        self._duration = duration
