"""KOL 数据源适配器 - 统一接口支持多平台数据接入"""
from __future__ import annotations

from typing import Any, Optional, Protocol


class KOLDataSource(Protocol):
    """KOL 数据源接口协议"""
    
    name: str
    
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
        """搜索 KOL"""
        ...
    
    def get_detail(self, kol_id: str) -> dict[str, Any]:
        """获取 KOL 详情"""
        ...
    
    def get_contact(self, kol_id: str) -> dict[str, Any]:
        """获取 KOL 联系方式（需授权）"""
        ...


class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self):
        self._sources: dict[str, KOLDataSource] = {}
    
    def register(self, source: KOLDataSource) -> None:
        """注册数据源"""
        self._sources[source.name] = source
    
    def get(self, name: str) -> Optional[KOLDataSource]:
        """获取数据源"""
        return self._sources.get(name)
    
    def search_all(
        self,
        platform: str,
        **kwargs
    ) -> list[dict[str, Any]]:
        """跨所有数据源搜索"""
        results = []
        for source in self._sources.values():
            try:
                data = source.search(platform, **kwargs)
                for item in data:
                    item["_source"] = source.name
                results.extend(data)
            except Exception as e:
                print(f"[{source.name}] 搜索失败: {e}")
        return results


# 全局管理器实例
manager = DataSourceManager()


from .mock import MockSource

__all__ = [
    "KOLDataSource",
    "DataSourceManager", 
    "manager",
    "MockSource",
]
