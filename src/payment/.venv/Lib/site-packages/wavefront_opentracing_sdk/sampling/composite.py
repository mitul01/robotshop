"""Composite Sampler.

Sampler that delegates to multiple other samplers for sampling.

The sampling decision is true if any of the delegate samplers allow the span.

@author: Hao Song (songhao@vmware.com)
"""

from . import sampler


class CompositeSampler(sampler.Sampler):
    """Tracing span composite sampler."""

    def __init__(self, samplers):
        """Set up samplers."""
        self.samplers = samplers

    def sample(self, operation_name, trace_id, duration):
        """Perform sampling for every sampler."""
        if not self.samplers:
            return True
        for a_sampler in self.samplers:
            if isinstance(a_sampler, sampler.Sampler):
                if a_sampler.sample(operation_name, trace_id, duration):
                    return True
        return False

    def is_early(self):
        """Return False."""
        return False
