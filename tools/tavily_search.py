"""
Tavily search tool compatible con agno.framework (mismo patrón que DuckDuckGoTools/WebSearchTools).
Se usa como alternativa cuando DuckDuckGo no devuelve resultados.
"""

from __future__ import annotations

import json
import logging
import os

from agno.tools import Toolkit
from tools.monitor import monitor_search, monitor_search_result

log = logging.getLogger(__name__)


def _get_api_key() -> str:
    key = os.getenv("TAVILY_API_KEY", "")
    if not key:
        raise ValueError(
            "TAVILY_API_KEY no está definida. Añádela al .env o a las variables de entorno."
        )
    return key


# Optional specific exception classes from tavily-python — fall back to a
# tuple containing only Exception when the package version doesn't expose
# them, so the code keeps working regardless of upstream churn.
try:
    from tavily.errors import (  # type: ignore
        UsageLimitExceededError,
        InvalidAPIKeyError,
        MissingAPIKeyError,
    )
    _AUTH_ERRORS = (InvalidAPIKeyError, MissingAPIKeyError)
    _QUOTA_ERRORS = (UsageLimitExceededError,)
except Exception:  # pragma: no cover — older / restructured tavily
    _AUTH_ERRORS = ()
    _QUOTA_ERRORS = ()


class TavilySearchTools(Toolkit):
    """Toolkit de búsqueda web via Tavily API.

    Compatible con agno.Agent — mismo interfaz que WebSearchTools.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or _get_api_key()
        from tavily import TavilyClient
        self._client = TavilyClient(api_key=self.api_key)
        self.call_count = 0
        super().__init__(name="tavily_search", tools=[self.web_search, self.search_news])

    # Max chars per result content — keeps context lean without losing key facts
    _MAX_CONTENT = 600

    def _format(self, results: list, max_results: int) -> str:
        """Return compact JSON keeping only title, url and content (truncated)."""
        slim = [
            {
                "title":   r.get("title", ""),
                "url":     r.get("url", ""),
                "content": (r.get("content") or "")[:self._MAX_CONTENT],
            }
            for r in results[:max_results]
            if r.get("title") or r.get("content")
        ]
        return json.dumps(slim, ensure_ascii=False)

    def _safe_search(self, label: str, **kwargs) -> dict | None:
        """Wrap Tavily client call; log and downgrade errors to None."""
        try:
            return self._client.search(**kwargs)
        except _AUTH_ERRORS as e:
            log.error("[%s] Tavily auth error: %s", label, e)
        except _QUOTA_ERRORS as e:
            log.warning("[%s] Tavily quota exceeded: %s", label, e)
        except Exception as e:  # network, timeout, malformed response
            log.warning("[%s] Tavily search failed (%s): %s", label, type(e).__name__, e)
        return None

    def web_search(self, query: str, max_results: int = 3) -> str:
        """Use this function to search the web for a query.

        Args:
            query: The query to search for.
            max_results: The maximum number of results to return.
        """
        self.call_count += 1
        monitor_search("Tavily", query)
        results = self._safe_search("Tavily", query=query, max_results=max_results)

        if not results or not results.get("results"):
            monitor_search_result("Tavily", 0)
            return json.dumps([])

        n = len(results["results"][:max_results])
        monitor_search_result("Tavily", n)
        return self._format(results["results"], max_results)

    def search_news(self, query: str, max_results: int = 3) -> str:
        """Use this function to get the latest news from the web.

        Args:
            query: The query to search for.
            max_results: The maximum number of results to return.
        """
        self.call_count += 1
        monitor_search("Tavily/News", query)
        results = self._safe_search(
            "Tavily/News", query=query, max_results=max_results, topic="news"
        )

        if not results or not results.get("results"):
            monitor_search_result("Tavily/News", 0)
            return json.dumps([])

        n = len(results["results"][:max_results])
        monitor_search_result("Tavily/News", n)
        return self._format(results["results"], max_results)
