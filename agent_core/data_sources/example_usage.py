"""KOL 数据源使用示例"""
from __future__ import annotations

from agent_core.data_sources import manager


def search_kol_example():
    """搜索 KOL 示例"""
    
    # 方法1: 使用特定数据源
    # source = manager.get("newrank")
    # if source:
    #     results = source.search(
    #         platform="小红书",
    #         category="美妆",
    #         min_followers=100000,
    #         limit=10
    #     )
    
    # 方法2: 跨所有数据源搜索
    results = manager.search_all(
        platform="小红书",
        category="美妆",
        min_followers=100000,
        limit=10
    )
    
    for kol in results:
        print(f"{kol['name']} - {kol['followers']}粉 - 来自: {kol.get('_source', 'unknown')}")
    
    return results


def register_new_data_source():
    """注册新的数据源示例"""
    
    from agent_core.data_sources import KOLDataSource, manager
    
    class MyCustomSource:
        """自定义数据源"""
        
        name = "my_source"
        
        def search(self, platform: str, **kwargs):
            # 实现你的搜索逻辑
            # 例如：调用你自己的 API 或数据库
            return []
        
        def get_detail(self, kol_id: str):
            return {}
        
        def get_contact(self, kol_id: str):
            return {}
    
    # 注册到管理器
    manager.register(MyCustomSource())


def integrate_with_match_ai():
    """与 MatchAI 集成示例"""
    
    from agent_core.data_sources import manager
    
    def search_kols_with_real_data(
        platform: str,
        category: str = None,
        min_followers: str = None,
        **kwargs
    ):
        """使用真实数据源搜索 KOL"""
        
        # 解析粉丝数
        min_followers_num = None
        if min_followers:
            if "万" in min_followers:
                min_followers_num = int(float(min_followers.replace("万", "")) * 10000)
            else:
                min_followers_num = int(min_followers)
        
        # 从数据源搜索
        results = manager.search_all(
            platform=platform,
            category=category,
            min_followers=min_followers_num,
            limit=kwargs.get("limit", 10)
        )
        
        return results
    
    return search_kols_with_real_data


if __name__ == "__main__":
    print("=== KOL 数据源使用示例 ===\n")
    
    # 查看已注册的数据源
    print("已注册的数据源:")
    for name in manager._sources.keys():
        print(f"  - {name}")
    
    print("\n搜索示例:")
    results = search_kol_example()
    print(f"找到 {len(results)} 个 KOL")
