"""API版本管理模块

提供API版本路由和版本控制功能。
"""
from fastapi import APIRouter
from typing import Dict, Optional


class APIVersionManager:
    """API版本管理器
    
    管理API版本路由和版本控制。
    """
    
    def __init__(self):
        self.versions: Dict[str, APIRouter] = {}
        self.current_version = "v1"
    
    def register_version(self, version: str, router: APIRouter) -> None:
        """注册API版本路由
        
        Args:
            version: 版本号（如v1, v2）
            router: 路由器
        """
        self.versions[version] = router
    
    def get_version_router(self, version: Optional[str] = None) -> APIRouter:
        """获取指定版本的路由器
        
        Args:
            version: 版本号，默认使用当前版本
        
        Returns:
            路由器
        """
        version = version or self.current_version
        return self.versions.get(version, self.versions[self.current_version])
    
    def set_current_version(self, version: str) -> None:
        """设置当前版本
        
        Args:
            version: 版本号
        """
        if version not in self.versions:
            raise ValueError(f"版本 {version} 不存在")
        self.current_version = version


# 全局版本管理器
api_version_manager = APIVersionManager()


def create_versioned_router(version: str) -> APIRouter:
    """创建版本化路由器
    
    Args:
        version: 版本号（如v1, v2）
    
    Returns:
        APIRouter实例
    """
    router = APIRouter(prefix=f"/api/{version}")
    api_version_manager.register_version(version, router)
    return router


def get_current_version() -> str:
    """获取当前API版本
    
    Returns:
        当前版本号
    """
    return api_version_manager.current_version
