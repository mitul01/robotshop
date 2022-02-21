"""Abstract Class of Sampler.

@author: Hao Song (songhao@vmware.com)
"""


class Sampler:
    """Abstract tracing span sampler."""

    def sample(self, operation_name, trace_id, duration):
        """
        Check if a span should be allowed given its operation and trace id.

        :param operation_name: The operation name of the span.
        :param trace_id: The trace_id of the span.
        :param duration: The duration of the span in milliseconds.
        :return: True if the span should be allowed, False otherwise.
        """
        raise NotImplementedError

    def is_early(self):
        """
        Whether this sampler performs early or head based sampling.

        Offers a non-binding hint for clients using the sampler.

        :return: True for early sampling, False otherwise
        """
        raise NotImplementedError
