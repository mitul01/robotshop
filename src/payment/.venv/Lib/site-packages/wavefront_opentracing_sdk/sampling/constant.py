"""Constant Sampler.

Sampler that allows spans through at a constant rate (all in or all out).

@author: Hao Song (songhao@vmware.com)
"""

from . import sampler


class ConstantSampler(sampler.Sampler):
    """Tracing span constant sampler."""

    def __init__(self, decision):
        """Set up constant sampler's attributes."""
        self._decision = decision
        self.set_decision(decision)

    def sample(self, operation_name, trace_id, duration):
        """Do the sampling."""
        return self._decision

    def is_early(self):
        """Return True."""
        return True

    def set_decision(self, decision):
        """Set the decision for this sampler."""
        self._decision = decision
