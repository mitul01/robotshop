"""
HTTP Propagator.

@author: Hao Song (songhao@vmware.com)
"""
from wavefront_opentracing_sdk.propagation import textmap


class HTTPPropagator(textmap.TextMapPropagator):
    """HTTP Propagator."""
