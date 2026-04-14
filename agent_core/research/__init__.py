"""Research module for MA Agent - external data gathering."""
from __future__ import annotations

from agent_core.research.tavily_client import TavilyClient, tavily_search
from agent_core.research.camoufox_client import CamoufoxClient, camoufox_search
from agent_core.research.strategy_researcher import StrategyResearcher, research_for_strategy

__all__ = [
    "TavilyClient",
    "tavily_search",
    "CamoufoxClient",
    "camoufox_search",
    "StrategyResearcher",
    "research_for_strategy",
]
