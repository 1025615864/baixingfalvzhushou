"""Prometheus指标采集配置

提供装饰器式的API请求追踪。
"""
from functools import wraps
import time
import logging
from contextlib import asynccontextmanager

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
except ImportError:
    Counter = Histogram = Gauge = Info = None
    start_http_server = None

logger = logging.getLogger(__name__)

if Counter is None:
    api_request_total = None
    api_request_duration = None
    api_errors_total = None
    active_connections = None
    user_sessions_active = None
    system_info = None
    ai_requests_total = None
    ai_request_duration = None
    cache_operations_total = None
    database_query_duration = None
    websocket_connections = None
    websocket_messages_total = None
else:
    # 指标定义 - API请求相关
    api_request_total = Counter(
        'api_requests_total',
        'Total API requests',
        ['method', 'endpoint', 'status']
    )

    api_request_duration = Histogram(
        'api_request_duration_seconds',
        'API request duration in seconds',
        ['method', 'endpoint'],
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )

    api_errors_total = Counter(
        'api_errors_total',
        'Total API errors',
        ['error_type', 'endpoint']
    )

    # 指标定义 - 数据库连接
    active_connections = Gauge(
        'active_connections',
        'Active database connections',
        ['database']
    )

    # 指标定义 - 用户会话
    user_sessions_active = Gauge(
        'user_sessions_active',
        'Active user sessions',
        ['status']  # active, expired
    )

    # 指标定义 - 系统信息
    system_info = Info(
        'system_info',
        'System information'
    )

    # 指标定义 - 业务自定义
    ai_requests_total = Counter(
        'ai_requests_total',
        'Total AI requests',
        ['model', 'operation']
    )

    ai_request_duration = Histogram(
        'ai_request_duration_seconds',
        'AI request duration in seconds',
        ['model', 'operation'],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
    )

    cache_operations_total = Counter(
        'cache_operations_total',
        'Total cache operations',
        ['operation', 'cache_name']
    )

    database_query_duration = Histogram(
        'database_query_duration_seconds',
        'Database query duration in seconds',
        ['table', 'operation'],
        buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
    )

    # 指标定义 - WebSocket连接
    websocket_connections = Gauge(
        'websocket_connections',
        'Active WebSocket connections'
    )

    websocket_messages_total = Counter(
        'websocket_messages_total',
        'Total WebSocket messages',
        ['direction', 'message_type']
    )


def track_api_request(func=None, *, track_errors: bool = True):
    """装饰器：追踪API请求
    
    Args:
        func: 要装饰的函数
        track_errors: 是否追踪错误
        
    Returns:
        装饰后的函数
    """
    def decorator(f):
        @wraps(f)
        async def async_wrapper(*args, **kwargs):
            if api_request_total is None:
                return await f(*args, **kwargs)
            
            start_time = time.time()
            method = 'UNKNOWN'
            endpoint = f.__name__
            status = '200'
            
            try:
                # 尝试从kwargs中获取request对象
                request = kwargs.get('request')
                if hasattr(request, 'method'):
                    method = request.method
                if hasattr(request, 'url'):
                    endpoint = request.url.path
                
                # 执行请求
                result = await f(*args, **kwargs)
                
                # 记录成功请求
                status_code = getattr(result, 'status_code', 200)
                duration = time.time() - start_time
                
                api_request_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=str(status_code)
                ).inc()
                
                api_request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                error_type = type(e).__name__
                
                # 记录错误请求
                api_request_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status='error'
                ).inc()
                
                api_request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                if track_errors:
                    api_errors_total.labels(
                        error_type=error_type,
                        endpoint=endpoint
                    ).inc()
                
                # 重新抛出异常
                raise
        
        @wraps(f)
        def sync_wrapper(*args, **kwargs):
            if api_request_total is None:
                return f(*args, **kwargs)
            
            start_time = time.time()
            method = 'UNKNOWN'
            endpoint = f.__name__
            status = '200'
            
            try:
                # 执行请求
                result = f(*args, **kwargs)
                
                # 记录成功请求
                duration = time.time() - start_time
                
                api_request_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
                
                api_request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                error_type = type(e).__name__
                
                # 记录错误请求
                api_request_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status='error'
                ).inc()
                
                api_request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                if track_errors:
                    api_errors_total.labels(
                        error_type=error_type,
                        endpoint=endpoint
                    ).inc()
                
                # 重新抛出异常
                raise
        
        # 判断是异步还是同步函数
        import asyncio
        if asyncio.iscoroutinefunction(f):
            return async_wrapper
        else:
            return sync_wrapper
    
    # 支持带参数和不带参数的装饰器
    if func is not None:
        return decorator(func)
    else:
        return decorator


def track_ai_request(func):
    """装饰器：追踪AI请求
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        if ai_request_duration is None:
            return await func(*args, **kwargs)
        
        start_time = time.time()
        model = kwargs.get('model', 'unknown')
        operation = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            
            duration = time.time() - start_time
            ai_requests_total.labels(
                model=model,
                operation=operation
            ).inc()
            
            ai_request_duration.labels(
                model=model,
                operation=operation
            ).observe(duration)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            ai_requests_total.labels(
                model=model,
                operation=operation
            ).inc()
            
            ai_request_duration.labels(
                model=model,
                operation=operation
            ).observe(duration)
            
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        if ai_request_duration is None:
            return func(*args, **kwargs)
        
        start_time = time.time()
        model = kwargs.get('model', 'unknown')
        operation = func.__name__
        
        try:
            result = func(*args, **kwargs)
            
            duration = time.time() - start_time
            ai_requests_total.labels(
                model=model,
                operation=operation
            ).inc()
            
            ai_request_duration.labels(
                model=model,
                operation=operation
            ).observe(duration)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            ai_requests_total.labels(
                model=model,
                operation=operation
            ).inc()
            
            ai_request_duration.labels(
                model=model,
                operation=operation
            ).observe(duration)
            
            raise
    
    # 判断是异步还是同步函数
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def track_cache_operation(operation: str, cache_name: str = 'default'):
    """追踪缓存操作的上下文管理器
    
    Args:
        operation: 操作类型 (hit, miss, set, delete)
        cache_name: 缓存名称
        
    Yields:
        None
    """
    if cache_operations_total is None:
        yield
        return
    
    cache_operations_total.labels(
        operation=operation,
        cache_name=cache_name
    ).inc()
    yield


@asynccontextmanager
async def track_database_query(table: str, operation: str):
    """追踪数据库查询的上下文管理器
    
    Args:
        table: 表名
        operation: 操作类型 (select, insert, update, delete)
        
    Yields:
        None
    """
    if database_query_duration is None:
        yield
        return
    
    import time
    start_time = time.time()
    
    try:
        yield
    finally:
        duration = time.time() - start_time
        database_query_duration.labels(
            table=table,
            operation=operation
        ).observe(duration)


def update_system_info(version: str, environment: str, python_version: str = None):
    """更新系统信息
    
    Args:
        version: 应用版本
        environment: 环境 (production, staging, development)
        python_version: Python版本
    """
    if system_info is None:
        return
    
    info_data = {
        'version': version,
        'environment': environment,
        'framework': 'FastAPI',
    }
    
    if python_version:
        info_data['python_version'] = python_version
    
    system_info.info(info_data)


def update_active_connections(database: str, count: int):
    """更新活跃数据库连接数
    
    Args:
        database: 数据库名称
        count: 连接数
    """
    if active_connections is None:
        return
    
    active_connections.labels(database=database).set(count)


def update_user_sessions(active: int = None, expired: int = None):
    """更新用户会话数
    
    Args:
        active: 活跃会话数
        expired: 过期会话数
    """
    if user_sessions_active is None:
        return
    
    if active is not None:
        user_sessions_active.labels(status='active').set(active)
    if expired is not None:
        user_sessions_active.labels(status='expired').set(expired)


def update_websocket_connections(count: int):
    """更新WebSocket连接数
    
    Args:
        count: 连接数
    """
    if websocket_connections is None:
        return
    
    websocket_connections.set(count)


def record_websocket_message(direction: str, message_type: str):
    """记录WebSocket消息
    
    Args:
        direction: 消息方向 (incoming, outgoing)
        message_type: 消息类型
    """
    if websocket_messages_total is None:
        return
    
    websocket_messages_total.labels(
        direction=direction,
        message_type=message_type
    ).inc()


def start_metrics_server(port: int = 8001, host: str = '0.0.0.0'):
    """启动Prometheus指标服务器
    
    Args:
        port: 监听端口
        host: 监听地址
        
    Returns:
        是否启动成功
    """
    if start_http_server is None:
        logger.warning("prometheus_client未安装，无法启动Prometheus指标服务器")
        return False
    
    try:
        import threading
        thread = threading.Thread(
            target=start_http_server,
            kwargs={'port': port, 'addr': host},
            daemon=True
        )
        thread.start()
        logger.info(f"Prometheus metrics server started on {host}:{port}")
        return True
    except Exception as e:
        logger.error(f"Failed to start Prometheus metrics server: {e}")
        return False


def get_prometheus_metrics_text() -> str:
    """获取Prometheus格式的指标文本
    
    Returns:
        指标文本
    """
    try:
        from prometheus_client import generate_latest
        return generate_latest().decode('utf-8')
    except ImportError:
        return ""


__all__ = [
    'track_api_request',
    'track_ai_request',
    'track_cache_operation',
    'track_database_query',
    'update_system_info',
    'update_active_connections',
    'update_user_sessions',
    'update_websocket_connections',
    'record_websocket_message',
    'start_metrics_server',
    'get_prometheus_metrics_text',
]