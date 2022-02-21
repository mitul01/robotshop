"""Propagator Registry.

@author: Hao Song (songhao@vmware.com)
"""

import opentracing

from . import http
from . import textmap


class PropagatorRegistry:
    """Registry of available propagators."""

    def __init__(self):
        """Construct propagator registry."""
        self.propagators = {
            opentracing.propagation.Format.TEXT_MAP:
                textmap.TextMapPropagator(),
            opentracing.propagation.Format.HTTP_HEADERS:
                http.HTTPPropagator()}

    # pylint: disable=redefined-builtin
    def get(self, format):
        """
        Get propagator of certain format.

        :param format: Format of propagator.
        :type format: opentracing.propagation.Format
        :return: Propagator of given format
        :rtype: wavefront_opentracing_sdk.propagation.Propagator
        """
        return self.propagators.get(format)

    # pylint: disable=redefined-builtin
    def register(self, format, propagator):
        """
        Register propagator.

        :param format: Format of propagator.
        :type format: opentracing.propagation.Format
        :param propagator: Propagator to be registered.
        :type propagator: Propagator
        """
        self.propagators.update({format: propagator})
