"""
Flow 复楼 MA Agent - Perplexity 风格界面
智能社交营销AI代理平台
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

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
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================
# Perplexity 风格 CSS
# ============================================
st.markdown("""
<style>
    /* 全局样式重置 */
    .main .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 深色模式支持 */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-primary: #0d0d0d;
            --bg-secondary: #1a1a1a;
            --bg-input: #262626;
            --text-primary: #fafafa;
            --text-secondary: #a3a3a3;
            --border-color: #404040;
            --accent-color: #10a37f;
            --accent-hover: #0d8c6d;
        }
    }
    
    @media (prefers-color-scheme: light) {
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f9fafb;
            --bg-input: #ffffff;
            --text-primary: #111827;
            --text-secondary: #6b7280;
            --border-color: #e5e7eb;
            --accent-color: #10a37f;
            --accent-hover: #0d8c6d;
        }
    }
    
    /* 中央搜索区域 */
    .search-container {
        max-width: 700px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
    
    .brand-title {
        font-size: 2.5rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #10a37f 0%, #0d8c6d 50%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .brand-subtitle {
        text-align: center;
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* 搜索框样式 */
    .search-box {
        position: relative;
        background: var(--bg-input);
        border: 2px solid var(--border-color);
        border-radius: 1rem;
        padding: 1rem 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }
    
    .search-box:focus-within {
        border-color: var(--accent-color);
        box-shadow: 0 0 0 3px rgba(16, 163, 127, 0.1);
    }
    
    /* 回答区域 */
    .answer-container {
        max-width: 700px;
        margin: 0 auto;
        padding: 1.5rem;
    }
    
    .answer-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .answer-icon {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #10a37f, #6366f1);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1rem;
    }
    
    .answer-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    /* 内容卡片 */
    .content-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    
    .content-card h4 {
        margin-top: 0;
        margin-bottom: 0.75rem;
        color: var(--text-primary);
        font-size: 1rem;
        font-weight: 600;
    }
    
    /* 来源引用 */
    .source-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-color);
    }
    
    .source-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.75rem;
        background: var(--bg-input);
        border: 1px solid var(--border-color);
        border-radius: 1rem;
        font-size: 0.875rem;
        color: var(--text-secondary);
        text-decoration: none;
    }
    
    .source-tag:hover {
        border-color: var(--accent-color);
        color: var(--accent-color);
    }
    
    /* 相关问题 */
    .related-questions {
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 1px solid var(--border-color);
    }
    
    .related-questions h4 {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .question-chip {
        display: block;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        color: var(--text-primary);
        text-decoration: none;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .question-chip:hover {
        background: var(--bg-input);
        border-color: var(--accent-color);
    }
    
    /* 快捷操作 */
    .quick-actions {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        justify-content: center;
        margin-top: 1.5rem;
    }
    
    .quick-action-btn {
        padding: 0.5rem 1rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 2rem;
        font-size: 0.875rem;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .quick-action-btn:hover {
        background: var(--bg-input);
        border-color: var(--accent-color);
        color: var(--accent-color);
    }
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background: var(--bg-secondary);
    }
    
    /* 输入框覆盖 */
    .stTextArea textarea {
        border: none !important;
        background: transparent !important;
        font-size: 1rem !important;
        resize: none !important;
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: var(--accent-color) !important;
        color: white !important;
        border: none !important;
        border-radius: 0.5rem !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: var(--accent-hover) !important;
        transform: translateY(-1px);
    }
    
    /* 加载动画 */
    .loading-dots {
        display: flex;
        gap: 0.25rem;
        align-items: center;
        justify-content: center;
        padding: 2rem;
    }
    
    .loading-dots span {
        width: 8px;
        height: 8px;
        background: var(--accent-color);
        border-radius: 50%;
        animation: bounce 1.4s infinite ease-in-out both;
    }
    
    .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
    .loading-dots span:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
    
    /* 响应式 */
    @media (max-width: 768px) {
        .brand-title {
            font-size: 1.75rem;
        }
        .search-container {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# 会话状态初始化
# ============================================
def init_session_state():
    """初始化会话状态"""
    defaults = {
        "messages": [],
        "current_query": "",
        "is_processing": False,
        "show_result": False,
        "last_result": None,
        "mode": "auto",  # auto, strategy, kol, outreach, creative
        "sidebar_open": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================
# 侧边栏
# ============================================
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("### 🔮 Flow 复楼")
        st.caption("智能社交营销AI代理")
        
        st.divider()
        
        # 历史记录
        st.markdown("#### 最近查询")
        if st.session_state.messages:
            for msg in reversed(st.session_state.messages[-5:]):
                query = msg.get("query", "")[:30] + "..." if len(msg.get("query", "")) > 30 else msg.get("query", "")
                if st.button(f"📝 {query}", key=f"hist_{msg.get('id', '')}", use_container_width=True):
                    st.session_state.current_query = msg.get("query", "")
                    st.rerun()
        else:
            st.caption("暂无历史记录")
        
        st.divider()
        
        # 模式选择
        st.markdown("#### 专业模式")
        mode = st.radio(
            "选择模式",
            ["智能自动", "策略生成", "KOL匹配", "建联话术", "创意指导"],
            index=0,
            label_visibility="collapsed",
        )
        mode_map = {
            "智能自动": "auto",
            "策略生成": "strategy",
            "KOL匹配": "kol",
            "建联话术": "outreach",
            "创意指导": "creative",
        }
        st.session_state.mode = mode_map.get(mode, "auto")
        
        st.divider()
        
        # 设置
        with st.expander("⚙️ 设置"):
            if st.button("清除历史"):
                st.session_state.messages = []
                st.rerun()


# ============================================
# 搜索页面
# ============================================
def render_search_page():
    """渲染搜索主页"""
    # 品牌标题
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="brand-title">Flow 复楼</h1>', unsafe_allow_html=True)
    st.markdown('<p class="brand-subtitle">智能社交营销AI代理 - 输入您的营销需求</p>', unsafe_allow_html=True)
    
    # 搜索框
    query = st.text_area(
        "",
        placeholder="例如：美妆品牌花西子新品口红上市，预算100万，目标种草18-25岁年轻女性...",
        height=100,
        key="search_input",
        label_visibility="collapsed",
    )
    
    # 快捷操作
    st.markdown('<div class="quick-actions">', unsafe_allow_html=True)
    cols = st.columns(4)
    quick_prompts = [
        ("💄 美妆策略", "完美日记新品粉底液推广，预算50万"),
        ("📱 3C数码", "Anker充电宝海外推广，针对年轻用户"),
        ("👶 母婴产品", "贝亲婴儿奶瓶新品上市，目标宝妈群体"),
        ("🍔 快消食品", "元气森林夏季营销，预算200万"),
    ]
    for col, (label, prompt) in zip(cols, quick_prompts):
        with col:
            if st.button(label, key=f"quick_{label}", use_container_width=True):
                st.session_state.current_query = prompt
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 提交按钮
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔮 生成营销方案", use_container_width=True, type="primary", disabled=not query):
            st.session_state.current_query = query
            st.session_state.is_processing = True
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================
# 结果展示
# ============================================
def render_result():
    """渲染回答结果"""
    query = st.session_state.current_query
    
    st.markdown('<div class="answer-container">', unsafe_allow_html=True)
    
    # 回答头部
    st.markdown(f"""
    <div class="answer-header">
        <div class="answer-icon">🔮</div>
        <div class="answer-title">营销方案</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 显示问题
    st.caption(f"Q: {query}")
    
    # 处理中状态
    if st.session_state.is_processing:
        st.markdown("""
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
        <p style="text-align: center; color: var(--text-secondary);">AI正在分析需求并生成方案...</p>
        """, unsafe_allow_html=True)
        
        # 模拟处理
        process_query(query)
        st.session_state.is_processing = False
        st.session_state.show_result = True
        st.rerun()
    
    # 显示结果
    elif st.session_state.show_result and st.session_state.last_result:
        result = st.session_state.last_result
        
        # 根据结果显示不同内容
        if result.get("type") == "strategy":
            render_strategy_result(result["data"])
        elif result.get("type") == "kol":
            render_kol_result(result["data"])
        elif result.get("type") == "outreach":
            render_outreach_result(result["data"])
        elif result.get("type") == "creative":
            render_creative_result(result["data"])
        
        # 来源引用
        render_sources()
        
        # 相关问题
        render_related_questions()
    
    st.markdown('</div>', unsafe_allow_html=True)


def process_query(query: str):
    """处理查询"""
    mode = st.session_state.mode
    
    try:
        if mode == "auto":
            # 智能模式：解析brief并生成完整策略
            brief_data = parse_brief(query)
            strategy = generate_strategy(brief_data)
            st.session_state.last_result = {
                "type": "strategy",
                "data": {
                    "brief": brief_data,
                    "strategy": strategy,
                }
            }
        elif mode == "strategy":
            brief_data = parse_brief(query)
            strategy = generate_strategy(brief_data)
            st.session_state.last_result = {
                "type": "strategy",
                "data": {
                    "brief": brief_data,
                    "strategy": strategy,
                }
            }
        elif mode == "kol":
            kols = search_kols(
                platform="小红书",
                category="美妆",
                brand=query[:20],
                limit=5,
            )
            st.session_state.last_result = {
                "type": "kol",
                "data": kols,
            }
        elif mode == "outreach":
            result = generate_outreach_with_llm(
                kol_name="KOL",
                brand=query[:20],
                product="产品",
                platform="小红书",
            )
            st.session_state.last_result = {
                "type": "outreach",
                "data": result,
            }
        else:  # creative
            result = generate_creative_brief_with_llm(
                brand=query[:20],
                product="产品",
                platform="小红书",
            )
            st.session_state.last_result = {
                "type": "creative",
                "data": result,
            }
        
        # 保存到历史
        st.session_state.messages.append({
            "id": str(time.time()),
            "query": query,
            "type": mode,
        })
        
    except Exception as e:
        st.session_state.last_result = {
            "type": "error",
            "data": {"error": str(e)},
        }


def render_strategy_result(data: dict):
    """渲染策略结果"""
    brief = data.get("brief", {})
    strategy = data.get("strategy", {})
    
    # Brief解析结果
    st.markdown("""
    <div class="content-card">
        <h4>📋 需求解析</h4>
    </div>
    """, unsafe_allow_html=True)
    
    cols = st.columns(4)
    with cols[0]:
        st.metric("品牌", brief.get("brand", "未知"))
    with cols[1]:
        st.metric("行业", brief.get("industry", "未知"))
    with cols[2]:
        st.metric("预算", brief.get("budget", "未知"))
    with cols[3]:
        st.metric("目标", brief.get("goal", "未知")[:10])
    
    # 平台策略
    st.markdown("""
    <div class="content-card">
        <h4>📱 平台策略</h4>
    </div>
    """, unsafe_allow_html=True)
    
    for platform in strategy.get("platform_strategy", [])[:3]:
        with st.expander(f"{platform['name']} ({platform['priority']}优先级)"):
            st.write(platform.get("reasoning", ""))
            st.caption(f"内容形式: {platform.get('content_format', '')}")
    
    # KOL策略
    kol = strategy.get("kol_strategy", {})
    st.markdown("""
    <div class="content-card">
        <h4>👥 KOL组合策略</h4>
    </div>
    """, unsafe_allow_html=True)
    
    cols = st.columns(3)
    with cols[0]:
        head = kol.get("head_kol", {})
        st.metric("头部KOL", head.get("count", "0"))
        st.caption(f"预算占比: {head.get('budget_ratio', 0)*100:.0f}%")
        # 显示推荐KOL
        for k in head.get("recommended_kols", [])[:2]:
            st.write(f"• {k['name']} ({k['followers']})")
    
    with cols[1]:
        waist = kol.get("waist_kol", {})
        st.metric("腰部KOL", waist.get("count", "0"))
        st.caption(f"预算占比: {waist.get('budget_ratio', 0)*100:.0f}%")
        for k in waist.get("recommended_kols", [])[:2]:
            st.write(f"• {k['name']}")
    
    with cols[2]:
        koc = kol.get("koc", {})
        st.metric("KOC", koc.get("count", "0"))
        st.caption(f"预算占比: {koc.get('budget_ratio', 0)*100:.0f}%")
    
    # 执行指导
    exec_guide = strategy.get("execution_guide", {})
    if exec_guide:
        st.markdown("""
        <div class="content-card">
            <h4>🎯 执行指导</h4>
        </div>
        """, unsafe_allow_html=True)
        
        for phase in exec_guide.get("phases", [])[:3]:
            with st.expander(f"{phase['phase']} ({phase['duration']})"):
                for action in phase.get("key_actions", []):
                    st.write(f"- {action}")


def render_kol_result(data: list):
    """渲染KOL结果"""
    st.markdown(f"""
    <div class="content-card">
        <h4>🔍 找到 {len(data)} 位匹配KOL</h4>
    </div>
    """, unsafe_allow_html=True)
    
    for kol in data:
        with st.container():
            cols = st.columns([2, 2, 1])
            with cols[0]:
                st.write(f"**{kol.get('name', '未知')}**")
                st.caption(f"📍 {kol.get('city', '未知')} | 🏷️ {kol.get('category', '未知')}")
            with cols[1]:
                st.write(f"👥 {kol.get('followers', 'N/A')} 粉丝")
                st.write(f"📈 互动率: {kol.get('engagement', 'N/A')}")
            with cols[2]:
                st.metric("匹配度", f"{kol.get('match_score', 0)}%")
            st.divider()


def render_outreach_result(data: dict):
    """渲染建联话术结果"""
    st.markdown("""
    <div class="content-card">
        <h4>✉️ 建联话术</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.text_input("主题", data.get("subject", ""), key="outreach_subject_result")
    st.text_area("正文", data.get("full_message", data.get("body", "")), height=300, key="outreach_body_result")
    
    if data.get("value_proposition"):
        st.info(f"💡 价值主张: {data['value_proposition']}")


def render_creative_result(data: dict):
    """渲染创意结果"""
    st.markdown("""
    <div class="content-card">
        <h4>🎨 创意Brief</h4>
    </div>
    """, unsafe_allow_html=True)
    
    llm_brief = data.get("llm_brief", {})
    if "content_strategy" in llm_brief:
        cs = llm_brief["content_strategy"]
        st.write(f"**核心信息**: {cs.get('core_message', 'N/A')}")
        st.write(f"**切入角度**: {cs.get('content_angle', 'N/A')}")
    
    if "execution_guide" in llm_brief:
        eg = llm_brief["execution_guide"]
        st.write(f"**开头钩子**: {eg.get('opening_hook', 'N/A')}")
        st.write(f"**CTA设计**: {eg.get('cta', 'N/A')}")


def render_sources():
    """渲染来源"""
    st.markdown("""
    <div class="source-list">
        <span style="color: var(--text-secondary); font-size: 0.875rem;">来源：</span>
        <a href="#" class="source-tag">📊 平台数据</a>
        <a href="#" class="source-tag">👥 KOL库</a>
        <a href="#" class="source-tag">📈 行业报告</a>
    </div>
    """, unsafe_allow_html=True)


def render_related_questions():
    """渲染相关问题"""
    st.markdown("""
    <div class="related-questions">
        <h4>相关问题</h4>
    </div>
    """, unsafe_allow_html=True)
    
    related = [
        "如何优化这个方案的预算分配？",
        "推荐哪些头部KOL合作？",
        "这个方案的预期ROI是多少？",
        "如何设计内容投放的时间线？",
    ]
    
    for q in related:
        if st.button(q, key=f"related_{q[:20]}", use_container_width=True):
            st.session_state.current_query = q
            st.session_state.is_processing = True
            st.rerun()


# ============================================
# 主函数
# ============================================
def main():
    """主函数"""
    init_session_state()
    render_sidebar()
    
    # 根据状态渲染不同页面
    if st.session_state.current_query and (st.session_state.is_processing or st.session_state.show_result):
        render_result()
        
        # 返回按钮
        if st.button("← 返回搜索", key="back_btn"):
            st.session_state.current_query = ""
            st.session_state.show_result = False
            st.session_state.last_result = None
            st.rerun()
    else:
        render_search_page()


if __name__ == "__main__":
    main()
