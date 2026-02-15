"""
Mock工具模块

提供统一的Mock创建工具，简化测试中的Mock设置。
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Optional, Callable, Dict, List
from decimal import Decimal


class MockAsyncClient:
    """HTTP客户端Mock基类"""
    
    def __init__(self):
        self.responses: Dict[str, Any] = {}
        self.requests: List[Dict[str, Any]] = []
        self.raise_exception: bool = False
        self.exception_to_raise: Exception = None
    
    async def get(self, url: str, **kwargs) -> MagicMock:
        """Mock GET请求"""
        self.requests.append({"method": "GET", "url": url, "kwargs": kwargs})
        
        if self.raise_exception and self.exception_to_raise:
            raise self.exception_to_raise
            
        response = MagicMock()
        response.status_code = 200
        response.text = json.dumps(self.responses.get(url, {}))
        response.json.return_value = self.responses.get(url, {})
        return response
    
    async def post(self, url: str, data: Any = None, **kwargs) -> MagicMock:
        """Mock POST请求"""
        self.requests.append({"method": "POST", "url": url, "data": data, "kwargs": kwargs})
        
        if self.raise_exception and self.exception_to_raise:
            raise self.exception_to_raise
            
        response = MagicMock()
        response.status_code = 200
        response.text = json.dumps(self.responses.get(url, {"success": True}))
        response.json.return_value = self.responses.get(url, {"success": True})
        return response
    
    async def put(self, url: str, data: Any = None, **kwargs) -> MagicMock:
        """Mock PUT请求"""
        self.requests.append({"method": "PUT", "url": url, "data": data, "kwargs": kwargs})
        
        response = MagicMock()
        response.status_code = 200
        response.text = json.dumps({"success": True})
        response.json.return_value = {"success": True}
        return response
    
    async def delete(self, url: str, **kwargs) -> MagicMock:
        """Mock DELETE请求"""
        self.requests.append({"method": "DELETE", "url": url, "kwargs": kwargs})
        
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"success": True}
        return response
    
    def async_context_manager(self):
        """Mock异步上下文管理器"""
        return self
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


class MockCacheService:
    """Mock缓存服务"""
    
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self.hits = 0
        self.misses = 0
        self.calls: List[Dict[str, Any]] = []
    
    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        """获取缓存值"""
        self.calls.append({"method": "get", "key": key})
        value = self._store.get(key, default)
        
        if value is None:
            self.misses += 1
            return None
        
        self.hits += 1
        return value
    
    async def set(
        self, 
        key: str, 
        value: Any,
        expire: Optional[int] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        self.calls.append({"method": "set", "key": key, "value": value, "expire": expire, "ttl": ttl})
        self._store[key] = value
        return True
    
    async def setex(self, key: str, expire: int, value: Any) -> bool:
        """设置带过期时间的缓存值"""
        self.calls.append({"method": "setex", "key": key, "expire": expire, "value": value})
        self._store[key] = value
        return True
    
    async def delete(self, key: str) -> int:
        """删除缓存值"""
        self.calls.append({"method": "delete", "key": key})
        return self._store.pop(key, None) is not None
    
    async def exists(self, key: str) -> int:
        """检查键是否存在"""
        self.calls.append({"method": "exists", "key": key})
        return 1 if key in self._store else 0
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """递增值"""
        self.calls.append({"method": "incr", "key": key, "amount": amount})
        current = self._store.get(key, 0)
        if not isinstance(current, int):
            current = 0
        self._store[key] = current + amount
        return self._store[key]
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.hits = 0
        self.misses = 0
    
    def reset(self) -> None:
        """重置所有状态"""
        self._store.clear()
        self.calls.clear()
        self.reset_stats()


class MockOpenAIClient:
    """Mock OpenAI客户端"""
    
    def __init__(self, mock_response: Optional[str] = None):
        self.mock_response = mock_response or "这是一个模拟的AI回复"
        self.chat_calls: List[Dict[str, Any]] = []
        self.stream_calls: List[Dict[str, Any]] = []
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncMock:
        """Mock聊天接口"""
        self.chat_calls.append({"messages": messages, "kwargs": kwargs})
        
        response = AsyncMock()
        response.content = self.mock_response
        response.usage = MagicMock()
        response.usage.prompt_tokens = 100
        response.usage.completion_tokens = 200
        response.usage.total_tokens = 300
        
        return response
    
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        """Mock聊天流接口"""
        self.stream_calls.append({"messages": messages, "kwargs": kwargs})
        
        async def generate_stream():
            for chunk in self.mock_response.split(" "):
                yield AsyncMock(content=chunk + " ")
        
        return generate_stream()


class MockRedisClient:
    """Mock Redis客户端"""
    
    def __init__(self):
        self._store: Dict[str, bytes] = {}
        self._scan_results: List[str] = []
        self.calls: List[Dict[str, Any]] = []
    
    async def ping(self) -> bool:
        """Ping测试"""
        self.calls.append({"method": "ping"})
        return True
    
    async def get(self, key: str) -> Optional[bytes]:
        """获取值"""
        self.calls.append({"method": "get", "key": key})
        return self._store.get(key)
    
    async def set(
        self,
        key: str,
        value: bytes,
        expire: Optional[int] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """设置值"""
        self.calls.append({"method": "set", "key": key, "expire": expire, "ttl": ttl})
        self._store[key] = value if isinstance(value, bytes) else str(value).encode()
        return True
    
    async def setex(self, key: str, expire: int, value: bytes) -> bool:
        """设置带过期时间的值"""
        self.calls.append({"method": "setex", "key": key, "expire": expire})
        self._store[key] = value if isinstance(value, bytes) else str(value).encode()
        return True
    
    async def delete(self, key: str) -> int:
        """删除值"""
        self.calls.append({"method": "delete", "key": key})
        return self._store.pop(key, None) is not None
    
    async def scan_iter(self, match: str = "*") -> List[str]:
        """扫描键"""
        self.calls.append({"method": "scan_iter", "match": match})
        return self._scan_results if self._scan_results else [
            k for k in self._store.keys() if match in k
        ]
    
    async def exists(self, key: str) -> int:
        """检查键是否存在"""
        self.calls.append({"method": "exists", "key": key})
        return 1 if key in self._store else 0
    
    async def incr(self, key: str) -> int:
        """递增值"""
        self.calls.append({"method": "incr", "key": key})
        current = self._store.get(key, b"0")
        value = int(current.decode()) if isinstance(current, bytes) else int(current)
        self._store[key] = str(value + 1).encode()
        return value + 1
    
    async def acquire_lock(self, key: str, value: str, expire: int = 60) -> bool:
        """获取分布式锁"""
        self.calls.append({"method": "acquire_lock", "key": key, "value": value, "expire": expire})
        if key not in self._store:
            self._store[key] = str(value).encode()
            return True
        return False
    
    async def release_lock(self, key: str, value: str) -> bool:
        """释放分布式锁"""
        self.calls.append({"method": "release_lock", "key": key, "value": value})
        lock_value = self._store.get(key)
        if lock_value and lock_value.decode() == value:
            del self._store[key]
            return True
        return False
    
    def set_scan_results(self, results: List[str]) -> None:
        """设置scan_iter的返回结果"""
        self._scan_results = results
    
    def clear(self):
        """清空所有数据"""
        self._store.clear()
        self._scan_results.clear()
        self.calls.clear()


class MockDatabaseClient:
    """Mock数据库客户端"""

    def __init__(self):
        self._data = {}
        self.queries = []

    def __getitem__(self, key):
        return self._data.get(key)

    def __setitem__(self, key, value):
        self._data[key] = value

    def execute(self, query, params=None):
        """执行查询"""
        self.queries.append({"query": query, "params": params})
        return []

    def fetchone(self):
        """获取单条记录"""
        return None

    def fetchall(self):
        """获取所有记录"""
        return []


class MockDatabaseSession:
    """Mock数据库会话"""
    
    def __init__(self):
        self.added: List[Any] = []
        self.updated: List[Any] = []
        self.deleted: List[Any] = []
        self.committed: bool = False
        self.rolled_back: bool = False
    
    async def add(self, instance: Any) -> None:
        """添加实例"""
        self.added.append(instance)
    
    async def update(self, instance: Any) -> None:
        """更新实例"""
        self.updated.append(instance)
    
    async def delete(self, instance: Any) -> None:
        """删除实例"""
        self.deleted.append(instance)
    
    async def commit(self) -> None:
        """提交事务"""
        self.committed = True
        self.rolled_back = False
    
    async def rollback(self) -> None:
        """回滚事务"""
        self.rolled_back = True
        self.committed = False
    
    def reset(self) -> None:
        """重置状态"""
        self.added.clear()
        self.updated.clear()
        self.deleted.clear()
        self.committed = False
        self.rolled_back = False


def create_mock_service(service_class: str, **kwargs) -> Any:
    """创建Mock服务实例
    
    Args:
        service_class: 服务类标识
            - "cache": 缓存服务
            - "redis": Redis客户端
            - "openai": OpenAI客户端
            - "http": HTTP客户端
        **kwargs: 额外配置参数
        
    Returns:
        Mock服务实例
    """
    if service_class == "cache":
        return MockCacheService()
    elif service_class == "redis":
        return MockRedisClient(**kwargs)
    elif service_class == "openai":
        return MockOpenAIClient(**kwargs)
    elif service_class == "http":
        return MockAsyncClient(**kwargs)
    else:
        raise ValueError(f"未知的服务类型: {service_class}")


def patch_import(
    module_path: str,
    target: str,
    mock_instance: Any
) -> Any:
    """创建导入补丁
    
    Args:
        module_path: 模块路径（如"app.services.cache_service"）
        target: 目标属性名
        mock_instance: Mock实例
        
    Returns:
        补丁对象
        
    Example:
        with patch_import("app.services.cache_service", "get_cache_service", MockCacheService()):
            # 测试代码
            pass
    """
    return patch(f"{module_path}.{target}", return_value=mock_instance)


def create_async_mock(return_value: Any = None, side_effect: Optional[Callable] = None) -> AsyncMock:
    """创建AsyncMock
    
    Args:
        return_value: 返回值
        side_effect: 副作用函数
        
    Returns:
        AsyncMock实例
    """
    mock = AsyncMock()
    if return_value is not None:
        mock.return_value = return_value
    if side_effect is not None:
        mock.side_effect = side_effect
    return mock


class MockResponse:
    """Mock HTTP响应"""
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功") -> MagicMock:
        """创建成功响应"""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "success": True,
            "message": message,
            "data": data
        }
        response.text = json.dumps({
            "success": True,
            "message": message,
            "data": data
        })
        return response
    
    @staticmethod
    def error(
        message: str = "操作失败",
        status_code: int = 400,
        error_code: Optional[str] = None
    ) -> MagicMock:
        """创建错误响应"""
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = {
            "success": False,
            "message": message,
        }
        if error_code:
            response.json.return_value["error_code"] = error_code
        response.text = json.dumps(response.json.return_value)
        return response
    
    @staticmethod
    def not_found() -> MagicMock:
        """创建404响应"""
        return MockResponse.error(message="资源不存在", status_code=404)
    
    @staticmethod
    def unauthorized() -> MagicMock:
        """创建401响应"""
        return MockResponse.error(message="未授权", status_code=401)
    
    @staticmethod
    def forbidden() -> MagicMock:
        """创建403响应"""
        return MockResponse.error(message="禁止访问", status_code=403)