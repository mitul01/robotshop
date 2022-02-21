"""Rate Sampler.

Sampler that allows a certain probabilistic rate (between 0.0 and 1.0) of spans
to be reported.

Note: Sampling is performed per trace id. All spans for a sampled trace will be
reported.

@author: Hao Song (songhao@vmware.com)
"""

from . import sampler


class RateSampler(sampler.Sampler):
    """Tracing span rate sampler."""

    MIN_SAMPLING_RATE = 0.0
    MAX_SAMPLING_RATE = 1.0
    MOD_FACTOR = 10000

    def __init__(self, sampling_rate):
        """Set up rate sampler attributes."""
        self._boundary = None
        self.set_sampling_rate(sampling_rate)

    def sample(self, operation_name, trace_id, duration):
        """Perform sampling."""
        return abs(trace_id % self.MOD_FACTOR) <= self._boundary

    def is_early(self):
        """Return True."""
        return True

    def set_sampling_rate(self, sampling_rate):
        """Set the sampling rate for this sampler."""
        if not self.MIN_SAMPLING_RATE < sampling_rate < self.MAX_SAMPLING_RATE:
            raise ValueError('Sampling rate must be between '
                             '{0.MIN_SAMPLING_RATE} and '
                             '{0.MAX_SAMPLING_RATE}'.format(self))
        self._boundary = sampling_rate * self.MOD_FACTOR
