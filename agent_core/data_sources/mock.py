"""Mock 数据源 - 示例数据，用于开发和测试"""
from __future__ import annotations

from typing import Any, Optional


# 模拟 KOL 数据库 - 扩展版
SAMPLE_KOLS = {
    "小红书": [
        {"id": "xhs_001", "name": "@美妆达人小美", "followers": "50万", "engagement": "8.5%", "category": "美妆", "price": "3万", "city": "上海", "recent_posts": ["口红试色", "护肤日常"], "brand_history": ["花西子", "完美日记"], "avatar": "https://example.com/avatar1.jpg"},
        {"id": "xhs_002", "name": "@护肤分享师", "followers": "30万", "engagement": "9.2%", "category": "美妆", "price": "2万", "city": "杭州", "recent_posts": ["成分分析", "敏感肌护理"], "brand_history": ["薇诺娜", "理肤泉"], "avatar": "https://example.com/avatar2.jpg"},
        {"id": "xhs_003", "name": "@生活方式博主", "followers": "80万", "engagement": "6.8%", "category": "生活方式", "price": "5万", "city": "北京", "recent_posts": ["日常vlog", "好物分享"], "brand_history": ["无印良品", "宜家"], "avatar": "https://example.com/avatar3.jpg"},
        {"id": "xhs_004", "name": "@母婴博主乐乐", "followers": "40万", "engagement": "10.1%", "category": "母婴", "price": "2.5万", "city": "广州", "recent_posts": ["育儿经验", "宝宝辅食"], "brand_history": ["贝亲", "帮宝适"], "avatar": "https://example.com/avatar4.jpg"},
        {"id": "xhs_005", "name": "@数码测评君", "followers": "60万", "engagement": "7.5%", "category": "3C", "price": "4万", "city": "深圳", "recent_posts": ["手机评测", "数码开箱"], "brand_history": ["小米", "华为"], "avatar": "https://example.com/avatar5.jpg"},
        {"id": "xhs_006", "name": "@美食探店小能手", "followers": "25万", "engagement": "11.2%", "category": "美食", "price": "1.5万", "city": "成都", "recent_posts": ["探店日记", "美食测评"], "brand_history": ["喜茶", "海底捞"], "avatar": "https://example.com/avatar6.jpg"},
        {"id": "xhs_007", "name": "@旅行日记", "followers": "45万", "engagement": "8.8%", "category": "旅行", "price": "3.5万", "city": "北京", "recent_posts": ["云南游记", "民宿推荐"], "brand_history": ["携程", "Airbnb"], "avatar": "https://example.com/avatar7.jpg"},
    ],
    "抖音": [
        {"id": "dy_001", "name": "@时尚小姐姐", "followers": "200万", "engagement": "5.2%", "category": "时尚", "price": "15万", "city": "上海", "recent_posts": ["穿搭分享", "变装视频"], "brand_history": ["ZARA", "H&M"], "avatar": "https://example.com/avatar8.jpg"},
        {"id": "dy_002", "name": "@搞笑日常", "followers": "500万", "engagement": "4.8%", "category": "娱乐", "price": "30万", "city": "成都", "recent_posts": ["搞笑段子", "生活日常"], "brand_history": [], "avatar": "https://example.com/avatar9.jpg"},
        {"id": "dy_003", "name": "@美食探店", "followers": "150万", "engagement": "6.5%", "category": "美食", "price": "10万", "city": "重庆", "recent_posts": ["探店视频", "美食制作"], "brand_history": ["海底捞", "喜茶"], "avatar": "https://example.com/avatar10.jpg"},
        {"id": "dy_004", "name": "@科技大人", "followers": "300万", "engagement": "5.8%", "category": "3C", "price": "20万", "city": "北京", "recent_posts": ["科技评测", "产品开箱"], "brand_history": ["苹果", "三星"], "avatar": "https://example.com/avatar11.jpg"},
        {"id": "dy_005", "name": "@辣妈日记", "followers": "120万", "engagement": "7.2%", "category": "母婴", "price": "8万", "city": "杭州", "recent_posts": ["育儿日常", "母婴好物"], "brand_history": ["飞鹤", "好孩子"], "avatar": "https://example.com/avatar12.jpg"},
    ],
    "微博": [
        {"id": "wb_001", "name": "@时尚icon", "followers": "800万", "engagement": "3.5%", "category": "时尚", "price": "50万", "city": "北京", "recent_posts": ["时尚资讯", "穿搭分享"], "brand_history": ["LV", "Gucci"], "avatar": "https://example.com/avatar13.jpg"},
        {"id": "wb_002", "name": "@美妆教主", "followers": "600万", "engagement": "4.2%", "category": "美妆", "price": "40万", "city": "上海", "recent_posts": ["美妆教程", "产品推荐"], "brand_history": ["MAC", "雅诗兰黛"], "avatar": "https://example.com/avatar14.jpg"},
        {"id": "wb_003", "name": "@数码控", "followers": "400万", "engagement": "4.8%", "category": "3C", "price": "25万", "city": "深圳", "recent_posts": ["数码资讯", "评测分享"], "brand_history": ["华为", "OPPO"], "avatar": "https://example.com/avatar15.jpg"},
    ],
    "B站": [
        {"id": "bili_001", "name": "@测评实验室", "followers": "150万", "engagement": "12.5%", "category": "3C", "price": "12万", "city": "上海", "recent_posts": ["深度评测", "对比测试"], "brand_history": ["小米", "一加"], "avatar": "https://example.com/avatar16.jpg"},
        {"id": "bili_002", "name": "@生活分享官", "followers": "100万", "engagement": "10.2%", "category": "生活", "price": "8万", "city": "北京", "recent_posts": ["生活vlog", "好物分享"], "brand_history": ["网易严选", "小米有品"], "avatar": "https://example.com/avatar17.jpg"},
        {"id": "bili_003", "name": "@游戏解说", "followers": "300万", "engagement": "8.8%", "category": "游戏", "price": "18万", "city": "广州", "recent_posts": ["游戏评测", "直播回放"], "brand_history": ["腾讯游戏", "网易游戏"], "avatar": "https://example.com/avatar18.jpg"},
    ],
}


class MockSource:
    """Mock 数据源实现"""
    
    name = "mock"
    
    def search(
        self,
        platform: str,
        category: Optional[str] = None,
        min_followers: Optional[int] = None,
        max_followers: Optional[int] = None,
        min_engagement: Optional[float] = None,
        city: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """搜索 KOL - 从模拟数据筛选"""
        platform_kols = SAMPLE_KOLS.get(platform, [])
        results = []
        
        for kol in platform_kols:
            # 分类筛选
            if category and kol["category"] != category:
                continue
            
            # 城市筛选
            if city and city not in kol["city"]:
                continue
            
            # 粉丝量筛选
            followers_num = self._parse_followers(kol["followers"])
            if min_followers and followers_num < min_followers:
                continue
            if max_followers and followers_num > max_followers:
                continue
            
            # 互动率筛选
            engagement_val = kol.get("engagement", "0%")
            if isinstance(engagement_val, str):
                engagement = float(engagement_val.rstrip("%"))
            else:
                engagement = float(engagement_val)
            if min_engagement and engagement < min_engagement:
                continue
            
            results.append(kol)
        
        return results[:limit]
    
    def get_detail(self, kol_id: str) -> dict[str, Any]:
        """获取 KOL 详情"""
        for platform_kols in SAMPLE_KOLS.values():
            for kol in platform_kols:
                if kol["id"] == kol_id:
                    return kol
        return {}
    
    def get_contact(self, kol_id: str) -> dict[str, Any]:
        """获取联系方式（模拟）"""
        return {
            "kol_id": kol_id,
            "email": "example@kol.com",
            "wechat": "kol_wechat_123",
            "phone": "138****8888",
            "mcn": "示例MCN机构",
            "note": "此为模拟数据，真实环境需授权访问"
        }
    
    @staticmethod
    def _parse_followers(followers_str: str) -> int:
        """解析粉丝数量"""
        if "万" in followers_str:
            return int(float(followers_str.replace("万", "")) * 10000)
        elif "千" in followers_str:
            return int(float(followers_str.replace("千", "")) * 1000)
        else:
            return int(followers_str)


# 自动注册
from . import manager
manager.register(MockSource())
