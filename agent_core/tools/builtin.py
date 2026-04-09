"""Built-in tools registration for MA Agent"""
from __future__ import annotations

from agent_core.models import ToolSpec
from agent_core.tools.strategy_iq import (
    strategy_parse_executor,
    strategy_generate_executor,
)
from agent_core.tools.match_ai import (
    kol_search_executor,
    kol_combo_executor,
    kol_analyze_executor,
)
from agent_core.tools.connect_bot import (
    outreach_generate_executor,
    follow_up_generate_executor,
    negotiation_advice_executor,
    contract_clauses_executor,
)
from agent_core.tools.creative_pilot import (
    creative_brief_executor,
    content_template_executor,
    content_review_executor,
)

BUILTIN_TOOLS: list[ToolSpec] = [
    # StrategyIQ Tools
    ToolSpec(
        name="StrategyParseTool",
        responsibility="Parse client brief to extract key information",
        input_schema={"brief": "string"},
        executor=strategy_parse_executor,
    ),
    ToolSpec(
        name="StrategyGenerateTool",
        responsibility="Generate marketing strategy based on parsed brief",
        input_schema={"brief_data": "object", "skills": "array"},
        executor=strategy_generate_executor,
    ),
    
    # MatchAI Tools
    ToolSpec(
        name="KOLSearchTool",
        responsibility="Search and filter KOLs based on criteria",
        input_schema={
            "platform": "string",
            "category": "string",
            "min_followers": "string",
            "max_followers": "string",
            "min_engagement": "number",
            "city": "string",
            "limit": "number",
        },
        executor=kol_search_executor,
    ),
    ToolSpec(
        name="KOLComboTool",
        responsibility="Generate optimal KOL combination based on budget",
        input_schema={
            "budget": "number",
            "platforms": "array",
            "category": "string",
            "skills": "array",
        },
        executor=kol_combo_executor,
    ),
    ToolSpec(
        name="KOLAnalyzeTool",
        responsibility="Analyze KOL data quality and risk assessment",
        input_schema={
            "kol_data": "object",
            "target_category": "string",
        },
        executor=kol_analyze_executor,
    ),
    
    # ConnectBot Tools
    ToolSpec(
        name="OutreachGenerateTool",
        responsibility="Generate personalized outreach messages to KOLs",
        input_schema={
            "kol_name": "string",
            "brand": "string",
            "platform": "string",
            "style": "string",
            "content_highlight": "string",
            "cooperation_content": "string",
            "benefits": "string",
            "timeline": "string",
            "skills": "array",
        },
        executor=outreach_generate_executor,
    ),
    ToolSpec(
        name="FollowUpGenerateTool",
        responsibility="Generate follow-up messages for KOL outreach",
        input_schema={
            "kol_name": "string",
            "brand": "string",
            "days_since": "number",
            "previous_response": "string",
        },
        executor=follow_up_generate_executor,
    ),
    ToolSpec(
        name="NegotiationAdviceTool",
        responsibility="Provide negotiation tips and counter-offer suggestions",
        input_schema={
            "kol_price": "number",
            "budget": "number",
            "kol_engagement": "number",
            "kol_followers": "number",
        },
        executor=negotiation_advice_executor,
    ),
    ToolSpec(
        name="ContractClausesTool",
        responsibility="Generate recommended contract clauses",
        input_schema={
            "cooperation_type": "string",
        },
        executor=contract_clauses_executor,
    ),
    
    # CreativePilot Tools
    ToolSpec(
        name="CreativeBriefTool",
        responsibility="Generate creative brief for KOL content creation",
        input_schema={
            "brand": "string",
            "product": "string",
            "industry": "string",
            "platform": "string",
            "kol_style": "string",
            "key_messages": "array",
            "must_include": "array",
            "forbidden": "array",
            "skills": "array",
        },
        executor=creative_brief_executor,
    ),
    ToolSpec(
        name="ContentTemplateTool",
        responsibility="Generate content templates for different platforms",
        input_schema={
            "template_type": "string",
            "platform": "string",
            "brand": "string",
            "product": "string",
        },
        executor=content_template_executor,
    ),
    ToolSpec(
        name="ContentReviewTool",
        responsibility="Review content for compliance and brand alignment",
        input_schema={
            "content": "string",
            "brand": "string",
            "platform": "string",
            "requirements": "object",
        },
        executor=content_review_executor,
    ),
]
