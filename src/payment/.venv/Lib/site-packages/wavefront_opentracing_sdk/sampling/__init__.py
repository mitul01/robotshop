"""Sampling Module.

@author: Hao Song (songhao@vmware.com)
"""
from .composite import CompositeSampler
from .constant import ConstantSampler
from .duration import DurationSampler
from .rate import RateSampler


__all__ = ['CompositeSampler',
           'ConstantSampler',
           'DurationSampler',
           'RateSampler']
