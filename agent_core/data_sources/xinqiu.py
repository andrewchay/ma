"""星图数据源适配器 - 示例实现"""
from __future__ import annotations

import os
from typing import Any, Optional

import requests


class XinqiuSource:
    """抖音星图 API 数据源
    
    文档: https://www.xingtu.cn/
    覆盖: 抖音（官方平台，数据最权威）
    """
    
    name = "xinqiu"
    
    BASE_URL = "https://api.xingtu.cn/openapi"
    
    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        self.app_id = app_id or os.getenv("XINGQIU_APP_ID")
        self.app_secret = app_secret or os.getenv("XINGQIU_APP_SECRET")
        self.access_token = None
        
        if not (self.app_id and self.app_secret):
            raise ValueError("XINGQIU_APP_ID and XINGQIU_APP_SECRET not configured")
    
    def _get_access_token(self) -> str:
        """获取访问令牌"""
        if self.access_token:
            return self.access_token
        
        # 示例：实际请参考星图官方文档
        url = f"{self.BASE_URL}/oauth2/access_token"
        params = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
            "grant_type": "client_credentials"
        }
        
        try:
            response = requests.post(url, json=params, timeout=30)
            data = response.json()
            self.access_token = data.get("access_token")
            return self.access_token
        except Exception as e:
            raise ValueError(f"Failed to get access token: {e}")
    
    def _request(self, endpoint: str, params: dict) -> dict:
        """发送 API 请求"""
        token = self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[Xingqiu API Error] {e}")
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
        
        星图只支持抖音平台
        """
        if platform != "抖音":
            return []
        
        params = {
            "page_size": limit,
        }
        
        if category:
            params["tag"] = category
        if min_followers:
            params["fans_min"] = min_followers
        if max_followers:
            params["fans_max"] = max_followers
        if keywords:
            params["keyword"] = keywords[0]  # 星图通常只支持单个关键词
        
        # 示例：实际使用时替换为真实 endpoint
        # data = self._request("v1/douyin/author/search", params)
        
        print(f"[Xingqiu] 搜索 {platform} - 请在 agent_core/data_sources/xinqiu.py 中实现真实 API 调用")
        return []
    
    def get_detail(self, kol_id: str) -> dict[str, Any]:
        """获取 KOL 详情"""
        print("[Xingqiu] get_detail 需接入真实 API")
        return {}
    
    def get_contact(self, kol_id: str) -> dict[str, Any]:
        """获取联系方式（需通过平台下单）"""
        print("[Xingqiu] 联系方式需通过星图平台下单获取")
        return {}
    
    def get_quote(self, kol_id: str) -> dict[str, Any]:
        """获取报价信息"""
        # 星图可以获取达人的任务报价
        print("[Xingqiu] get_quote 需接入真实 API")
        return {}


# 自动注册（需配置 API Key）
# from . import manager
# if os.getenv("XINGQIU_APP_ID"):
#     manager.register(XinqiuSource())
