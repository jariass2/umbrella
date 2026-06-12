"""
Wrappers de herramientas de búsqueda con monitorización en terminal.
"""

import json

from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.pubmed import PubmedTools

from tools.monitor import monitor_search, monitor_search_result


class MonitoredDuckDuckGoTools(DuckDuckGoTools):
    """DuckDuckGoTools con logging de monitorización."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_count = 0

    def web_search(self, query: str, max_results: int = 5) -> str:
        self.call_count += 1
        monitor_search("DuckDuckGo", query)
        result = super().web_search(query, max_results)
        try:
            n = len(json.loads(result))
        except Exception:
            n = 0
        monitor_search_result("DuckDuckGo", n)
        return result

    def search_news(self, query: str, max_results: int = 5) -> str:
        self.call_count += 1
        monitor_search("DuckDuckGo/News", query)
        result = super().search_news(query, max_results)
        try:
            n = len(json.loads(result))
        except Exception:
            n = 0
        monitor_search_result("DuckDuckGo/News", n)
        return result


class MonitoredPubmedTools(PubmedTools):
    """PubmedTools con logging de monitorización."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_count = 0

    def search_pubmed(self, query: str, max_results=10) -> str:
        self.call_count += 1
        monitor_search("PubMed", query)
        result = super().search_pubmed(query, max_results)
        try:
            n = len(json.loads(result))
        except Exception:
            n = 0
        monitor_search_result("PubMed", n)
        return result
