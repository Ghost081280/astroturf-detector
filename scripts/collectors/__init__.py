"""Collectors package"""

from .job_collector import JobCollector
from .fec_collector import FECCollector
from .nonprofit_collector import NonprofitCollector
from .news_collector import NewsCollector
from .ddg_collector import DuckDuckGoCollector
from .campaign_finance_collector import CampaignFinanceCollector
from .propublica_collector import ProPublicaCollector

__all__ = [
    'JobCollector',
    'FECCollector',
    'NonprofitCollector',
    'NewsCollector',
    'DuckDuckGoCollector',
    'CampaignFinanceCollector',
    'ProPublicaCollector'
]
