# Flow 复楼 MA Agent - 项目概览

基于 `init_agent` 模板开发的智能社交营销AI代理系统，已接入多LLM提供商支持。

## 🚀 快速开始

### 方式1: Web界面 (推荐) 🌐

```bash
cd /Users/chaihao/LLM/ma

# 启动Web服务
./run_web.sh

# 浏览器打开: http://localhost:8501
```

### 方式2: 命令行

```bash
cd /Users/chaihao/LLM/ma

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置你的API密钥

# 查看状态
python3 cli.py status

# 生成策略
python3 cli.py strategy-generate industry=美妆 budget=高 goal=种草
```

## 📁 项目结构

```
ma/                                # 项目根目录
├── agent_core/
│   ├── llm/                      # ✅ LLM客户端
│   ├── workflow/                 # ✅ 工作流引擎 (新增)
│   │   ├── __init__.py
│   │   ├── engine.py            # 工作流引擎核心
│   │   └── marketing_workflow.py # 端到端营销工作流
│   ├── commands/                 # Commands实现
│   ├── tools/                    # Tools实现
│   ├── models/                   # 数据模型
│   └── ...
├── streamlit_app.py              # ✅ Streamlit Web界面
├── run_web.sh                    # ✅ Web启动脚本
├── requirements.txt              # ✅ Python依赖
├── .agent/spec/                  # 配置文件
├── .env.example                  # 环境变量模板
└── cli.py                        # CLI入口
```

## 🌐 Web界面

### 启动方式

```bash
# 方式1: 使用启动脚本
./run_web.sh

# 方式2: 直接启动
python3 -m streamlit run streamlit_app.py
```

### Web界面功能

| 页面 | 功能描述 |
|------|----------|
| **🏠 首页** | 四大模块概览、快速入口 |
| **🔄 工作流** | **端到端自动化** - 输入Brief一键生成完整方案 |
| **🧠 StrategyIQ** | Brief解析、策略生成 |
| **🎯 MatchAI** | KOL搜索、匹配度分析 |
| **🤝 ConnectBot** | 建联话术、跟进策略 |
| **✨ CreativePilot** | 创意Brief、内容审核 |

### 🔄 端到端工作流

**工作流程**: Brief输入 → 策略生成 → KOL匹配 → 建联话术 → 创意Brief → 完整报告

```bash
# CLI使用
python3 cli.py workflow "美妆品牌花西子新品口红上市，预算100万..."

# Web使用
# 进入「🔄 工作流」页面 → 输入Brief → 点击启动
```

### Web界面特点

- 🎨 **美观设计** - 渐变色彩、卡片式布局
- 📊 **数据可视化** - 图表展示、匹配度指标
- 📱 **响应式布局** - 支持桌面和移动端
- ⚙️ **侧边栏配置** - 快速切换LLM提供商
- 🔄 **实时预览** - 即时生成、即时查看

## 🤖 LLM 集成

### 支持的提供商

| 提供商 | 配置方式 | 特点 |
|--------|----------|------|
| **DeepSeek** | `DEEPSEEK_API_KEY` | 国产模型，中文优秀，性价比高 |
| **OpenAI** | `OPENAI_API_KEY` | GPT-4o系列，JSON模式支持好 |
| **Claude** | `ANTHROPIC_API_KEY` | 中文表现优秀 |
| **Kimi** | `KIMI_API_KEY` | 国产模型，性价比高 |
| **Minimax** | `MINIMAX_API_KEY` | 需GROUP_ID |
| **Mock** | 无需配置 | 测试用 |

### 配置示例

```bash
# 编辑 .env 文件
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_MODEL=deepseek-chat
```

## 📊 代码统计

| 模块 | 文件 | 行数 | 说明 |
|------|------|------|------|
| LLM Client | 3个 | ~600行 | 多提供商支持 |
| StrategyIQ | 1个 | ~350行 | LLM+规则双引擎 |
| MatchAI | 1个 | ~400行 | LLM智能分析 |
| ConnectBot | 1个 | ~400行 | LLM话术生成 |
| CreativePilot | 1个 | ~350行 | LLM创意指导 |
| **Streamlit UI** | **1个** | **~1000行** | **完整Web界面** |

## 🧪 测试验证

### Web界面测试

```bash
# 启动Web服务
cd /Users/chaihao/LLM/ma
./run_web.sh

# 测试功能
# 1. 侧边栏配置LLM
# 2. StrategyIQ - Brief解析
# 3. MatchAI - KOL搜索
# 4. ConnectBot - 生成话术
# 5. CreativePilot - 内容审核
```

### CLI测试

```bash
# 测试LLM模块
python3 -c "from agent_core.llm import get_llm_client; \
    llm = get_llm_client(provider='mock'); \
    print(llm.complete('测试'))"

# 测试策略生成
python3 cli.py strategy-generate industry=美妆 budget=高 goal=种草

# 测试KOL搜索
python3 cli.py kol-search platform=小红书 category=美妆 limit=3
```

## 📝 版本历史

### v1.3.0 (2026-04-04)
- ✅ **端到端工作流自动化**
- ✅ 工作流引擎 (6阶段流水线)
- ✅ `workflow` CLI命令
- ✅ Web界面「🔄 工作流」页面
- ✅ 一键生成完整营销方案

### v1.2.0 (2026-04-04)
- ✅ Streamlit Web界面
- ✅ 四大模块Web化
- ✅ 侧边栏LLM配置

### v1.1.0 (2026-04-04)
- ✅ 多LLM提供商支持
- ✅ 四大模块LLM化

### v1.0.0 (2026-04-03)
- 基础架构实现

## 🎯 下一步建议

1. **接入真实数据** - 替换模拟KOL数据库
2. **用户系统** - 添加登录和多用户支持
3. **数据持久化** - 保存策略和KOL数据
4. **高级分析** - ROI预测、效果追踪

---

**Flow 复楼** —— 让每一分投放都有复利 🚀
