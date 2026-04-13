"""Provider-agnostic marketing workflow orchestrator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_core.tools.strategy_iq import parse_brief, generate_strategy
from agent_core.tools.match_ai import generate_kol_combo_with_llm
from agent_core.tools.connect_bot import generate_outreach_with_llm
from agent_core.tools.creative_pilot import generate_creative_brief_with_llm
from agent_core.tools.user_research import generate_user_research_with_llm


STAGE_NAMES = ["Brief解析", "用户研究", "策略生成", "KOL组合", "建联话术", "创意Brief"]


@dataclass
class MarketingFlowState:
    stage: int = 0
    brief: str = ""
    skills: list[str] = field(default_factory=lambda: ["agency-agents", "content-marketing"])
    feedbacks: dict[int, str] = field(default_factory=dict)
    research_urls: list[str] = field(default_factory=list)
    research_notes: str = ""

    parsed: dict[str, Any] | None = None
    user_research: dict[str, Any] | None = None
    strategy: dict[str, Any] | None = None
    kol_combo: dict[str, Any] | None = None
    selected_kols: list[dict[str, Any]] = field(default_factory=list)
    outreach: list[dict[str, Any]] | None = None
    creative: dict[str, Any] | None = None

    messages: list[dict[str, str]] = field(default_factory=lambda: [
        {"role": "assistant", "content": "欢迎使用对话工作流。请先输入 Brief。"}
    ])


class MarketingFlowOrchestrator:
    """A provider-agnostic step orchestrator.

    Notes:
    - This orchestrator does not bind to Claude SDK.
    - Underlying model provider is selected by MA runtime (Kimi/OpenAI/Claude/Minimax).
    """

    def __init__(self, state: MarketingFlowState | None = None):
        self.state = state or MarketingFlowState()

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "MarketingFlowOrchestrator":
        if not data:
            return cls()
        state = MarketingFlowState(
            stage=int(data.get("stage", 0)),
            brief=str(data.get("brief", "")),
            skills=list(data.get("skills", ["agency-agents", "content-marketing"])),
            feedbacks={int(k): v for k, v in (data.get("feedbacks", {}) or {}).items()},
            research_urls=list(data.get("research_urls", [])),
            research_notes=str(data.get("research_notes", "")),
            parsed=data.get("parsed"),
            user_research=data.get("user_research"),
            strategy=data.get("strategy"),
            kol_combo=data.get("kol_combo"),
            selected_kols=list(data.get("selected_kols", [])),
            outreach=data.get("outreach"),
            creative=data.get("creative"),
            messages=list(data.get("messages", [])) or [{"role": "assistant", "content": "欢迎使用对话工作流。请先输入 Brief。"}],
        )
        return cls(state)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.state.stage,
            "brief": self.state.brief,
            "skills": self.state.skills,
            "feedbacks": self.state.feedbacks,
            "research_urls": self.state.research_urls,
            "research_notes": self.state.research_notes,
            "parsed": self.state.parsed,
            "user_research": self.state.user_research,
            "strategy": self.state.strategy,
            "kol_combo": self.state.kol_combo,
            "selected_kols": self.state.selected_kols,
            "outreach": self.state.outreach,
            "creative": self.state.creative,
            "messages": self.state.messages,
        }

    def set_brief(self, brief: str):
        self.state.brief = (brief or "").strip()

    def set_skills(self, skills: list[str]):
        self.state.skills = skills or []

    def set_feedback(self, stage: int, text: str):
        self.state.feedbacks[int(stage)] = (text or "").strip()

    def set_research_inputs(self, urls_text: str, notes: str):
        self.state.research_urls = [u.strip() for u in (urls_text or "").splitlines() if u.strip()]
        self.state.research_notes = (notes or "").strip()

    def set_selected_kols_by_names(self, names: list[str]):
        combo = self.state.kol_combo or {}
        pool = (combo.get("recommended_head", []) or []) + (combo.get("recommended_waist", []) or [])
        by_name = {k.get("name"): k for k in pool if k.get("name")}
        self.state.selected_kols = [by_name[n] for n in names if n in by_name]

    def stage_name(self) -> str:
        idx = self.state.stage
        if 0 <= idx < len(STAGE_NAMES):
            return STAGE_NAMES[idx]
        return "完成"

    def confirm_next(self):
        self.state.stage = min(self.state.stage + 1, len(STAGE_NAMES))
        self.state.messages.append({"role": "assistant", "content": f"已确认，进入【{self.stage_name()}】。"})

    def current_artifact(self) -> Any:
        m = {
            0: self.state.parsed,
            1: self.state.user_research,
            2: self.state.strategy,
            3: self.state.kol_combo,
            4: self.state.outreach,
            5: self.state.creative,
        }
        return m.get(min(self.state.stage, 5))

    def _build_user_research(self) -> dict[str, Any]:
        parsed = self.state.parsed or {}
        notes = "\n".join(
            [
                self.state.research_notes.strip(),
                f"用户反馈: {self.state.feedbacks.get(1, '').strip()}",
            ]
        ).strip()
        return generate_user_research_with_llm(
            brief_data=parsed,
            brief_text=self.state.brief,
            external_links=self.state.research_urls,
            user_notes=notes,
        )

    def run_current_stage(self) -> dict[str, Any]:
        stage = self.state.stage

        if stage == 0:
            if not self.state.brief:
                return {"summary": "请先输入 Brief。", "artifact": None}
            self.state.parsed = parse_brief(self.state.brief)
            p = self.state.parsed or {}
            return {
                "summary": f"已完成Brief解析：品牌={p.get('brand','未提及')}，行业={p.get('industry','未提及')}，目标={p.get('goal','未提及')}。",
                "artifact": self.state.parsed,
            }

        if stage == 1:
            if not self.state.parsed:
                self.state.parsed = parse_brief(self.state.brief)
            self.state.user_research = self._build_user_research()
            return {
                "summary": f"已生成用户研究草案（含{len(self.state.research_urls)}个外部链接输入）。",
                "artifact": self.state.user_research,
            }

        if stage == 2:
            if not self.state.parsed:
                self.state.parsed = parse_brief(self.state.brief)
            if not self.state.user_research:
                self.state.user_research = self._build_user_research()
            payload = dict(self.state.parsed)
            payload["skills"] = self.state.skills
            payload["user_research_confirmed"] = self.state.user_research
            payload["additional_feedback"] = self.state.feedbacks.get(2, "")
            strategy = generate_strategy(payload)
            if isinstance(strategy, dict):
                strategy["audience_research"] = {
                    "segments": [
                        {
                            "name": "核心消费人群",
                            "profile": self.state.user_research.get("persona_profile", {}).get("target_audience", "未提及"),
                            "habits": self.state.user_research.get("behavior_habits", []),
                            "product_linked_lifestyles": self.state.user_research.get("scenario_insights", []),
                            "core_tensions": self.state.user_research.get("emotional_insights", []),
                        }
                    ],
                    "insights": self.state.user_research.get("scenario_insights", []),
                }
            self.state.strategy = strategy
            return {"summary": "策略已生成。", "artifact": self.state.strategy}

        if stage == 3:
            parsed = self.state.parsed or parse_brief(self.state.brief)
            strategy = self.state.strategy or generate_strategy({
                "industry": parsed.get("industry", "通用"),
                "goal": parsed.get("goal", "品牌曝光"),
                "budget": parsed.get("budget", "中等"),
                "skills": self.state.skills,
            })
            platforms = [p.get("name", "") for p in strategy.get("platform_strategy", []) if p.get("name")] if isinstance(strategy, dict) else []
            if not platforms:
                platforms = parsed.get("preferred_platforms", []) or ["小红书", "抖音"]
            try:
                budget_num = float(parsed.get("budget_amount", 50))
            except Exception:
                budget_num = 50.0
            self.state.kol_combo = generate_kol_combo_with_llm(
                budget=budget_num,
                platforms=platforms[:2],
                category=parsed.get("industry", "通用"),
                brand=parsed.get("brand", "品牌"),
                product="产品",
                goal=parsed.get("goal", "品牌曝光"),
                skills=self.state.skills,
            )
            return {"summary": "KOL组合已生成。", "artifact": self.state.kol_combo}

        if stage == 4:
            parsed = self.state.parsed or parse_brief(self.state.brief)
            picked = self.state.selected_kols
            if not picked:
                combo = self.state.kol_combo or {}
                picked = (combo.get("recommended_head", []) + combo.get("recommended_waist", []))[:5]
            style = "professional"
            fb = (self.state.feedbacks.get(4, "") or "").lower()
            if "casual" in fb or "轻松" in fb:
                style = "casual"
            msgs = []
            for kol in picked:
                msg = generate_outreach_with_llm(
                    kol_name=kol.get("name", "KOL"),
                    kol_profile=kol,
                    brand=parsed.get("brand", "品牌"),
                    brand_intro="品牌合作邀约",
                    product="产品",
                    platform=kol.get("platform", "小红书"),
                    style=style,
                    cooperation_type="内容合作",
                    budget_range="面议",
                    skills=self.state.skills,
                )
                msgs.append({"kol": kol.get("name", "KOL"), "platform": kol.get("platform", "小红书"), "message": msg})
            self.state.outreach = msgs
            return {"summary": f"建联话术已生成（{len(msgs)}条）。", "artifact": self.state.outreach}

        if stage == 5:
            parsed = self.state.parsed or parse_brief(self.state.brief)
            strategy = self.state.strategy or {}
            platforms = [p.get("name", "") for p in strategy.get("platform_strategy", []) if p.get("name")] if isinstance(strategy, dict) else []
            if not platforms:
                platforms = parsed.get("preferred_platforms", []) or ["小红书"]
            creative: dict[str, Any] = {}
            kol_profile = self.state.selected_kols[0] if self.state.selected_kols else {}
            for p in platforms[:2]:
                creative[p] = generate_creative_brief_with_llm(
                    brand=parsed.get("brand", "品牌"),
                    product="产品",
                    platform=p,
                    kol_style="真实分享",
                    key_messages=parsed.get("key_messages", []),
                    must_include=["产品展示", "使用体验"],
                    forbidden=["绝对化宣传", "虚假承诺"],
                    target_audience=parsed.get("target_audience", "目标受众"),
                    campaign_goal=parsed.get("goal", "品牌曝光"),
                    industry=parsed.get("industry", "通用"),
                    skills=self.state.skills,
                    kol_profile=kol_profile,
                )
            self.state.creative = creative
            return {"summary": "创意Brief已完成。", "artifact": self.state.creative}

        return {"summary": "流程已完成。", "artifact": self.state.creative}

    def append_user_message(self, text: str):
        self.state.messages.append({"role": "user", "content": text})

    def append_assistant_message(self, text: str):
        self.state.messages.append({"role": "assistant", "content": text})

    def export_package(self) -> dict[str, Any]:
        return {
            "brief": self.state.brief,
            "parsed": self.state.parsed,
            "user_research": self.state.user_research,
            "strategy": self.state.strategy,
            "kol_combo": self.state.kol_combo,
            "selected_kols": self.state.selected_kols,
            "outreach": self.state.outreach,
            "creative": self.state.creative,
            "skills": self.state.skills,
            "feedbacks": self.state.feedbacks,
        }
