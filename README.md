# Flow 复楼 —— 智能社交营销AI代理 (MA)

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> **每一分投放都应该有复利**

Flow 复楼是一个AI驱动的全链路社交营销智能代理平台，专为广告公司、品牌营销团队打造，致力于解决社交营销中"KOL匹配难、执行效果难、完成目标难"的三难核心痛点。

---

## 🎯 核心定位

**"AI驱动的全链路社交营销智能合伙人"**

AgentSocial 不仅是一个工具，更是一个可自主执行、持续学习、具备策略思维的"AI营销合伙人"。

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Flow 复楼 - MA Agent                      │
│                    (智能社交营销AI代理)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │  StrategyIQ  │ │   MatchAI    │ │  ConnectBot  │        │
│  │  策略理解与   │ │ KOL/KOC智能  │ │  智能建联    │        │
│  │  生成引擎    │ │   匹配系统    │ │  协作代理    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐                                          │
│  │ CreativePilot│                                          │
│  │ 创意内容指导  │                                          │
│  │   助手      │                                          │
│  └──────────────┘                                          │
├─────────────────────────────────────────────────────────────┤
│              可调用 Agency Agents 专业网络                   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │  Marketing │ │    Sales   │ │  Product   │              │
│  │   Division │ │   Division │ │  Division  │              │
│  └────────────┘ └────────────┘ └────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 激活MA Agent

```bash
"激活 Flow 复楼营销代理"
"Activate the MA Social Marketing Agent"
"启动 Flow 复楼"
```

### 使用四大核心能力

#### 1. StrategyIQ - 策略理解与生成

```bash
"使用 StrategyIQ 解析这个brief并生成策略提案"
"基于我们的品牌目标和预算，生成一个抖音+小红书的营销方案"
```

#### 2. MatchAI - KOL智能匹配

```bash
"使用 MatchAI 为我的美妆品牌推荐合适的KOL"
"筛选粉丝量在10-50万之间、互动率>5%的生活方式类KOL"
```

#### 3. ConnectBot - 智能建联

```bash
"使用 ConnectBot 生成给KOL的邀约话术"
"自动跟进这些待联系的KOL，并追踪响应状态"
```

#### 4. CreativePilot - 创意内容指导

```bash
"使用 CreativePilot 为这次合作生成内容Brief"
"审核这条KOL提交的内容是否符合品牌规范"
```

---

## 📂 文件结构

```
ma/
├── README.md                      # 本文件 - 项目介绍和快速开始
├── ma-social-marketing-agent.md   # 主Agent定义文件（详细能力说明）
├── AGENTS.md                      # 配置指南和故障排查
├── QUICKSTART.md                  # 快速启动指南（5分钟上手）
└── examples/                      # 示例用例 (待补充)
```

### 文档导航

| 文档 | 内容 |
|------|------|
| [README.md](./README.md) | 项目概览、快速开始、系统架构 |
| [ma-social-marketing-agent.md](./ma-social-marketing-agent.md) | **详细能力文档**：四大模块、API参考、扩展开发指南 |
| [AGENTS.md](./AGENTS.md) | 配置指南、Agent集成、故障排查 |
| [QUICKSTART.md](./QUICKSTART.md) | 5分钟快速上手指南 |

---

## 🔗 依赖的 Agency Agents

本Agent可以调用以下专业Agent的能力：

### Marketing Division

- `marketing-xiaohongshu-specialist` - 小红书专家
- `marketing-douyin-strategist` - 抖音策略师
- `marketing-kuaishou-strategist` - 快手策略师
- `marketing-weibo-strategist` - 微博策略师
- `marketing-bilibili-content-strategist` - B站内容策略师
- `marketing-livestream-commerce-coach` - 直播电商教练
- `marketing-short-video-editing-coach` - 短视频剪辑教练
- `marketing-content-creator` - 内容创作者
- `marketing-growth-hacker` - 增长黑客
- `marketing-seo-specialist` - SEO专家
- `marketing-social-media-strategist` - 社交媒体策略师
- `marketing-private-domain-operator` - 私域运营专家

### Sales Division

- `sales-outbound-strategist` - 外联策略师
- `sales-discovery-coach` - 需求发现教练
- `sales-deal-strategist` - 交易策略师

### 调用示例

```bash
"调用 marketing-xiaohongshu-specialist 来制定小红书KOL筛选标准"
"Activate sales-outbound-strategist to craft KOL outreach templates"
"组建团队: marketing-douyin-strategist + marketing-content-creator 来制定抖音内容策略"
```

---

## 🎯 典型使用场景

### 场景1: 完整项目执行

**输入:**
```bash
"我是一家美妆品牌，预算100万，想在小红书和抖音做新品上市推广，
目标是获得5000万曝光和10万互动。请帮我制定完整的执行方案。"
```

**MA-Agent将:**
1. 解析需求，生成整体策略
2. 筛选并推荐KOL组合
3. 生成建联话术并执行
4. 提供内容创意指导
5. 输出完整项目方案

### 场景2: KOL筛选

**输入:**
```bash
"帮我筛选适合母婴品牌的腰部KOL，要求：
- 粉丝量：20-100万
- 互动率：>6%
- 平台：小红书+抖音
- 地域：一二线城市
- 预算：单个KOL 2-5万"
```

### 场景3: 内容审核

**输入:**
```bash
"审核这条KOL提交的脚本是否符合我们的品牌调性和合规要求"
```

---

## 📊 核心指标

| 指标 | 目标 |
|------|------|
| KOL建联效率 | 提升5倍+ |
| 策略生成时间 | 从2天缩短至2小时 |
| KOL匹配精准度 | >90% |
| 平均ROI | >1:5 |

---

## 🛠️ 技术栈

- **AI核心**: NLP语义理解 + 策略推理模型
- **数据接入**: 微博、小红书、抖音、B站、快手等平台API
- **知识库**: 行业案例库 + KOL画像数据库
- **工作流**: 自主决策引擎 + 人机协同模式

---

## 📝 更新日志

### v1.0.0 (2026-04-03)

- 基于 init_agent 模板重构文档结构
- 完善四大核心能力模块
- 添加扩展开发指南
- 集成Agency Agents专业网络

### v0.9.0 (2026-04-01)

- 初始版本发布
- 四大核心能力模块

---

## 🤝 贡献指南

欢迎提交Issue和PR来改进这个Agent。

---

## 📄 许可证

MIT License

---

**Flow 复楼** —— 让每一分投放都有复利
