# Flow 复楼 MA Agent - 配置指南

> 本文档面向后续接入本项目的 AI Agent，提供配置信息和快速参考。

---

## Agent 信息

```yaml
name: Flow 复楼 - 智能社交营销AI代理
alias: MA (Marketing Agent)
location: /Users/chaihao/LLM/ma/
main_file: ma-social-marketing-agent.md
version: 1.0.0
division: marketing
capabilities:
  - strategy_generation
  - kol_matching
  - outreach_automation
  - creative_guidance
  - multi_platform
```

---

## 快速开始

### 1. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置你的API密钥
vim .env
```

### 2. 安装依赖 (可选)

```bash
# 如果使用OpenAI
pip install openai

# 如果使用Claude
pip install anthropic

# 如果使用Kimi (基于OpenAI SDK)
pip install openai

# 如果使用Minimax
pip install requests
```

### 3. 运行Agent

```bash
# 查看状态
python3 cli.py status

# 生成策略 (使用LLM)
python3 cli.py strategy-generate industry=美妆 budget=高 goal=种草

# 搜索KOL
python3 cli.py kol-search platform=小红书 category=美妆 limit=5

# 生成建联话术
python3 cli.py outreach kol_name=小美 brand=花西子 platform=小红书
```

---

## LLM 配置

### 支持的提供商

| 提供商 | 环境变量 | 默认模型 | 备注 |
|--------|----------|----------|------|
| OpenAI | `OPENAI_API_KEY` | gpt-4o-mini | 推荐，JSON模式支持好 |
| Claude | `ANTHROPIC_API_KEY` | claude-3-sonnet | 中文表现优秀 |
| **Kimi** | `KIMI_API_KEY` | **kimi-k2.5** (推荐) | 国产模型，中文优秀，性价比高 |
| Minimax | `MINIMAX_API_KEY` | abab6.5-chat | 需配置GROUP_ID |
| Mock | 无需配置 | - | 测试用，返回模拟数据 |

### 切换提供商

```bash
# 方式1: 环境变量
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-xxx

# 方式2: 修改 .env 文件
LLM_PROVIDER=kimi
KIMI_API_KEY=your_key_here
```

### 测试LLM连接

```python
from agent_core.llm import get_llm_client

# 使用默认配置
llm = get_llm_client()
print(llm.complete("你好，请介绍一下自己", json_mode=False))

# 指定提供商
llm = get_llm_client(provider="openai")
```

---

## CLI 使用

### 基础命令

```bash
python3 cli.py status      # 查看状态
python3 cli.py help        # 显示帮助
```

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
python3 cli.py kol-search platform=小红书 category=美妆 limit=5

# 生成KOL组合
python3 cli.py kol-combo budget=100 platforms=小红书,抖音 category=美妆
```

### ConnectBot - 智能建联

```bash
# 生成建联话术
python3 cli.py outreach kol_name=小美 brand=花西子 platform=小红书 style=professional

# 生成跟进话术
python3 cli.py follow-up kol_name=小美 brand=花西子 days_since=5

# 谈判建议
python3 cli.py negotiation kol_price=5 budget=4 kol_engagement=8.5 kol_followers=500000
```

### CreativePilot - 创意指导

```bash
# 生成创意Brief
python3 cli.py creative-brief brand=花西子 product=散粉 platform=小红书

# 审核内容
python3 cli.py content-review content="这产品真好用！" brand=花西子 platform=小红书
```

---

## 激活指令 (自然语言)

### 方式1: 直接激活

```bash
"激活 Flow 复楼营销代理"
"Activate MA Social Marketing Agent"
"启动 Flow 复楼"
```

### 方式2: 指定具体能力

```bash
"使用 StrategyIQ 生成营销方案"
"调用 MatchAI 筛选KOL"
"启动 ConnectBot 进行建联"
"使用 CreativePilot 审核内容"
```

### 方式3: 调用专业Agent

```bash
"调用 marketing-xiaohongshu-specialist 来..."
"Activate marketing-douyin-strategist to..."
```

---

## 文件结构

```
ma/
├── agent_core/
│   ├── llm/                    # LLM客户端 (新增)
│   │   ├── __init__.py
│   │   ├── client.py          # LLMClient主类
│   │   └── providers.py       # 多提供商支持
│   ├── commands/              # Commands实现
│   ├── tools/                 # Tools实现 (已接入LLM)
│   ├── models/                # 数据模型
│   └── ...
├── .agent/spec/               # 配置文件
├── .env.example               # 环境变量模板
└── cli.py                     # CLI入口
```

---

## 故障排查

### LLM连接失败

**问题**: `Error: No API key provided`

**解决**: 
```bash
# 检查环境变量
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your_key

# 或复制并编辑 .env 文件
cp .env.example .env
```

### 依赖缺失

**问题**: `ImportError: openai package not installed`

**解决**:
```bash
pip install openai
# 或
pip install anthropic
```

### 模型响应异常

**问题**: LLM返回格式不正确

**解决**: 
- 检查API密钥是否有效
- 尝试切换其他提供商
- 使用 `LLM_PROVIDER=mock` 测试基础功能

---

## 扩展开发

### 添加新的LLM提供商

1. 在 `agent_core/llm/providers.py` 创建新Provider类
2. 在 `LLMClient.PROVIDERS` 中注册

### 自定义提示词

修改各模块中的 `system_prompt` 变量即可自定义LLM行为。

### Brief 解析字段变更规范

为避免再次出现"前端有字段、后端解析器不返回"的脱节问题，任何 Brief 解析字段的增删改必须遵循以下流程：

1. **更新数据模型**  
   先修改 `agent_core/models/brief.py` 中的 `BriefParseResult`，它是前后端字段的**唯一数据源**。

2. **更新解析逻辑**  
   修改 `agent_core/tools/strategy_iq.py`：
   - LLM prompt 的 JSON schema 通过 `BriefParseResult.get_prompt_schema_text()` 生成，不要手写
   - 规则兜底解析 `_rule_based_parse` 构建完 dict 后，必须用 `BriefParseResult.model_validate(result).model_dump()` 返回，确保字段不缺

3. **更新 Web API 映射**  
   修改 `web_api.py` 的 `/api/analyze-brief`，确保新字段被显式映射到前端返回结构。

4. **更新前端消费**  
   修改 `web/index.html` 中的：
   - `autoFillForm` — 把新字段映射到对应表单元素
   - `showExtractedPreview` — 在提取信息预览中展示新字段

5. **运行同步测试**  
   必须执行并确保通过：
   ```bash
   python3 -m unittest tests.test_brief_schema_sync -v
   ```
   测试会检查：解析器返回完整性、后端 API 字段引用、前端字段消费三处是否一致。

---

**文档版本**: 1.2.0  
**更新日期**: 2026-04-15  
**更新内容**: 接入LLM支持 (OpenAI/Claude/Kimi/Minimax)；增加 Brief 解析字段变更规范与同步测试
