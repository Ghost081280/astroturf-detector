"""Collectors package - Data collection modules for Astroturf Detector"""

from .job_collector import JobCollector
from .fec_collector import FECCollector
from .nonprofit_collector import NonprofitCollector
from .news_collector import NewsCollector
from .ddg_collector import DuckDuckGoCollector

__all__ = ['JobCollector', 'FECCollector', 'NonprofitCollector', 'NewsCollector', 'DuckDuckGoCollector']
