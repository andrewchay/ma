# KOL 数据源接入指南

本文档介绍如何接入真实达人数据 API，实现真正的 KOL 挖掘功能。

---

## 📊 当前状态

### ✅ 已具备的能力
- **智能匹配算法**：基于 LLM 分析 KOL 与品牌的匹配度
- **多维筛选**：平台、分类、粉丝量、互动率、城市等
- **组合推荐**：头部+腰部+KOC 的预算分配策略
- **风险评估**：基于 AI 的合作风险分析

### ⚠️ 数据现状
- **当前**：使用 `SAMPLE_KOLS` 模拟数据（约 30 个示例 KOL）
- **目标**：接入真实达人数据 API（百万级 KOL 库）

---

## 🔌 支持的数据源

| 数据源 | 覆盖平台 | 特点 | 接入难度 |
|--------|----------|------|----------|
| **新榜** | 全平台 | 数据聚合最全 | ⭐⭐⭐ |
| **抖音星图** | 抖音 | 官方数据最权威 | ⭐⭐⭐⭐ |
| **小红书蒲公英** | 小红书 | 官方合作平台 | ⭐⭐⭐ |
| **飞瓜数据** | 抖音/快手 | 电商转化数据强 | ⭐⭐⭐ |
| **蝉妈妈** | 抖音/快手 | 直播带货数据 | ⭐⭐⭐ |

---

## 🚀 快速接入

### 步骤 1：获取 API 密钥

以**新榜**为例：
1. 访问 [新榜官网](https://www.newrank.cn/)
2. 注册企业账号并完成认证
3. 申请 API 接入权限
4. 获取 `NEWRANK_API_KEY`

### 步骤 2：配置环境变量

```bash
# 编辑 .env 文件
cp .env.example .env
vim .env

# 添加你的 API Key
NEWRANK_API_KEY=your_newrank_api_key_here
KOL_DATA_SOURCE=newrank  # 切换为真实数据源
```

### 步骤 3：启用数据源

编辑 `agent_core/data_sources/__init__.py`，取消对应数据源的注册注释：

```python
from .newrank import NewrankSource
from . import manager

# 自动注册（需配置 API Key）
if os.getenv("NEWRANK_API_KEY"):
    manager.register(NewrankSource())
```

### 步骤 4：验证接入

```python
# 测试脚本
from agent_core.data_sources import manager

# 查看已注册的数据源
print(manager._sources.keys())

# 搜索 KOL
results = manager.search_all(
    platform="小红书",
    category="美妆",
    min_followers=100000,
    limit=10
)

for kol in results:
    print(f"{kol['name']} - {kol['followers']}")
```

---

## 🔧 自定义数据源

如需接入自己的 KOL 数据库或 API：

### 方法 1：创建自定义数据源

```python
# agent_core/data_sources/my_api.py
from agent_core.data_sources import manager

class MyCustomSource:
    name = "my_api"
    
    def search(self, platform, category=None, **kwargs):
        # 调用你的 API
        response = requests.get("https://your-api.com/kol/search", params={
            "platform": platform,
            "category": category,
            ...
        })
        return response.json()
    
    def get_detail(self, kol_id):
        # 获取详情
        pass
    
    def get_contact(self, kol_id):
        # 获取联系方式
        pass

# 注册
manager.register(MyCustomSource())
```

### 方法 2：直接修改 MatchAI

编辑 `agent_core/tools/match_ai.py`，修改 `search_kols` 函数：

```python
def search_kols(...):
    # 替换为你的数据获取逻辑
    # 例如：查询数据库、调用内部 API 等
    results = your_data_source.search(...)
    
    # 使用 LLM 进行智能分析
    analyzed_results = []
    for kol in results:
        analysis = analyze_kol_with_llm(kol, brand, product, target_audience)
        analyzed_results.append({**kol, **analysis})
    
    return analyzed_results
```

---

## 📚 数据结构

### 标准 KOL 数据格式

```python
{
    "id": "唯一标识",
    "name": "@账号名",
    "platform": "小红书/抖音/微博/B站",
    "followers": "50万",  # 或数字
    "engagement": "8.5%",  # 互动率
    "category": "美妆",
    "price": "3万",  # 报价
    "city": "上海",
    "avatar": "头像URL",
    "recent_posts": ["最近内容1", "最近内容2"],
    "brand_history": ["合作品牌1", "合作品牌2"],
    "_source": "数据来源",  # 可选
}
```

### LLM 分析结果格式

```python
{
    "match_score": 85,  # 匹配度 0-100
    "match_reasoning": "匹配理由",
    "audience_overlap": "目标受众重叠度",
    "content_fit": "内容风格契合度",
    "brand_alignment": "品牌调性匹配度",
    "risk_factors": ["风险1", "风险2"],
    "advantages": ["优势1", "优势2"],
    "estimated_roi": "预估ROI 1:5-1:8",
    "cooperation_suggestions": "合作建议"
}
```

---

## 💡 使用示例

### CLI 命令

```bash
# 搜索 KOL
python3 cli.py kol-search platform=小红书 category=美妆 min_engagement=8 limit=5

# 生成 KOL 组合
python3 cli.py kol-combo budget=100 platforms=小红书,抖音 category=美妆
```

### Python API

```python
from agent_core.tools.match_ai import search_kols

# 搜索美妆 KOL
results = search_kols(
    platform="小红书",
    category="美妆",
    min_followers="10万",
    min_engagement=8.0,
    brand="花西子",
    product="散粉",
    target_audience="18-25岁女性",
    limit=10
)

for kol in results:
    print(f"{kol['name']} - 匹配度: {kol['match_score']}%")
    print(f"  预估ROI: {kol['estimated_roi']}")
    print(f"  风险: {kol['risk_factors']}")
```

---

## 🔍 数据源对比

### 新榜 API
- **优点**：覆盖平台最全，数据维度丰富
- **缺点**：价格较高，需要企业认证
- **适用**：多平台综合投放

### 抖音星图
- **优点**：官方数据，转化链路完整
- **缺点**：仅支持抖音
- **适用**：抖音专项投放

### 小红书蒲公英
- **优点**：官方合作，交易安全
- **缺点**：仅支持小红书，需品牌认证
- **适用**：小红书种草营销

### 飞瓜/蝉妈妈
- **优点**：电商数据强，直播分析深
- **缺点**：需额外付费
- **适用**：带货转化导向

---

## ❓ 常见问题

### Q: 接入 API 需要多少钱？
A: 
- 新榜：约 2-10万/年（根据调用量）
- 星图/蒲公英：免费（但交易抽成）
- 飞瓜/蝉妈妈：约 1-5万/年

### Q: 个人开发者能申请吗？
A: 
- 新榜：需要企业资质
- 星图：需要企业资质
- 飞瓜/蝉妈妈：个人可申请基础版

### Q: 没有 API 怎么办？
A: 可以使用以下替代方案：
1. **爬虫抓取**（需遵守平台规则）
2. **第三方数据服务**（如灰豚、考古加）
3. **自建 KOL 库**（从公开渠道收集）
4. **对接 MCN 机构**（获取内部数据）

---

## 📞 支持

如需帮助接入特定数据源，请提供：
1. 目标平台（抖音/小红书/微博等）
2. 数据需求（粉丝量/互动率/报价等）
3. 预算范围
4. 已有 API 或需推荐供应商
