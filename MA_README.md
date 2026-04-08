# Flow 复楼 MA Agent

> AI驱动的全链路社交营销智能代理

## 🚀 快速开始

### 方式1: Web界面 (推荐) ✨

```bash
cd /Users/chaihao/LLM/ma

# 启动Web服务
./run_web.sh

# 或直接使用streamlit
python3 -m streamlit run streamlit_app.py
```

然后在浏览器打开: **http://localhost:8501**

#### 端到端工作流

Web界面新增 **「🔄 工作流」** 页面，输入Brief即可一键生成完整营销方案：

```
Brief输入 → 策略生成 → KOL匹配 → 建联话术 → 创意Brief → 完整报告
```

### 方式2: 命令行

```bash
cd /Users/chaihao/LLM/ma

# 查看状态
python3 cli.py status

# 查看帮助
python3 cli.py help

# 端到端工作流 (一键生成完整方案)
python3 cli.py workflow "美妆品牌花西子新品口红上市，预算100万，目标种草年轻女性"

# 交互式工作流
python3 cli.py workflow-i
```

## 🌐 Web界面功能

| 页面 | 功能描述 |
|------|----------|
| **🏠 首页** | 四大模块概览、快速入口 |
| **🧠 StrategyIQ** | Brief智能解析、营销策略生成、预算分配 |
| **🎯 MatchAI** | KOL智能搜索、匹配度分析、组合推荐 |
| **🤝 ConnectBot** | 个性化建联话术、跟进策略、谈判建议 |
| **✨ CreativePilot** | 创意Brief生成、内容模板、合规审核 |

### Web界面特点

- 🎨 **美观设计** - 渐变色彩、卡片式布局
- 📊 **数据可视化** - 图表展示预算分配、匹配度
- 📱 **响应式布局** - 支持桌面和移动端
- ⚙️ **侧边栏配置** - 快速切换LLM提供商
- 🔄 **实时预览** - 即时生成、即时查看

## 📋 命令行使用

### StrategyIQ - 策略生成

```bash
# 解析brief
python3 cli.py strategy-parse "美妆品牌新品上市预算100万目标种草"

# 生成策略
python3 cli.py strategy-generate industry=美妆 budget=高 goal=种草
```

### MatchAI - KOL匹配

```bash
# 搜索KOL
python3 cli.py kol-search platform=小红书 category=美妆 min_engagement=5 limit=5

# 生成KOL组合
python3 cli.py kol-combo budget=100 platforms=小红书,抖音 category=美妆
```

### ConnectBot - 智能建联

```bash
# 生成建联话术
python3 cli.py outreach kol_name=美妆达人 brand=花西子 platform=小红书 style=professional

# 生成跟进话术
python3 cli.py follow-up kol_name=美妆达人 brand=花西子 days_since=5

# 谈判建议
python3 cli.py negotiation kol_price=5 budget=4 kol_engagement=8.5 kol_followers=500000
```

### CreativePilot - 创意指导

```bash
# 生成创意Brief
python3 cli.py creative-brief brand=花西子 product=散粉 platform=小红书

# 生成内容模板
python3 cli.py content-template brand=花西子 product=散粉 platform=小红书 template_type=product_review

# 审核内容
python3 cli.py content-review content="这产品真好用！" brand=花西子 platform=小红书
```

## 🏗️ 项目结构

```
ma/
├── agent_core/
│   ├── llm/                    # LLM客户端
│   ├── cli/                    # CLI入口
│   ├── commands/               # Commands实现
│   ├── tools/                  # Tools实现
│   ├── models/                 # 数据模型
│   └── runtime/                # 运行时
├── streamlit_app.py            # ✅ Web界面主文件
├── run_web.sh                  # ✅ Web启动脚本
├── requirements.txt            # ✅ 依赖文件
├── cli.py                      # CLI入口
└── ...
```

## 🎯 核心模块

| 模块 | 功能 |
|------|------|
| StrategyIQ | Brief解析、策略生成 |
| MatchAI | KOL搜索、匹配、分析 |
| ConnectBot | 话术生成、跟进、谈判 |
| CreativePilot | 创意Brief、内容模板、审核 |

## 🖥️ Web界面截图预览

```
┌─────────────────────────────────────────────────────────────┐
│  🚀 Flow 复楼                    [首页] [策略] [KOL] [建联]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🧠 StrategyIQ        🎯 MatchAI                     │   │
│  │  策略理解与生成        KOL智能匹配                    │   │
│  │                                                     │   │
│  │  🤝 ConnectBot        ✨ CreativePilot               │   │
│  │  智能建联              创意内容指导                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ⚙️ 系统配置 (侧边栏)                                │   │
│  │  • LLM提供商: [DeepSeek ▼]                          │   │
│  │  • API Key:   [••••••••]                            │   │
│  │  • 模型:      [deepseek-chat ▼]                     │   │
│  │  [🔄 应用配置]                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📚 更多文档

- [Agent定义文档](./ma-social-marketing-agent.md)
- [项目配置](../AGENTS.md)
- [项目概览](../PROJECT_OVERVIEW.md)
