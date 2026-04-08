"""新榜数据源适配器 - 示例实现"""
from __future__ import annotations

import os
from typing import Any, Optional

import requests


class NewrankSource:
    """新榜 API 数据源
    
    文档: https://www.newrank.cn/
    覆盖: 微信/微博/抖音/快手/B站/小红书
    """
    
    name = "newrank"
    
    BASE_URL = "https://api.newrank.cn/api"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NEWRANK_API_KEY")
        if not self.api_key:
            raise ValueError("NEWRANK_API_KEY not configured")
    
    def _request(self, endpoint: str, params: dict) -> dict:
        """发送 API 请求"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 注意：这是示例代码，实际 API 请参考新榜官方文档
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[Newrank API Error] {e}")
            return {"error": str(e)}
    
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
        """搜索 KOL
        
        注意：这是示例实现，需要替换为真实的新榜 API 调用
        """
        # 平台映射
        platform_map = {
            "小红书": "xiaohongshu",
            "抖音": "douyin",
            "微博": "weibo",
            "B站": "bilibili",
            "快手": "kuaishou",
        }
        
        api_platform = platform_map.get(platform, platform)
        
        params = {
            "platform": api_platform,
            "pageSize": limit,
        }
        
        if category:
            params["category"] = category
        if min_followers:
            params["fansMin"] = min_followers
        if max_followers:
            params["fansMax"] = max_followers
        if keywords:
            params["keywords"] = ",".join(keywords)
        
        # 示例：实际使用时取消注释并替换为真实 endpoint
        # data = self._request("kol/search", params)
        # return self._normalize_data(data.get("data", []), platform)
        
        # 临时返回空列表，提示用户配置
        print(f"[Newrank] 搜索 {platform} - 请在 agent_core/data_sources/newrank.py 中实现真实 API 调用")
        return []
    
    def _normalize_data(self, raw_data: list[dict], platform: str) -> list[dict]:
        """标准化数据格式"""
        normalized = []
        
        for item in raw_data:
            normalized.append({
                "id": item.get("accountId", ""),
                "name": item.get("accountName", ""),
                "platform": platform,
                "followers": self._format_followers(item.get("fansCount", 0)),
                "engagement": f"{item.get('interactRate', 0)}%",
                "category": item.get("category", "未知"),
                "price": "待询",  # 价格通常需要单独获取
                "city": item.get("city", ""),
                "avatar": item.get("headImg", ""),
                "recent_posts": [],
                "brand_history": [],
                "raw_data": item,  # 保留原始数据
            })
        
        return normalized
    
    @staticmethod
    def _format_followers(count: int) -> str:
        """格式化粉丝数"""
        if count >= 10000:
            return f"{count / 10000:.1f}万"
        return str(count)
    
    def get_detail(self, kol_id: str) -> dict[str, Any]:
        """获取 KOL 详情"""
        # 示例：实际使用时替换为真实 API
        # return self._request(f"kol/detail/{kol_id}", {})
        print("[Newrank] get_detail 需接入真实 API")
        return {}
    
    def get_contact(self, kol_id: str) -> dict[str, Any]:
        """获取联系方式（需商务授权）"""
        print("[Newrank] get_contact 需商务授权")
        return {}


# 自动注册（需配置 API Key）
# from . import manager
# if os.getenv("NEWRANK_API_KEY"):
#     manager.register(NewrankSource())
