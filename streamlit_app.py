"""
Flow 复楼 MA Agent - Streamlit Web UI
智能社交营销AI代理平台
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional, Union

import streamlit as st

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from agent_core.llm import get_llm_client, reset_llm_client
from agent_core.tools.strategy_iq import parse_brief, generate_strategy
from agent_core.tools.match_ai import search_kols, generate_kol_combo_with_llm
from agent_core.tools.connect_bot import (
    generate_outreach_with_llm,
    generate_follow_up_with_llm,
    generate_negotiation_strategy_with_llm,
)
from agent_core.tools.creative_pilot import (
    generate_creative_brief_with_llm,
    generate_content_with_llm,
    review_content_with_llm,
)
from agent_core.workflow.marketing_workflow import MarketingWorkflow
from agent_core.workflow.marketing_workflow_v2 import MarketingWorkflowV2
from agent_core.clarification.engine import ClarificationEngine
from agent_core.eval.recorder import get_eval_recorder, EvalRecord

# ============================================
# 页面配置
# ============================================
st.set_page_config(
    page_title="Flow 复楼 - 智能社交营销AI代理",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 可选 Skills（用于路由到后端 skills 层）
AVAILABLE_SKILLS = [
    "agency-agents",
    "competitive-analysis",
    "content-marketing",
    "brand-storytelling",
    "marketing-xiaohongshu-specialist",
    "marketing-douyin-strategist",
    "sales-outbound-strategist",
]

# ============================================
# CSS样式
# ============================================
st.markdown("""
<style>
    /* 主标题 */
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #6366F1, #8B5CF6, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    /* 副标题 */
    .subtitle {
        color: #6B7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* 模块卡片 */
    .module-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 1rem;
    }
    
    /* 结果展示框 */
    .result-box {
        background-color: #F3F4F6;
        border-left: 4px solid #6366F1;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* 标签样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 0.5rem 0.5rem 0 0;
        gap: 1rem;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    /* 按钮美化 */
    .stButton>button {
        border-radius: 0.5rem;
        padding: 0.5rem 2rem;
        font-weight: 600;
    }
    
    /* 侧边栏 */
    .css-1d391kg {
        padding-top: 2rem;
    }
    
    /* 成功消息 */
    .success-msg {
        background-color: #D1FAE5;
        border: 1px solid #10B981;
        color: #065F46;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    
    /* 信息卡片 */
    .info-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# 侧边栏 - 配置
# ============================================
def render_sidebar():
    with st.sidebar:
        st.markdown("### 🧭 页面导航")
        nav_options = ["首页", "工作流", "StrategyIQ", "MatchAI", "ConnectBot", "CreativePilot"]
        current = st.session_state.get("current_tab", "首页")
        if current in {"工作流工作台", "工作流V2"}:
            current = "工作流"
        if current not in nav_options:
            current = "首页"
        selected_tab = st.radio(
            "跳转到",
            nav_options,
            index=nav_options.index(current),
            label_visibility="collapsed",
            key="sidebar_nav_tab",
        )
        st.session_state.current_tab = selected_tab
        st.divider()

        st.markdown("### ⚙️ 系统配置")
        minimax_group_id = os.getenv("MINIMAX_GROUP_ID", "")
        
        # LLM提供商选择
        provider = st.selectbox(
            "选择LLM提供商",
            options=["mock", "deepseek", "openai", "claude", "kimi", "minimax"],
            format_func=lambda x: {
                "mock": "🧪 Mock (测试用)",
                "deepseek": "🚀 DeepSeek (推荐)",
                "openai": "🤖 OpenAI GPT",
                "claude": "🧠 Claude",
                "kimi": "🌙 Kimi (月之暗面)",
                "minimax": "🧩 Minimax",
            }.get(x, x),
            help="选择要使用的AI模型提供商",
        )
        
        # API Key输入
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="输入你的API Key",
            help="在此输入所选提供商的API Key",
        )
        
        # 模型选择
        if provider == "deepseek":
            model = st.selectbox(
                "模型",
                ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
                help="deepseek-chat适合一般对话",
            )
        elif provider == "openai":
            model = st.selectbox(
                "模型",
                ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            )
        elif provider == "claude":
            model = st.selectbox(
                "模型",
                ["claude-3-sonnet-20240229", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            )
        elif provider == "kimi":
            model = st.selectbox(
                "模型",
                ["kimi-k2.5", "kimi-k2", "kimi-latest", "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
                help="kimi-k2.5 是最新版本，推荐使用",
            )
        elif provider == "minimax":
            model = st.selectbox(
                "模型",
                ["abab6.5-chat", "abab6.5s-chat", "abab7-chat-preview"],
                help="默认使用 abab6.5-chat；如你的账号支持，可切换更高版本",
            )
            minimax_group_id = st.text_input(
                "Minimax Group ID（可选）",
                value=minimax_group_id,
                help="部分账号/端点需要 Group ID；如不需要可留空",
            )
        else:
            model = "mock"
        
        # 应用配置按钮
        if st.button("🔄 应用配置", type="primary", use_container_width=True):
            if provider != "mock" and not api_key:
                st.error("⚠️ 请输入API Key")
            else:
                # 设置环境变量
                os.environ["LLM_PROVIDER"] = provider
                if api_key:
                    key_mapping = {
                        "deepseek": "DEEPSEEK_API_KEY",
                        "openai": "OPENAI_API_KEY",
                        "claude": "ANTHROPIC_API_KEY",
                        "kimi": "KIMI_API_KEY",
                        "minimax": "MINIMAX_API_KEY",
                    }
                    if provider in key_mapping:
                        os.environ[key_mapping[provider]] = api_key
                if provider == "minimax":
                    os.environ["MINIMAX_GROUP_ID"] = minimax_group_id.strip()
                
                os.environ[f"{provider.upper()}_MODEL"] = model
                
                # 重置客户端
                reset_llm_client()
                st.session_state.llm_configured = True
                st.session_state.provider = provider
                st.session_state.model = model
                st.success(f"✅ 已切换到 {provider} ({model})")
        
        st.divider()
        
        # 当前状态
        st.markdown("### 📊 系统状态")
        if st.session_state.get("llm_configured"):
            st.success(f"🟢 当前模型: {st.session_state.get('provider', 'mock')}")
            st.info(f"模型: {st.session_state.get('model', 'default')}")
        else:
            st.warning("🟡 使用默认配置 (Mock)")
        
        st.divider()
        
        # 关于
        st.markdown("### ℹ️ 关于")
        st.markdown("""
        **Flow 复楼 MA Agent**
        
        AI驱动的全链路社交营销智能代理
        
        每一分投放都应该有复利
        
        v1.1.0
        """)


# ============================================
# 首页
# ============================================
def render_home():
    st.markdown('<p class="main-title">🚀 Flow 复楼</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI驱动的全链路社交营销智能代理平台</p>', unsafe_allow_html=True)
    
    # 四大模块卡片
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="module-card">
            <h3>🧠 StrategyIQ</h3>
            <p>策略理解与生成引擎</p>
            <ul>
                <li>Brief智能解析</li>
                <li>营销策略生成</li>
                <li>预算分配优化</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="module-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h3>🤝 ConnectBot</h3>
            <p>智能建联与协作代理</p>
            <ul>
                <li>个性化话术生成</li>
                <li>智能跟进策略</li>
                <li>谈判建议</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="module-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h3>🎯 MatchAI</h3>
            <p>KOL/KOC智能匹配系统</p>
            <ul>
                <li>KOL智能搜索</li>
                <li>匹配度分析</li>
                <li>组合推荐</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="module-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <h3>✨ CreativePilot</h3>
            <p>创意内容指导助手</p>
            <ul>
                <li>创意Brief生成</li>
                <li>内容模板</li>
                <li>合规审核</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # 快速开始
    st.divider()
    st.markdown("### 🚀 快速开始")
    
    quick_cols = st.columns(5)
    with quick_cols[0]:
        if st.button("🧩 进入工作流", use_container_width=True):
            st.session_state.current_tab = "工作流"
            st.rerun()
    with quick_cols[1]:
        if st.button("📊 生成策略", use_container_width=True):
            st.session_state.current_tab = "StrategyIQ"
            st.rerun()
    with quick_cols[2]:
        if st.button("🎯 搜索KOL", use_container_width=True):
            st.session_state.current_tab = "MatchAI"
            st.rerun()
    with quick_cols[3]:
        if st.button("✉️ 生成话术", use_container_width=True):
            st.session_state.current_tab = "ConnectBot"
            st.rerun()
    with quick_cols[4]:
        if st.button("🎨 创意指导", use_container_width=True):
            st.session_state.current_tab = "CreativePilot"
            st.rerun()


# ============================================
# 通用反馈组件
# ============================================
def render_feedback_section(module_name: str, record_id: Optional[str] = None):
    """渲染反馈输入区域 - 改进版：更直观的反馈流程
    
    Args:
        module_name: 模块名称（如 StrategyIQ、MatchAI 等）
        record_id: 可选的记录ID，如果不提供则自动创建
    """
    st.divider()
    st.markdown(f"#### 💬 对这个{module_name}结果满意吗？")
    
    # 生成唯一的 session state key
    state_key_prefix = f"feedback_{module_name}_{record_id or 'new'}"
    rating_key = f"{state_key_prefix}_rating"
    submitted_key = f"{state_key_prefix}_submitted"
    
    # 初始化 session state
    if rating_key not in st.session_state:
        st.session_state[rating_key] = None
    if submitted_key not in st.session_state:
        st.session_state[submitted_key] = False
    
    # 如果已经提交过，显示感谢信息
    if st.session_state[submitted_key]:
        st.success("✅ 感谢您的反馈！已保存到评估系统。")
        if st.button("🔄 重新评价", key=f"{state_key_prefix}_reset"):
            st.session_state[submitted_key] = False
            st.session_state[rating_key] = None
            st.rerun()
        return
    
    # 评分选择 - 使用 radio 更直观
    rating_options = {
        5: "👍 满意 - 结果很好，符合预期",
        3: "😐 一般 - 还可以，但有改进空间", 
        2: "👎 需改进 - 不满意，需要优化"
    }
    
    current_rating = st.session_state[rating_key]
    rating_index = None
    if current_rating == 5:
        rating_index = 0
    elif current_rating == 3:
        rating_index = 1
    elif current_rating == 2:
        rating_index = 2
    
    selected_rating = st.radio(
        "请选择您的评价",
        options=list(rating_options.keys()),
        format_func=lambda x: rating_options[x],
        index=rating_index,
        key=f"{state_key_prefix}_radio",
        horizontal=True,
    )
    
    # 更新评分状态
    if selected_rating != current_rating:
        st.session_state[rating_key] = selected_rating
        st.rerun()
    
    # 反馈输入区域 - 始终可见
    st.markdown("##### 📝 详细反馈（可选）")
    
    feedback_text = st.text_area(
        "请输入您的意见或建议",
        placeholder=f"例如：{module_name}的输出很准确，但是...",
        height=80,
        key=f"{state_key_prefix}_text"
    )
    
    # 问题标签
    issue_options = ["结果不准确", "缺少关键信息", "建议不合理", "格式不清晰", "其他问题"]
    selected_issues = st.multiselect(
        "发现的问题（可多选）",
        options=issue_options,
        key=f"{state_key_prefix}_issues"
    )
    
    # 自定义问题
    custom_issue = st.text_input(
        "其他问题描述（可选）",
        placeholder="请描述您发现的其他问题...",
        key=f"{state_key_prefix}_custom"
    )
    
    # 提交按钮
    col1, col2 = st.columns([1, 2])
    with col2:
        if st.button("📤 提交反馈", key=f"{state_key_prefix}_submit", use_container_width=True, type="primary"):
            recorder = get_eval_recorder()
            
            # 构建问题列表
            issues_list = list(selected_issues) if selected_issues else []
            if custom_issue:
                issues_list.append(custom_issue)
            
            # 确定评分和反馈文字
            rating = st.session_state[rating_key] or 3  # 默认一般
            
            if rating == 5:
                default_feedback = f"用户对{module_name}结果满意"
            elif rating == 3:
                default_feedback = f"用户认为{module_name}结果一般"
            else:
                default_feedback = f"用户认为{module_name}需要改进"
            
            final_feedback = feedback_text if feedback_text else default_feedback
            
            # 创建或更新记录
            if record_id and record_id in recorder.records:
                recorder.add_human_feedback(
                    record_id,
                    rating=rating,
                    feedback=final_feedback,
                    issues=issues_list if issues_list else None
                )
            else:
                new_record = recorder.create_record(
                    brief=f"{module_name} 模块反馈",
                    module=module_name
                )
                recorder.add_human_feedback(
                    new_record.record_id,
                    rating=rating,
                    feedback=final_feedback,
                    issues=issues_list if issues_list else None
                )
                record_id = new_record.record_id
            
            st.session_state[submitted_key] = True
            
            # 显示成功消息
            storage_path = recorder.storage_dir / f"{record_id}.json"
            
            if rating >= 4:
                st.success(f"✅ 感谢您的反馈！已保存。")
            elif rating == 3:
                st.info(f"✅ 感谢您的反馈！我们会继续改进。")
            else:
                st.warning(f"✅ 感谢您的反馈！我们会重点改进。")
            
            st.caption(f"📁 存储位置：`{storage_path}`")
            st.caption(f"🆔 记录ID：`{record_id}`")
            
            st.rerun()


# ============================================
# StrategyIQ 页面
# ============================================
def render_strategy_iq():
    st.markdown("### 🧠 StrategyIQ - 策略理解与生成引擎")
    
    tab1, tab2 = st.tabs(["📋 Brief解析", "🎯 策略生成"])
    
    with tab1:
        st.markdown("#### 智能解析客户Brief")
        
        brief_text = st.text_area(
            "输入客户Brief",
            height=150,
            placeholder="例如：美妆品牌花西子新品口红上市，预算100万，目标种草年轻女性，主要在小红书和抖音投放...",
            help="输入客户的营销需求brief，AI将自动提取关键信息",
        )
        
        if st.button("🔍 解析Brief", type="primary"):
            if not brief_text:
                st.warning("请输入Brief内容")
            else:
                with st.spinner("AI正在解析..."):
                    try:
                        result = parse_brief(brief_text)
                        
                        st.success("✅ 解析完成！")
                        
                        # 展示结果
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**📌 基本信息**")
                            st.info(f"**品牌**: {result.get('brand', '未识别')}")
                            st.info(f"**行业**: {result.get('industry', '未识别')}")
                            st.info(f"**目标**: {result.get('goal', '未识别')}")
                        with col2:
                            st.markdown("**💰 预算与周期**")
                            st.info(f"**预算级别**: {result.get('budget', '未识别')}")
                            st.info(f"**预算金额**: {result.get('budget_amount', '未提及')}万")
                            st.info(f"**周期**: {result.get('timeline', '未提及')}")
                        
                        # 其他信息
                        if result.get('key_messages'):
                            st.markdown("**📝 关键信息**")
                            for msg in result.get('key_messages', []):
                                st.write(f"- {msg}")
                        
                        # JSON展示
                        with st.expander("查看完整JSON"):
                            st.json(result)

                        # 自动生成策略（默认串联）
                        st.markdown("**🎯 自动生成策略**")
                        with st.spinner("正在基于解析结果生成策略..."):
                            strategy = generate_strategy(result)

                        # 平台策略
                        st.markdown("**📱 平台策略**")
                        for platform in strategy.get("platform_strategy", [])[:3]:
                            st.write(
                                f"- **{platform.get('name', '未知平台')}**: "
                                f"{platform.get('goal', '')}（{platform.get('priority', '中')}优先级）"
                            )

                        # KOL组合
                        kol = strategy.get("kol_strategy", {})
                        st.markdown("**👥 KOL组合建议**")
                        st.write(
                            f"- 头部KOL：{kol.get('head_kol', {}).get('count', '0个')} | "
                            f"腰部KOL：{kol.get('waist_kol', {}).get('count', '0个')} | "
                            f"KOC：{kol.get('koc', {}).get('count', '0个')}"
                        )

                        # 行业模板
                        template = strategy.get("industry_template", {})
                        if template:
                            st.markdown("**🏭 行业模板建议**")
                            st.write(f"- 行业：{template.get('industry', '通用')}")
                            st.write(f"- 目标：{template.get('core_objective', '')}")
                            if template.get("content_pillars"):
                                st.write(f"- 内容支柱：{', '.join(template.get('content_pillars', [])[:4])}")
                        
                        # 反馈入口
                        render_feedback_section("StrategyIQ-Brief解析")
                    
                    except Exception as e:
                        st.error(f"❌ 解析失败: {str(e)}")
    
    with tab2:
        st.markdown("#### 生成营销策略")
        
        col1, col2 = st.columns(2)
        with col1:
            industry = st.selectbox(
                "行业",
                ["美妆", "3C数码", "快消", "母婴", "时尚", "食品", "其他"],
            )
            goal = st.selectbox(
                "营销目标",
                ["品牌曝光", "种草转化", "销售转化", "用户增长", "口碑传播"],
            )
        with col2:
            budget = st.selectbox(
                "预算级别",
                ["高(100万+)", "中高(50-100万)", "中等(20-50万)", "低(20万以下)"],
            )
            platforms = st.multiselect(
                "目标平台",
                ["小红书", "抖音", "微博", "B站", "快手", "微信视频号"],
                default=["小红书", "抖音"],
            )
        strategy_skills = st.multiselect(
            "启用Skills（可选）",
            AVAILABLE_SKILLS,
            default=["agency-agents", "content-marketing"],
            key="strategy_skills",
        )
        
        if st.button("🎯 生成策略", type="primary"):
            with st.spinner("AI正在生成策略..."):
                try:
                    brief_data = {
                        "industry": industry,
                        "budget": budget.split("(")[0],
                        "goal": goal,
                        "platforms": platforms,
                        "skills": strategy_skills,
                    }
                    
                    result = generate_strategy(brief_data)
                    
                    st.success("✅ 策略生成完成！")
                    
                    # 平台策略
                    st.markdown("**📱 平台策略**")
                    platform_cols = st.columns(len(result.get("platform_strategy", [])))
                    for i, platform in enumerate(result.get("platform_strategy", [])):
                        with platform_cols[i]:
                            st.metric(
                                platform["name"],
                                platform["goal"],
                                f"{platform['priority']}优先级",
                            )
                    
                    # KOL策略
                    st.markdown("**👥 KOL组合策略**")
                    kol = result.get("kol_strategy", {})
                    kol_cols = st.columns(3)
                    with kol_cols[0]:
                        st.info(f"**头部KOL**\n\n{kol.get('head_kol', {}).get('count', '0')}\n{kol.get('head_kol', {}).get('purpose', '')}")
                    with kol_cols[1]:
                        st.info(f"**腰部KOL**\n\n{kol.get('waist_kol', {}).get('count', '0')}\n{kol.get('waist_kol', {}).get('purpose', '')}")
                    with kol_cols[2]:
                        st.info(f"**KOC**\n\n{kol.get('koc', {}).get('count', '0')}\n{kol.get('koc', {}).get('purpose', '')}")
                    
                    # 预算分配
                    st.markdown("**💰 预算分配**")
                    budget_data = result.get("budget_allocation", {})
                    st.bar_chart({k: v for k, v in budget_data.items() if isinstance(v, (int, float))})
                    
                    # KPI
                    st.markdown("**📊 KPI目标**")
                    kpis = result.get("kpis", {})
                    for level, kpi in kpis.items():
                        st.write(f"- **{level}**: {kpi}")

                    framework = result.get("market_strategy_framework", {})
                    if framework:
                        with st.expander("🧠 市场策略分块框架（用户研究/竞品/产品/三定位）"):
                            user_research = framework.get("user_research", {})
                            st.write(f"**用户研究画像维度**: {', '.join(user_research.get('profile_dimensions', []))}")
                            for item in user_research.get("scenario_insights", [])[:2]:
                                st.write(f"- 场景洞察: {item}")
                            competitor = framework.get("competitor_analysis", {})
                            st.write(f"**竞品沟通方向**: {', '.join(competitor.get('communication_choice', []))}")
                            product_features = framework.get("product_features", {})
                            st.write(f"**产品独特属性**: {', '.join(product_features.get('unique_attributes', []))}")
                            st.write("**三定位方向**:")
                            for p in framework.get("triple_positioning_options", [])[:3]:
                                st.write(f"- {p.get('name', '定位')}: {p.get('logic', '')}")

                    if result.get("applied_skills"):
                        st.write(f"🧩 已应用Skills: {', '.join(result.get('applied_skills', []))}")
                    
                    # 时间线
                    st.markdown("**📅 执行时间线**")
                    for phase in result.get("timeline", []):
                        with st.expander(f"{phase['phase']} ({phase['duration']})"):
                            for activity in phase.get("activities", []):
                                st.write(f"- {activity}")
                    
                    # 反馈入口
                    render_feedback_section("StrategyIQ-策略生成")
                
                except Exception as e:
                    st.error(f"❌ 生成失败: {str(e)}")


# ============================================
# MatchAI 页面
# ============================================
def render_match_ai():
    st.markdown("### 🎯 MatchAI - KOL/KOC智能匹配系统")
    
    tab1, tab2 = st.tabs(["🔍 KOL搜索", "🎯 智能组合"])
    
    with tab1:
        st.markdown("#### 搜索并分析KOL")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            platform = st.selectbox(
                "平台",
                ["小红书", "抖音", "微博", "B站"],
                key="search_platform",
            )
            category = st.selectbox(
                "内容分类",
                ["美妆", "3C", "生活方式", "母婴", "时尚", "美食", "娱乐"],
            )
        with col2:
            min_followers = st.text_input("最小粉丝量", placeholder="如: 10万")
            min_engagement = st.slider("最低互动率(%)", 0.0, 20.0, 5.0)
        with col3:
            city = st.text_input("城市", placeholder="如: 上海")
            limit = st.slider("返回数量", 1, 20, 5)
        
        # 品牌信息（用于LLM分析）
        with st.expander("品牌信息（用于智能匹配分析）"):
            brand = st.text_input("品牌名称", placeholder="如: 花西子")
            product = st.text_input("产品", placeholder="如: 新品口红")
            target_audience = st.text_input("目标受众", placeholder="如: 18-25岁年轻女性")
        
        if st.button("🔍 搜索KOL", type="primary"):
            with st.spinner("正在搜索并分析KOL..."):
                try:
                    results = search_kols(
                        platform=platform,
                        category=category,
                        min_followers=min_followers or None,
                        min_engagement=min_engagement,
                        city=city or None,
                        brand=brand,
                        product=product,
                        target_audience=target_audience,
                        limit=limit,
                    )
                    
                    if not results:
                        st.info("未找到符合条件的KOL")
                    else:
                        st.success(f"✅ 找到 {len(results)} 位KOL")
                        
                        for i, kol in enumerate(results, 1):
                            with st.container():
                                col_a, col_b, col_c = st.columns([2, 2, 1])
                                with col_a:
                                    st.markdown(f"**{i}. {kol['name']}**")
                                    st.write(f"📍 {kol['city']} | 🏷️ {kol['category']}")
                                with col_b:
                                    st.write(f"👥 粉丝: {kol['followers']}")
                                    st.write(f"📈 互动率: {kol['engagement']}")
                                    st.write(f"💰 报价: {kol['price']}")
                                with col_c:
                                    match_score = kol.get('match_score', 0)
                                    st.metric("匹配度", f"{match_score}%")
                                    st.write(f"💡 ROI: {kol.get('estimated_roi', '未知')}")
                                
                                # 详细分析
                                if 'match_reasoning' in kol:
                                    with st.expander("查看AI匹配分析"):
                                        st.write(kol.get('match_reasoning', ''))
                                        st.write(f"**受众重叠**: {kol.get('audience_overlap', '')}")
                                        st.write(f"**内容契合**: {kol.get('content_fit', '')}")
                                
                                st.divider()
                        
                        # 反馈入口
                        render_feedback_section("MatchAI-KOL搜索")
                
                except Exception as e:
                    st.error(f"❌ 搜索失败: {str(e)}")
    
    with tab2:
        st.markdown("#### 生成KOL组合方案")
        
        col1, col2 = st.columns(2)
        with col1:
            budget_combo = st.number_input("预算(万)", min_value=10, max_value=1000, value=100)
            combo_platforms = st.multiselect(
                "投放平台",
                ["小红书", "抖音", "微博", "B站"],
                default=["小红书", "抖音"],
                key="combo_platforms",
            )
        with col2:
            combo_category = st.selectbox(
                "产品分类",
                ["美妆", "3C", "快消", "母婴", "时尚"],
                key="combo_category",
            )
            combo_goal = st.selectbox(
                "活动目标",
                ["种草", "曝光", "转化", "品宣"],
            )
        
        combo_brand = st.text_input("品牌", placeholder="如: 花西子", key="combo_brand")
        combo_product = st.text_input("产品", placeholder="如: 新品口红", key="combo_product")
        combo_skills = st.multiselect(
            "启用Skills（可选）",
            AVAILABLE_SKILLS,
            default=["agency-agents", "competitive-analysis"],
            key="combo_skills",
        )
        
        if st.button("🎯 生成组合方案", type="primary"):
            with st.spinner("AI正在生成最优组合..."):
                try:
                    result = generate_kol_combo_with_llm(
                        budget=budget_combo,
                        platforms=combo_platforms,
                        category=combo_category,
                        brand=combo_brand or "品牌",
                        product=combo_product or "产品",
                        goal=combo_goal,
                        skills=combo_skills,
                    )
                    
                    st.success("✅ 组合方案生成完成！")
                    
                    # 策略概述
                    st.markdown(f"**📝 {result.get('strategy_overview', 'KOL组合策略')}**")
                    
                    # 预算分配
                    st.markdown("**💰 预算分配**")
                    budget_breakdown = result.get("budget_allocation", {})
                    cols = st.columns(len(budget_breakdown))
                    for i, (tier, info) in enumerate(budget_breakdown.items()):
                        with cols[i]:
                            st.metric(
                                tier.replace("_", " ").title(),
                                f"{info.get('amount', 0)}万",
                                f"{info.get('percentage', 0)}%",
                            )
                    
                    # 推荐KOL
                    st.markdown("**👥 推荐KOL**")
                    head_kols = result.get("recommended_head", [])
                    waist_kols = result.get("recommended_waist", [])
                    
                    if head_kols:
                        st.markdown("*头部KOL*")
                        for kol in head_kols:
                            st.write(f"- **{kol.get('name', '')}** ({kol.get('followers', '')}粉) - {kol.get('reasoning', '')}")
                    
                    if waist_kols:
                        st.markdown("*腰部KOL*")
                        for kol in waist_kols:
                            st.write(f"- **{kol.get('name', '')}** ({kol.get('followers', '')}粉) - {kol.get('reasoning', '')}")
                    
                    # 预期效果
                    st.markdown("**📊 预期效果**")
                    expected = result.get("expected_results", {})
                    st.info(f"总触达: {expected.get('total_reach', 'N/A')} | 预估互动: {expected.get('estimated_engagement', 'N/A')} | 预期ROI: {expected.get('expected_roi', 'N/A')}")

                    comm_plan = result.get("communication_plan", {})
                    if comm_plan:
                        with st.expander("📣 传播主题与节奏（三段式）"):
                            for topic in comm_plan.get("theme_options", [])[:2]:
                                st.write(f"- [{topic.get('type', '')}] {topic.get('theme', '')}")
                            rhythm = comm_plan.get("rhythm", {})
                            for phase_key, phase_name in [("opening", "开篇"), ("explosion", "引爆"), ("elevation", "升华")]:
                                phase = rhythm.get(phase_key, {})
                                if phase:
                                    st.write(f"**{phase_name}({phase.get('duration_days', '')}天)**: {phase.get('goal', '')}")
                                    st.write(f"- 重点: {phase.get('focus', '')}")

                    if result.get("manual_override"):
                        st.write("🛠️ 支持人工干预：可对KOL组合进行添加/修改/删除")

                    if result.get("applied_skills"):
                        st.write(f"🧩 已应用Skills: {', '.join(result.get('applied_skills', []))}")
                    
                    # 完整方案
                    with st.expander("查看完整方案JSON"):
                        st.json(result)
                    
                    # 反馈入口
                    render_feedback_section("MatchAI-智能组合")
                
                except Exception as e:
                    st.error(f"❌ 生成失败: {str(e)}")


# ============================================
# ConnectBot 页面
# ============================================
def render_connect_bot():
    st.markdown("### 🤝 ConnectBot - 智能建联与协作代理")
    
    tab1, tab2, tab3 = st.tabs(["✉️ 建联话术", "📨 跟进话术", "💼 谈判建议"])
    
    with tab1:
        st.markdown("#### 生成个性化建联话术")
        
        col1, col2 = st.columns(2)
        with col1:
            outreach_kol = st.text_input("KOL名称", placeholder="如: 美妆达人小美")
            outreach_brand = st.text_input("品牌名称", placeholder="如: 花西子")
            outreach_product = st.text_input("产品", placeholder="如: 新品口红")
        with col2:
            outreach_platform = st.selectbox(
                "平台",
                ["小红书", "抖音", "微博", "B站"],
                key="outreach_platform",
            )
            outreach_style = st.selectbox(
                "话术风格",
                ["professional", "casual", "formal"],
                format_func=lambda x: {
                    "professional": "专业商务",
                    "casual": "轻松友好",
                    "formal": "正式严谨",
                }.get(x, x),
            )
            outreach_budget = st.text_input("预算范围", placeholder="如: 5-8万")
        
        # KOL信息
        with st.expander("KOL详细信息（可选，用于更个性化的话术）"):
            kol_followers = st.text_input("粉丝量", placeholder="如: 50万")
            kol_category = st.text_input("内容领域", placeholder="如: 美妆")
            kol_recent = st.text_area("近期内容", placeholder="如: 口红试色、护肤日常")
        outreach_skills = st.multiselect(
            "启用Skills（可选）",
            AVAILABLE_SKILLS,
            default=["agency-agents", "brand-storytelling"],
            key="outreach_skills",
        )
        
        if st.button("✉️ 生成建联话术", type="primary"):
            if not outreach_kol or not outreach_brand:
                st.warning("请填写KOL名称和品牌名称")
            else:
                with st.spinner("AI正在生成话术..."):
                    try:
                        result = generate_outreach_with_llm(
                            kol_name=outreach_kol,
                            kol_profile={
                                "followers": kol_followers,
                                "category": kol_category,
                                "recent_posts": kol_recent.split(",") if kol_recent else [],
                            },
                            brand=outreach_brand,
                            brand_intro=f"致力于提供优质{outreach_product}" if outreach_product else "优质品牌",
                            product=outreach_product or "产品",
                            platform=outreach_platform,
                            style=outreach_style,
                            cooperation_type="内容合作",
                            budget_range=outreach_budget or "面议",
                            skills=outreach_skills,
                        )
                        
                        st.success("✅ 话术生成完成！")
                        
                        # 展示话术
                        st.markdown("**📧 邮件/私信内容**")
                        st.text_input("主题", result.get("subject", ""), key="outreach_subject")
                        st.text_area(
                            "正文",
                            result.get("full_message", result.get("body", "")),
                            height=400,
                            key="outreach_body",
                        )
                        
                        # 复制按钮
                        full_message = f"主题: {result.get('subject', '')}\n\n{result.get('full_message', result.get('body', ''))}"
                        st.code(full_message, language="text")
                        
                        # 要点分析
                        with st.expander("话术要点分析"):
                            st.write(f"**价值主张**: {result.get('value_proposition', 'N/A')}")
                            st.write(f"**下一步**: {result.get('next_steps', 'N/A')}")
                            if result.get("contact_discovery_checklist"):
                                st.write(f"**联系方式核查**: {', '.join(result.get('contact_discovery_checklist', []))}")
                            if result.get("required_confirmation_fields"):
                                st.write(f"**建联需确认信息**: {', '.join(result.get('required_confirmation_fields', []))}")
                            if result.get("applied_skills"):
                                st.write(f"**已应用Skills**: {', '.join(result.get('applied_skills', []))}")
                        
                        # 反馈入口
                        render_feedback_section("ConnectBot-建联话术")
                    
                    except Exception as e:
                        st.error(f"❌ 生成失败: {str(e)}")
    
    with tab2:
        st.markdown("#### 生成跟进话术")
        
        col1, col2 = st.columns(2)
        with col1:
            follow_kol = st.text_input("KOL名称", placeholder="如: 小美", key="follow_kol")
            follow_brand = st.text_input("品牌", placeholder="如: 花西子", key="follow_brand")
        with col2:
            follow_days = st.slider("距离上次联系(天)", 1, 30, 3)
            follow_response = st.selectbox(
                "KOL响应状态",
                ["未回复", "已读未回", "表示兴趣", "暂时拒绝"],
            )
        
        if st.button("📨 生成跟进话术", type="primary"):
            with st.spinner("AI正在生成跟进话术..."):
                try:
                    result = generate_follow_up_with_llm(
                        kol_name=follow_kol or "KOL",
                        brand=follow_brand or "品牌",
                        days_since=follow_days,
                        previous_message="",
                        kol_response=None if follow_response == "未回复" else follow_response,
                    )
                    
                    st.success("✅ 跟进话术生成完成！")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.info(f"**语气**: {result.get('tone', 'moderate')}")
                    with col_b:
                        st.info(f"**策略**: {result.get('psychology', 'N/A')}")
                    
                    st.markdown("**📨 跟进消息**")
                    st.text_area("内容", result.get("message", ""), height=200)
                    
                    st.write(f"**行动号召**: {result.get('call_to_action', 'N/A')}")
                    
                    # 反馈入口
                    render_feedback_section("ConnectBot-跟进话术")
                
                except Exception as e:
                    st.error(f"❌ 生成失败: {str(e)}")
    
    with tab3:
        st.markdown("#### 谈判策略建议")
        
        col1, col2 = st.columns(2)
        with col1:
            neg_kol_price = st.number_input("KOL报价(万)", min_value=0.1, max_value=100.0, value=5.0)
            neg_budget = st.number_input("品牌预算(万)", min_value=0.1, max_value=100.0, value=4.0)
        with col2:
            neg_engagement = st.slider("KOL互动率(%)", 0.0, 20.0, 8.5)
            neg_followers = st.number_input("KOL粉丝数", min_value=1000, max_value=10000000, value=500000)
        
        if st.button("💼 生成谈判策略", type="primary"):
            with st.spinner("AI正在分析谈判策略..."):
                try:
                    result = generate_negotiation_strategy_with_llm(
                        kol_price=neg_kol_price,
                        budget=neg_budget,
                        kol_data={
                            "engagement": neg_engagement,
                            "followers": neg_followers,
                        },
                        brand_value="品牌价值和资源",
                    )
                    
                    st.success("✅ 谈判策略生成完成！")
                    
                    # 价格评估
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("KOL报价", f"{neg_kol_price}万")
                    with col_b:
                        st.metric("建议报价", f"{result.get('suggested_offer', neg_budget * 0.9)}万")
                    with col_c:
                        diff = neg_kol_price - result.get('suggested_offer', neg_budget * 0.9)
                        st.metric("可谈空间", f"{diff:.1f}万", delta=f"{-diff/neg_kol_price*100:.0f}%" if diff > 0 else None)
                    
                    # 策略要点
                    st.markdown("**💡 谈判策略**")
                    for tactic in result.get("negotiation_tactics", []):
                        st.write(f"- {tactic}")
                    
                    # 筹码
                    st.markdown("**🎯 谈判筹码**")
                    for value in result.get("value_propositions", []):
                        st.write(f"- {value}")
                    
                    # 底线
                    st.markdown("**🚫 底线条件**")
                    for deal_breaker in result.get("deal_breakers", []):
                        st.warning(deal_breaker)
                    
                    # 反馈入口
                    render_feedback_section("ConnectBot-谈判策略")
                
                except Exception as e:
                    st.error(f"❌ 生成失败: {str(e)}")


# ============================================
# CreativePilot 页面
# ============================================
def render_creative_pilot():
    st.markdown("### ✨ CreativePilot - 创意内容指导助手")
    
    tab1, tab2, tab3 = st.tabs(["🎨 创意Brief", "📝 内容模板", "🔍 内容审核"])
    
    with tab1:
        st.markdown("#### 生成KOL创意Brief")
        
        col1, col2 = st.columns(2)
        with col1:
            brief_brand = st.text_input("品牌", placeholder="如: 花西子", key="brief_brand")
            brief_product = st.text_input("产品", placeholder="如: 新品口红", key="brief_product")
            brief_platform = st.selectbox(
                "平台",
                ["小红书", "抖音", "微博", "B站"],
                key="brief_platform",
            )
        with col2:
            brief_style = st.selectbox(
                "KOL风格",
                ["真实分享", "专业测评", "搞笑幽默", "高端时尚", "亲和日常"],
            )
            brief_goal = st.selectbox(
                "活动目标",
                ["种草", "曝光", "转化", "品牌宣传"],
            )
        
        # 内容要求
        col3, col4 = st.columns(2)
        with col3:
            key_messages = st.text_area("关键传播信息", placeholder="如: 新品上市、天然成分、持久显色")
            must_include = st.text_area("必须包含元素", placeholder="如: 产品特写、使用场景")
        with col4:
            forbidden = st.text_area("禁止事项", placeholder="如: 对比竞品、夸大宣传")
            target_audience = st.text_input("目标受众", placeholder="如: 18-25岁年轻女性")
        creative_skills = st.multiselect(
            "启用Skills（可选）",
            AVAILABLE_SKILLS,
            default=["agency-agents", "content-marketing", "brand-storytelling"],
            key="creative_skills",
        )
        
        if st.button("🎨 生成创意Brief", type="primary"):
            if not brief_brand or not brief_product:
                st.warning("请填写品牌和产品")
            else:
                with st.spinner("AI正在生成创意Brief..."):
                    try:
                        result = generate_creative_brief_with_llm(
                            brand=brief_brand,
                            product=brief_product,
                            platform=brief_platform,
                            kol_style=brief_style,
                            key_messages=[m.strip() for m in key_messages.split(",") if m.strip()],
                            must_include=[m.strip() for m in must_include.split(",") if m.strip()],
                            forbidden=[m.strip() for m in forbidden.split(",") if m.strip()],
                            target_audience=target_audience or "目标受众",
                            campaign_goal=brief_goal,
                            skills=creative_skills,
                        )
                        
                        st.success("✅ 创意Brief生成完成！")
                        
                        # 项目信息
                        info = result.get("project_info", {})
                        st.info(f"**{info.get('brand', '')}** | {info.get('product', '')} | {info.get('platform', '')}")
                        
                        # LLM生成的Brief
                        llm_brief = result.get("llm_brief", {})
                        
                        if "content_strategy" in llm_brief:
                            st.markdown("**📝 内容策略**")
                            cs = llm_brief["content_strategy"]
                            st.write(f"核心信息: {cs.get('core_message', 'N/A')}")
                            st.write(f"切入角度: {cs.get('content_angle', 'N/A')}")
                        
                        if "execution_guide" in llm_brief:
                            st.markdown("**🎯 执行指导**")
                            eg = llm_brief["execution_guide"]
                            st.write(f"开头钩子: {eg.get('opening_hook', 'N/A')}")
                            st.write(f"CTA设计: {eg.get('cta', 'N/A')}")

                        if result.get("kol_adaptation_guidelines"):
                            st.markdown("**👤 KOL调性适配指导**")
                            kg = result.get("kol_adaptation_guidelines", {})
                            st.write(f"调性对齐: {kg.get('style_alignment', 'N/A')}")
                            for d in kg.get("dos", [])[:2]:
                                st.write(f"- 建议: {d}")
                            for d in kg.get("donts", [])[:2]:
                                st.write(f"- 避免: {d}")

                        if result.get("applied_skills"):
                            st.write(f"🧩 已应用Skills: {', '.join(result.get('applied_skills', []))}")
                        
                        # 平台指南
                        st.markdown("**📱 平台规范**")
                        guidelines = result.get("platform_guidelines", {})
                        if "optimal_length" in guidelines:
                            st.write(f"最佳长度: {guidelines['optimal_length']}")
                        if "hashtag_strategy" in guidelines:
                            st.write(f"标签策略: {guidelines['hashtag_strategy']}")
                        
                        # 完整Brief
                        with st.expander("查看完整Brief"):
                            st.json(result)
                        
                        # 反馈入口
                        render_feedback_section("CreativePilot-创意Brief")
                    
                    except Exception as e:
                        st.error(f"❌ 生成失败: {str(e)}")
    
    with tab2:
        st.markdown("#### 生成内容模板")
        
        col1, col2 = st.columns(2)
        with col1:
            template_brand = st.text_input("品牌", placeholder="如: 花西子", key="template_brand")
            template_product = st.text_input("产品", placeholder="如: 口红", key="template_product")
        with col2:
            template_platform = st.selectbox(
                "平台",
                ["小红书", "抖音", "微博", "B站"],
                key="template_platform",
            )
            template_type = st.selectbox(
                "内容类型",
                ["product_review", "unboxing", "tutorial", "lifestyle"],
                format_func=lambda x: {
                    "product_review": "产品测评",
                    "unboxing": "开箱体验",
                    "tutorial": "教程分享",
                    "lifestyle": "生活方式",
                }.get(x, x),
            )
        
        key_points = st.text_area("核心卖点", placeholder="如: 显色持久、天然成分、包装精美")
        
        if st.button("📝 生成内容模板", type="primary"):
            if not template_brand or not template_product:
                st.warning("请填写品牌和产品")
            else:
                with st.spinner("AI正在生成内容模板..."):
                    try:
                        result = generate_content_with_llm(
                            template_type=template_type,
                            platform=template_platform,
                            brand=template_brand,
                            product=template_product,
                            key_points=[p.strip() for p in key_points.split(",") if p.strip()],
                            style="真实分享",
                        )
                        
                        st.success("✅ 内容模板生成完成！")
                        
                        st.markdown(f"**标题**: {result.get('title', '')}")
                        
                        st.markdown("**内容**")
                        st.text_area("", result.get('content', ''), height=400)
                        
                        st.markdown(f"**推荐标签**: {', '.join(result.get('hashtags', []))}")
                        
                        if result.get('posting_tips'):
                            st.info(f"💡 发布建议: {result['posting_tips']}")
                        
                        # 反馈入口
                        render_feedback_section("CreativePilot-内容模板")
                    
                    except Exception as e:
                        st.error(f"❌ 生成失败: {str(e)}")
    
    with tab3:
        st.markdown("#### 内容合规审核")
        
        review_brand = st.text_input("品牌", placeholder="如: 花西子", key="review_brand")
        review_platform = st.selectbox(
            "平台",
            ["小红书", "抖音", "微博", "B站"],
            key="review_platform",
        )
        review_content = st.text_area(
            "输入要审核的内容",
            height=300,
            placeholder="粘贴KOL提交的内容文案...",
        )
        
        with st.expander("审核要求"):
            review_must = st.text_area("必须包含", placeholder="如: 品牌名、产品特点")
            review_forbidden = st.text_area("禁止事项", placeholder="如: 竞品对比、绝对化用语")
        
        if st.button("🔍 开始审核", type="primary"):
            if not review_content:
                st.warning("请输入要审核的内容")
            else:
                with st.spinner("AI正在审核内容..."):
                    try:
                        result = review_content_with_llm(
                            content=review_content,
                            brand=review_brand or "品牌",
                            platform=review_platform,
                            requirements={
                                "must_include": [m.strip() for m in review_must.split(",") if m.strip()],
                                "forbidden": [m.strip() for m in review_forbidden.split(",") if m.strip()],
                                "tone": "真实分享",
                            },
                        )
                        
                        # 审核结果
                        passed = result.get("passed", False)
                        score = result.get("overall_score", 0) or result.get("score", 0)
                        
                        if passed:
                            st.success(f"✅ 审核通过 (得分: {score})")
                        else:
                            st.error(f"❌ 审核未通过 (得分: {score})")
                        
                        # 详细结果
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown("**问题**")
                            issues = result.get("critical_issues", []) or result.get("issues", [])
                            if issues:
                                for issue in issues:
                                    st.error(issue)
                            else:
                                st.write("无严重问题")
                        
                        with col_b:
                            st.markdown("**警告**")
                            warnings = result.get("warnings", [])
                            if warnings:
                                for warning in warnings:
                                    st.warning(warning)
                            else:
                                st.write("无警告")
                        
                        # 改进建议
                        st.markdown("**💡 改进建议**")
                        suggestions = result.get("improvement_suggestions", []) or result.get("suggestions", [])
                        for suggestion in suggestions:
                            st.write(f"- {suggestion}")
                        
                        # 详细评分
                        if "brand_alignment" in result:
                            with st.expander("详细评分"):
                                st.write(f"品牌契合度: {result['brand_alignment'].get('score', 'N/A')}")
                                st.write(f"合规检查: {result['compliance_check'].get('score', 'N/A')}")
                                st.write(f"内容质量: {result['content_quality'].get('score', 'N/A')}")
                        
                        # 反馈入口
                        render_feedback_section("CreativePilot-内容审核")
                    
                    except Exception as e:
                        st.error(f"❌ 审核失败: {str(e)}")


# ============================================
# Workflow 页面 - 端到端工作流
# ============================================
def render_workflow():
    st.markdown("### 🔄 端到端营销工作流")
    st.markdown("从Brief输入到完整执行方案，一站式自动化生成")
    
    # 工作流输入
    st.markdown("#### 📋 输入营销需求")
    
    workflow_brief = st.text_area(
        "请输入您的营销Brief",
        height=150,
        placeholder="例如：美妆品牌花西子新品口红上市，预算100万，目标种草18-25岁年轻女性，主要在小红书和抖音投放...",
        help="尽量详细地描述品牌、产品、预算、目标受众、投放平台等信息",
    )
    
    # 快速填充示例
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 加载美妆示例", use_container_width=True):
            st.session_state["workflow_brief"] = "美妆品牌花西子新品口红上市，预算100万，目标种草18-25岁年轻女性，主要在小红书和抖音投放，要求真实测评风格"
            st.rerun()
    with col2:
        if st.button("📱 加载3C示例", use_container_width=True):
            st.session_state["workflow_brief"] = "小米新款手机发布，预算200万，目标曝光和转化，主要投放B站和抖音，面向科技爱好者"
            st.rerun()
    with col3:
        if st.button("👶 加载母婴示例", use_container_width=True):
            st.session_state["workflow_brief"] = "母婴品牌贝亲新品奶瓶，预算50万，目标种草新手妈妈，主要在小红书投放，强调安全和品质"
            st.rerun()
    
    # 设置brief值
    if "workflow_brief" in st.session_state:
        workflow_brief = st.session_state["workflow_brief"]
    
    # 执行工作流
    if st.button("🚀 启动工作流", type="primary", use_container_width=True):
        if not workflow_brief:
            st.warning("请输入营销需求")
        else:
            # 导入工作流
            from agent_core.workflow.marketing_workflow import MarketingWorkflow
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 进度回调
            progress_data = {"current": 0, "total": 6}
            
            def on_progress(stage_name, result):
                progress_data["current"] += 1
                progress = progress_data["current"] / progress_data["total"]
                progress_bar.progress(progress)
                status_text.markdown(f"**当前阶段**: {stage_name}...")
            
            try:
                with st.spinner("工作流执行中，请稍候..."):
                    workflow = MarketingWorkflow()
                    context = workflow.run_with_progress(workflow_brief, progress_callback=on_progress)
                    
                progress_bar.empty()
                status_text.empty()
                
                st.success("✅ 工作流执行完成！")
                
                # 获取报告
                report_output = context.get_stage_output("report_generate")
                if report_output:
                    report = report_output.get("report", {})
                    
                    # 项目概览
                    st.markdown("---")
                    st.markdown("### 📊 项目概览")
                    
                    project = report.get("project_info", {})
                    cols = st.columns(4)
                    with cols[0]:
                        st.metric("品牌", project.get("brand", "N/A"))
                    with cols[1]:
                        st.metric("行业", project.get("industry", "N/A"))
                    with cols[2]:
                        st.metric("预算", f"{project.get('budget', 'N/A')}万")
                    with cols[3]:
                        st.metric("目标", project.get("goal", "N/A"))
                    
                    # 平台策略
                    st.markdown("### 📱 平台策略")
                    strategy = report.get("strategy", {})
                    platform_cols = st.columns(len(strategy.get("platform_strategy", [])))
                    for i, platform in enumerate(strategy.get("platform_strategy", [])):
                        with platform_cols[i]:
                            st.info(f"**{platform['name']}**\n\n"
                                   f"目标: {platform['goal']}\n\n"
                                   f"优先级: {platform['priority']}")
                    
                    # KOL推荐
                    st.markdown("### 👥 KOL推荐")
                    kol_rec = report.get("kol_recommendation", {})
                    combo = kol_rec.get("kol_combo", {})
                    
                    kol_cols = st.columns(2)
                    with kol_cols[0]:
                        st.markdown("**头部KOL**")
                        for kol in combo.get("recommended_head", [])[:3]:
                            st.write(f"- **{kol.get('name', 'N/A')}** ({kol.get('followers', 'N/A')}粉)")
                    with kol_cols[1]:
                        st.markdown("**腰部KOL**")
                        for kol in combo.get("recommended_waist", [])[:3]:
                            st.write(f"- **{kol.get('name', 'N/A')}** ({kol.get('followers', 'N/A')}粉)")
                    
                    # 建联话术预览
                    st.markdown("### ✉️ 建联话术预览")
                    outreach = report.get("outreach_plan", {})
                    messages = outreach.get("messages", [])
                    if messages:
                        with st.expander(f"查看 {len(messages)} 份建联话术"):
                            for msg in messages[:2]:  # 只显示前2个
                                st.markdown(f"**{msg.get('kol', 'KOL')}** ({msg.get('platform', '')})")
                                message_data = msg.get('message', {})
                                if isinstance(message_data, dict):
                                    st.write(f"主题: {message_data.get('subject', 'N/A')}")
                                st.divider()
                    
                    # 执行时间线
                    st.markdown("### 📅 执行时间线")
                    timeline = strategy.get("timeline", [])
                    for phase in timeline:
                        with st.expander(f"{phase['phase']} ({phase['duration']})"):
                            for activity in phase.get("activities", []):
                                st.write(f"- {activity}")
                    
                    # 下一步行动
                    st.markdown("### ✅ 下一步行动")
                    for step in report.get("next_steps", []):
                        st.checkbox(step, key=f"step_{step}")
                    
                    # 下载报告
                    st.markdown("---")
                    report_json = json.dumps(report, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="📥 下载完整报告 (JSON)",
                        data=report_json,
                        file_name=f"marketing_workflow_report_{int(time.time())}.json",
                        mime="application/json",
                        use_container_width=True,
                    )
            
            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ 工作流执行失败: {str(e)}")


# ============================================
# 工作流V2 - 带澄清机制和Eval记录
# ============================================
def render_workflow_v2():
    st.markdown("### 🔄 工作流 V2 (Beta)")
    st.markdown("智能澄清 + 完整记录 | 信息不完整时会主动询问")
    
    # 初始化session状态
    if "workflow_v2_state" not in st.session_state:
        st.session_state.workflow_v2_state = "input"  # input, clarification, running, complete
        st.session_state.workflow_v2_brief = ""
        st.session_state.workflow_v2_clarifications = {}
        st.session_state.workflow_v2_questions = []
        st.session_state.workflow_v2_result = None
        st.session_state.workflow_v2_record_id = None
    
    # 阶段1: 输入Brief
    if st.session_state.workflow_v2_state == "input":
        st.markdown("#### 📋 步骤1: 输入营销需求")
        
        brief = st.text_area(
            "请输入您的营销Brief",
            height=150,
            placeholder="例如：美妆品牌花西子新品口红上市，预算100万，目标种草18-25岁年轻女性...",
            key="v2_brief_input"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 分析需求", type="primary", use_container_width=True):
                if not brief:
                    st.warning("请输入营销需求")
                else:
                    # 分析需要澄清的问题
                    from agent_core.clarification.engine import ClarificationEngine
                    from agent_core.tools.strategy_iq import parse_brief
                    
                    clar_engine = ClarificationEngine()
                    parsed = parse_brief(brief)
                    session = clar_engine.analyze_brief(brief, parsed)
                    
                    st.session_state.workflow_v2_brief = brief
                    st.session_state.workflow_v2_questions = session.questions
                    
                    if session.questions:
                        st.session_state.workflow_v2_state = "clarification"
                    else:
                        st.session_state.workflow_v2_state = "running"
                    
                    st.rerun()
        
        with col2:
            if st.button("📊 查看示例", use_container_width=True):
                st.info("""
                **示例1**: Anker充电产品海外投放，美国市场，预算200万
                **示例2**: 花西子美妆新品国内推广，预算100万，目标种草年轻女性
                """)
    
    # 阶段2: 澄清问题
    elif st.session_state.workflow_v2_state == "clarification":
        st.markdown("#### ❓ 步骤2: 补充信息")
        st.info(f"检测到 **{len(st.session_state.workflow_v2_questions)}** 个需要澄清的问题")
        
        for i, q in enumerate(st.session_state.workflow_v2_questions):
            st.markdown(f"**问题 {i+1}**: {q.question}")
            st.caption(f"原因: {q.reason}")
            
            answer = st.text_input(
                f"您的回答_{i}",
                placeholder=f"请输入{q.field}...",
                key=f"clarification_{i}"
            )
            
            if answer:
                st.session_state.workflow_v2_clarifications[q.field] = answer
        
        if st.button("✅ 确认并继续", type="primary", use_container_width=True):
            st.session_state.workflow_v2_state = "running"
            st.rerun()
    
    # 阶段3: 执行工作流
    elif st.session_state.workflow_v2_state == "running":
        st.markdown("#### 🚀 步骤3: 生成方案")
        
        with st.spinner("AI正在生成完整营销方案..."):
            try:
                workflow = MarketingWorkflowV2()
                
                # 执行工作流
                context = workflow.run(
                    brief=st.session_state.workflow_v2_brief,
                    clarifications=st.session_state.workflow_v2_clarifications
                )
                
                # 保存结果
                st.session_state.workflow_v2_result = context
                st.session_state.workflow_v2_record_id = workflow.get_record_id()
                st.session_state.workflow_v2_state = "complete"
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ 执行失败: {str(e)}")
                st.session_state.workflow_v2_state = "input"
    
    # 阶段4: 显示结果
    elif st.session_state.workflow_v2_state == "complete":
        st.markdown("#### ✅ 方案生成完成")
        
        if st.session_state.workflow_v2_record_id:
            st.success(f"📊 记录ID: `{st.session_state.workflow_v2_record_id}`")
            st.caption("此ID可用于后续评估和改进")
        
        result = st.session_state.workflow_v2_result
        report_output = result.get_stage_output("report_generate") if result else None
        
        if report_output:
            report = report_output.get("report", {})
            
            # 显示项目信息
            project = report.get("project_info", {})
            cols = st.columns(4)
            with cols[0]:
                st.metric("品牌", project.get("brand", "N/A"))
            with cols[1]:
                st.metric("行业", project.get("industry", "N/A"))
            with cols[2]:
                st.metric("预算", f"{project.get('budget', 'N/A')}万")
            with cols[3]:
                st.metric("目标", project.get("goal", "N/A"))
            
            # 显示平台策略
            st.markdown("**📱 平台策略**")
            strategy = report.get("strategy", {})
            for p in strategy.get("platform_strategy", [])[:3]:
                st.write(f"• **{p['name']}** ({p['priority']}优先级) - {p['reasoning']}")
        
        # 反馈按钮
        st.divider()
        st.markdown("#### 💬 这个方案怎么样？")
        
        # 初始化反馈相关的 session state
        if "feedback_rating" not in st.session_state:
            st.session_state.feedback_rating = None
        if "feedback_submitted" not in st.session_state:
            st.session_state.feedback_submitted = False
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("👍 很有用", use_container_width=True, type="primary" if st.session_state.feedback_rating == 5 else "secondary"):
                st.session_state.feedback_rating = 5
                st.session_state.feedback_submitted = False
                st.rerun()
        with col2:
            if st.button("😐 一般", use_container_width=True, type="primary" if st.session_state.feedback_rating == 3 else "secondary"):
                st.session_state.feedback_rating = 3
                st.session_state.feedback_submitted = False
                st.rerun()
        with col3:
            if st.button("👎 需要改进", use_container_width=True, type="primary" if st.session_state.feedback_rating == 2 else "secondary"):
                st.session_state.feedback_rating = 2
                st.session_state.feedback_submitted = False
                st.rerun()
        
        # 如果用户选择了评分，显示详细反馈输入
        if st.session_state.feedback_rating is not None and not st.session_state.feedback_submitted:
            st.markdown("##### 📝 详细反馈（可选）")
            
            # 反馈文字输入
            user_feedback_text = st.text_area(
                "请输入您的意见或建议",
                placeholder="例如：这个方案的KOL推荐很准确，但是预算分配可以优化...",
                height=100,
                key="user_feedback_input"
            )
            
            # 问题标签（多选）
            issue_options = ["KOL推荐不准确", "平台选择不合适", "预算分配不合理", "内容方向不符合", "时间规划有问题", "其他问题"]
            selected_issues = st.multiselect(
                "发现的问题（可选）",
                options=issue_options,
                key="feedback_issues"
            )
            
            # 自定义问题输入
            custom_issue = st.text_input(
                "其他问题描述（可选）",
                placeholder="请描述您发现的其他问题...",
                key="custom_issue_input"
            )
            
            # 提交反馈按钮
            if st.button("📤 提交反馈", use_container_width=True, type="primary"):
                if st.session_state.workflow_v2_record_id:
                    recorder = get_eval_recorder()
                    
                    # 构建反馈文字
                    feedback_text = user_feedback_text if user_feedback_text else "用户未填写详细反馈"
                    
                    # 构建问题列表
                    issues_list = list(selected_issues) if selected_issues else []
                    if custom_issue:
                        issues_list.append(custom_issue)
                    
                    # 根据评分添加默认反馈
                    rating = st.session_state.feedback_rating
                    if rating == 5:
                        default_feedback = "用户认为方案很有用"
                    elif rating == 3:
                        default_feedback = "用户认为方案一般"
                    else:
                        default_feedback = "用户认为需要改进"
                    
                    # 合并反馈
                    final_feedback = f"{default_feedback}\n\n详细反馈：{feedback_text}" if user_feedback_text else default_feedback
                    
                    # 保存反馈
                    recorder.add_human_feedback(
                        st.session_state.workflow_v2_record_id,
                        rating=rating,
                        feedback=final_feedback,
                        issues=issues_list if issues_list else None
                    )
                    
                    st.session_state.feedback_submitted = True
                    
                    # 显示成功消息和存储路径
                    storage_path = recorder.storage_dir / f"{st.session_state.workflow_v2_record_id}.json"
                    
                    if rating >= 4:
                        st.success(f"✅ 感谢您的反馈！已保存到评估系统。")
                    elif rating == 3:
                        st.info(f"✅ 感谢您的反馈！我们会继续改进。")
                    else:
                        st.warning(f"✅ 感谢您的反馈！我们会重点改进。")
                    
                    st.caption(f"📁 存储位置：`{storage_path}`")
                    st.caption(f"🆔 记录ID：`{st.session_state.workflow_v2_record_id}`")
                    
                    st.rerun()
        
        # 重新开始
        if st.button("🔄 开始新的方案", use_container_width=True):
            st.session_state.workflow_v2_state = "input"
            st.session_state.workflow_v2_brief = ""
            st.session_state.workflow_v2_clarifications = {}
            st.session_state.workflow_v2_questions = []
            st.session_state.workflow_v2_result = None
            st.session_state.workflow_v2_record_id = None
            # 重置反馈状态
            st.session_state.feedback_rating = None
            st.session_state.feedback_submitted = False
            st.rerun()


def _wf3_json_default(key: str, data: dict[str, Any]) -> str:
    """Set initial JSON editor value only once for each workflow step key."""
    state_key = f"{key}_text"
    if state_key not in st.session_state:
        st.session_state[state_key] = json.dumps(data, ensure_ascii=False, indent=2)
    return st.session_state[state_key]


def _wf3_parse_json(text: str, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        return fallback


def render_workflow_studio():
    st.markdown("### 🧩 工作流（最新）")
    st.markdown("策略 → KOL搜索/组合 → 建联 → 创意，分步确认并自动串联，避免模块割裂。")
    st.caption("默认展示为可读卡片。JSON 仅用于高级模式和下载交付。")

    if "wf3_step" not in st.session_state:
        st.session_state.wf3_step = 1
        st.session_state.wf3_brief = ""
        st.session_state.wf3_skills = ["agency-agents", "content-marketing"]
        st.session_state.wf3_parsed = None
        st.session_state.wf3_strategy = None
        st.session_state.wf3_kol_combo = None
        st.session_state.wf3_selected_kols = []
        st.session_state.wf3_outreach = []
        st.session_state.wf3_creative = {}

    steps = ["1) Brief解析", "2) 策略确认", "3) KOL确认", "4) 建联确认", "5) 创意输出"]
    st.progress(st.session_state.wf3_step / len(steps))
    st.caption(f"当前进度：{steps[st.session_state.wf3_step - 1]}")

    st.session_state.wf3_brief = st.text_area(
        "营销Brief",
        value=st.session_state.wf3_brief,
        height=120,
        placeholder="例如：Nike 世界杯主题活动，预算100万，目标品牌曝光，产品Aero-Fit球服...",
        key="wf3_brief_input",
    )
    st.session_state.wf3_skills = st.multiselect(
        "工作流Skills（全链路生效）",
        AVAILABLE_SKILLS,
        default=st.session_state.wf3_skills,
        key="wf3_skills_selector",
    )
    advanced_mode = st.toggle("显示高级JSON编辑器", value=False, key="wf3_advanced_mode")

    # Step 1: Parse
    st.markdown("#### Step 1. Brief解析（确认基础信息）")
    col_parse_1, col_parse_2 = st.columns(2)
    with col_parse_1:
        if st.button("🔍 解析Brief", type="primary", use_container_width=True, key="wf3_parse_btn"):
            if not st.session_state.wf3_brief.strip():
                st.warning("请先输入Brief")
            else:
                parsed = parse_brief(st.session_state.wf3_brief)
                st.session_state.wf3_parsed = parsed
                st.session_state["wf3_parsed_json_text"] = json.dumps(parsed, ensure_ascii=False, indent=2)
    with col_parse_2:
        if st.button("🧹 重置工作台", use_container_width=True, key="wf3_reset_btn"):
            for k in [k for k in st.session_state.keys() if k.startswith("wf3_")]:
                del st.session_state[k]
            st.rerun()

    if st.session_state.wf3_parsed:
        parsed_text = _wf3_json_default("wf3_parsed_json", st.session_state.wf3_parsed)
        parsed_data = st.session_state.wf3_parsed
        info_cols = st.columns(4)
        with info_cols[0]:
            st.metric("品牌", parsed_data.get("brand", "未提及"))
        with info_cols[1]:
            st.metric("行业", parsed_data.get("industry", "未提及"))
        with info_cols[2]:
            st.metric("目标", parsed_data.get("goal", "未提及"))
        with info_cols[3]:
            st.metric("预算(万)", parsed_data.get("budget_amount", "未提及"))
        st.write(f"**目标受众**: {parsed_data.get('target_audience', '未提及')}")
        if parsed_data.get("key_messages"):
            st.write(f"**关键信息**: {' / '.join(parsed_data.get('key_messages', [])[:4])}")
        if parsed_data.get("preferred_platforms"):
            st.write(f"**优先平台**: {', '.join(parsed_data.get('preferred_platforms', []))}")
        if advanced_mode:
            parsed_text = st.text_area(
                "解析结果JSON（高级模式可编辑）",
                value=parsed_text,
                height=220,
                key="wf3_parsed_json_text",
            )
        else:
            with st.expander("查看原始JSON（只读）"):
                st.json(parsed_data)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 保存解析修改", use_container_width=True, key="wf3_save_parsed"):
                if advanced_mode:
                    st.session_state.wf3_parsed = _wf3_parse_json(parsed_text, st.session_state.wf3_parsed)
                    st.success("已保存解析修改")
                else:
                    st.info("当前为可视化模式，无需保存JSON。切换高级模式后可直接改JSON。")
        with col2:
            if st.button("✅ 确认并生成策略", use_container_width=True, key="wf3_confirm_to_strategy"):
                if advanced_mode:
                    st.session_state.wf3_parsed = _wf3_parse_json(parsed_text, st.session_state.wf3_parsed)
                input_data = dict(st.session_state.wf3_parsed)
                input_data["skills"] = st.session_state.wf3_skills
                st.session_state.wf3_strategy = generate_strategy(input_data)
                st.session_state["wf3_strategy_json_text"] = json.dumps(
                    st.session_state.wf3_strategy, ensure_ascii=False, indent=2
                )
                st.session_state.wf3_step = max(st.session_state.wf3_step, 2)
                st.rerun()

    # Step 2: Strategy confirm
    if st.session_state.wf3_strategy:
        st.markdown("#### Step 2. 策略确认（可视化确认后进入KOL）")
        strategy_text = _wf3_json_default("wf3_strategy_json", st.session_state.wf3_strategy)
        strategy_data = st.session_state.wf3_strategy
        st.markdown("**平台策略**")
        for p in strategy_data.get("platform_strategy", [])[:3]:
            st.write(f"- **{p.get('name', '平台')}**: {p.get('goal', '')}（{p.get('priority', '中')}优先级）")
        kol = strategy_data.get("kol_strategy", {})
        st.markdown("**KOL策略概览**")
        st.write(
            f"头部: {kol.get('head_kol', {}).get('count', '0')} | "
            f"腰部: {kol.get('waist_kol', {}).get('count', '0')} | "
            f"KOC: {kol.get('koc', {}).get('count', '0')}"
        )
        angle = strategy_data.get("communication_angle", {})
        if angle:
            st.write(f"**传播主张**: {angle.get('hero_message', 'N/A')}")
        if advanced_mode:
            strategy_text = st.text_area(
                "策略JSON（高级模式可编辑）",
                value=strategy_text,
                height=280,
                key="wf3_strategy_json_text",
            )
        else:
            with st.expander("查看策略原始JSON（只读）"):
                st.json(strategy_data)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 保存策略修改", use_container_width=True, key="wf3_save_strategy"):
                if advanced_mode:
                    st.session_state.wf3_strategy = _wf3_parse_json(strategy_text, st.session_state.wf3_strategy)
                    st.success("已保存策略修改")
                else:
                    st.info("当前为可视化模式，无需保存JSON。")
        with col2:
            if st.button("✅ 确认并生成KOL搜索+组合", use_container_width=True, key="wf3_to_kol"):
                if advanced_mode:
                    st.session_state.wf3_strategy = _wf3_parse_json(strategy_text, st.session_state.wf3_strategy)
                parsed = st.session_state.wf3_parsed or {}
                strategy = st.session_state.wf3_strategy or {}
                platforms = [p.get("name", "") for p in strategy.get("platform_strategy", []) if p.get("name")]
                if not platforms:
                    platforms = parsed.get("preferred_platforms", []) or ["小红书", "抖音"]
                category = parsed.get("industry", "通用")
                brand = parsed.get("brand", "品牌")
                goal = parsed.get("goal", "品牌曝光")
                budget = parsed.get("budget_amount", 50)
                try:
                    budget_num = float(budget)
                except Exception:
                    budget_num = 50.0

                search_pool = []
                for p in platforms[:2]:
                    search_pool.extend(
                        search_kols(
                            platform=p,
                            category=category,
                            brand=brand,
                            product="产品",
                            target_audience=parsed.get("target_audience", ""),
                            limit=8,
                        )
                    )
                combo = generate_kol_combo_with_llm(
                    budget=budget_num,
                    platforms=platforms[:2],
                    category=category,
                    brand=brand,
                    product="产品",
                    goal=goal,
                    skills=st.session_state.wf3_skills,
                )
                st.session_state.wf3_kol_pool = search_pool
                st.session_state.wf3_kol_combo = combo
                st.session_state["wf3_kol_combo_json_text"] = json.dumps(combo, ensure_ascii=False, indent=2)
                st.session_state.wf3_step = max(st.session_state.wf3_step, 3)
                st.rerun()

    # Step 3: KOL confirm
    if st.session_state.wf3_kol_combo:
        st.markdown("#### Step 3. KOL确认（人工干预筛选）")
        combo_text = _wf3_json_default("wf3_kol_combo_json", st.session_state.wf3_kol_combo)
        combo_data = st.session_state.wf3_kol_combo
        alloc = combo_data.get("budget_allocation", {})
        cols = st.columns(3)
        for i, key in enumerate(["head_kol", "waist_kol", "koc"]):
            with cols[i]:
                item = alloc.get(key, {})
                st.metric(
                    key.replace("_", " ").upper(),
                    f"{item.get('amount', 0)}万",
                    f"{item.get('percentage', 0)}%",
                )
        if advanced_mode:
            combo_text = st.text_area(
                "KOL组合JSON（高级模式可编辑）",
                value=combo_text,
                height=260,
                key="wf3_kol_combo_json_text",
            )
        else:
            with st.expander("查看KOL组合原始JSON（只读）"):
                st.json(combo_data)
        if st.button("💾 保存KOL组合修改", key="wf3_save_kol_combo"):
            if advanced_mode:
                st.session_state.wf3_kol_combo = _wf3_parse_json(combo_text, st.session_state.wf3_kol_combo)
                st.success("已保存KOL组合修改")
            else:
                st.info("当前为可视化模式，无需保存JSON。")

        combo = _wf3_parse_json(combo_text, st.session_state.wf3_kol_combo) if advanced_mode else st.session_state.wf3_kol_combo
        candidates = []
        for k in combo.get("recommended_head", []):
            candidates.append(("head", k))
        for k in combo.get("recommended_waist", []):
            candidates.append(("waist", k))
        for k in st.session_state.get("wf3_kol_pool", []):
            candidates.append(("search", k))

        unique = {}
        for t, k in candidates:
            name = k.get("name")
            if name and name not in unique:
                unique[name] = (t, k)
        options = list(unique.keys())
        default_pick = options[:5] if len(options) >= 5 else options
        selected_names = st.multiselect(
            "选择进入建联的KOL（支持人工干预）",
            options=options,
            default=st.session_state.get("wf3_selected_kol_names", default_pick),
            key="wf3_selected_kol_names",
        )
        st.session_state.wf3_selected_kols = [unique[n][1] for n in selected_names if n in unique]

        if st.button("✅ 确认KOL并生成建联话术", type="primary", key="wf3_to_outreach"):
            parsed = st.session_state.wf3_parsed or {}
            brand = parsed.get("brand", "品牌")
            product = "产品"
            msgs = []
            for kol in st.session_state.wf3_selected_kols[:8]:
                platform = kol.get("platform", "小红书")
                msg = generate_outreach_with_llm(
                    kol_name=kol.get("name", "KOL"),
                    kol_profile=kol,
                    brand=brand,
                    brand_intro=f"致力于提供优质{product}",
                    product=product,
                    platform=platform,
                    style="professional",
                    cooperation_type="内容合作",
                    budget_range="面议",
                    skills=st.session_state.wf3_skills,
                )
                msgs.append({"kol": kol.get("name", "KOL"), "platform": platform, "message": msg})
            st.session_state.wf3_outreach = msgs
            st.session_state.wf3_step = max(st.session_state.wf3_step, 4)
            st.rerun()

    # Step 4: Outreach confirm
    if st.session_state.wf3_outreach:
        st.markdown("#### Step 4. 建联确认（可改文案）")
        for i, row in enumerate(st.session_state.wf3_outreach):
            with st.expander(f"{i+1}. {row.get('kol')} ({row.get('platform')})", expanded=(i == 0)):
                msg = row.get("message", {}) or {}
                subj_key = f"wf3_outreach_subj_{i}"
                body_key = f"wf3_outreach_body_{i}"
                default_subj = msg.get("subject", "")
                default_body = msg.get("full_message", msg.get("body", ""))
                new_subj = st.text_input("主题", value=st.session_state.get(subj_key, default_subj), key=subj_key)
                new_body = st.text_area("正文", value=st.session_state.get(body_key, default_body), height=180, key=body_key)
                row["message"]["subject"] = new_subj
                row["message"]["full_message"] = new_body

        if st.button("✅ 确认建联并生成创意Brief", type="primary", key="wf3_to_creative"):
            parsed = st.session_state.wf3_parsed or {}
            strategy = st.session_state.wf3_strategy or {}
            platforms = [p.get("name", "") for p in strategy.get("platform_strategy", []) if p.get("name")]
            if not platforms:
                platforms = parsed.get("preferred_platforms", []) or ["小红书"]
            creative_map = {}
            for p in platforms[:2]:
                creative_map[p] = generate_creative_brief_with_llm(
                    brand=parsed.get("brand", "品牌"),
                    product="产品",
                    platform=p,
                    kol_style="真实分享",
                    key_messages=parsed.get("key_messages", []),
                    must_include=["产品展示", "使用体验"],
                    forbidden=["竞品对比", "绝对化用语"],
                    target_audience=parsed.get("target_audience", "目标受众"),
                    campaign_goal=parsed.get("goal", "品牌曝光"),
                    industry=parsed.get("industry", "通用"),
                    skills=st.session_state.wf3_skills,
                    kol_profile=(st.session_state.wf3_selected_kols[0] if st.session_state.wf3_selected_kols else {}),
                )
            st.session_state.wf3_creative = creative_map
            st.session_state.wf3_step = 5
            st.rerun()

    # Step 5: Final package
    if st.session_state.wf3_step >= 5 and st.session_state.wf3_creative:
        st.markdown("#### Step 5. 最终交付包（视觉展示 + JSON下载）")
        final_package = {
            "brief_parsed": st.session_state.wf3_parsed,
            "strategy": st.session_state.wf3_strategy,
            "kol_combo": st.session_state.wf3_kol_combo,
            "selected_kols": st.session_state.wf3_selected_kols,
            "outreach_messages": st.session_state.wf3_outreach,
            "creative_briefs": st.session_state.wf3_creative,
            "skills": st.session_state.wf3_skills,
        }
        final_text = json.dumps(final_package, ensure_ascii=False, indent=2)
        st.success("已完成全链路生成。你可以直接下载执行包，或展开查看原始JSON。")
        creative_map = st.session_state.wf3_creative
        st.markdown("**创意输出概览**")
        for platform, brief in creative_map.items():
            with st.expander(f"{platform} 创意Brief", expanded=False):
                info = brief.get("project_info", {})
                st.write(f"品牌: {info.get('brand', '')} | 产品: {info.get('product', '')}")
                llm_brief = brief.get("llm_brief", {})
                cs = llm_brief.get("content_strategy", {})
                if cs:
                    st.write(f"核心信息: {cs.get('core_message', 'N/A')}")
                    st.write(f"内容角度: {cs.get('content_angle', 'N/A')}")
                else:
                    st.write("已生成平台创意指导。")
        with st.expander("查看完整原始JSON"):
            st.json(final_package)
        st.download_button(
            "📥 下载一体化执行包(JSON)",
            data=final_text,
            file_name=f"workflow_v3_package_{int(time.time())}.json",
            mime="application/json",
            use_container_width=True,
        )


# ============================================
# 主函数
# ============================================
def main():
    # 初始化session state
    if "llm_configured" not in st.session_state:
        st.session_state.llm_configured = False
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "首页"
    
    # 侧边栏
    render_sidebar()
    
    # 主内容区
    tabs = {
        "首页": render_home,
        "工作流": render_workflow_studio,
        "StrategyIQ": render_strategy_iq,
        "MatchAI": render_match_ai,
        "ConnectBot": render_connect_bot,
        "CreativePilot": render_creative_pilot,
    }
    
    # 导航
    current_tab = st.session_state.get("current_tab", "首页")
    if current_tab in {"工作流工作台", "工作流V2"}:
        current_tab = "工作流"
        st.session_state.current_tab = "工作流"
    
    if current_tab in tabs:
        tabs[current_tab]()
    else:
        render_home()


if __name__ == "__main__":
    main()
