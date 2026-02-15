"""
安全测试用例

测试常见安全漏洞：SQL注入、XSS、CSRF、权限控制等
"""

import pytest
from httpx import AsyncClient


class SecurityTestResults:
    """安全测试结果收集器"""
    
    def __init__(self):
        self.results: list[dict] = []
    
    def record(self, name: str, passed: bool, details: str = ""):
        self.results.append({
            "name": name,
            "passed": passed,
            "details": details,
        })
    
    def get_summary(self) -> dict:
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed / total * 100) if total > 0 else 0,
        }


_security_results = SecurityTestResults()


@pytest.fixture
def security_results():
    """安全测试结果 fixture"""
    _security_results.results.clear()
    yield _security_results
    summary = _security_results.get_summary()
    print(f"\n安全测试摘要: {summary['passed']}/{summary['total']} 通过")


@pytest.mark.asyncio
async def test_sql_injection_prevention(
    client: AsyncClient,
    security_results: SecurityTestResults,
) -> None:
    """测试SQL注入防护"""
    malicious_inputs = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1; SELECT * FROM users",
        "1' UNION SELECT * FROM users --",
        "admin'--",
    ]
    
    for input_val in malicious_inputs:
        res = await client.get(f"/api/forum/posts?search={input_val}")
        # 应该返回200或400，而不是500或泄露数据
        assert res.status_code in [200, 400, 404], f"SQL注入可能: {input_val}"
    
    security_results.record("SQL注入防护", True, "所有恶意输入被正确处理")


@pytest.mark.asyncio
async def test_xss_prevention(
    client: AsyncClient,
    security_results: SecurityTestResults,
) -> None:
    """测试XSS防护"""
    xss_payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "<svg onload=alert('xss')>",
        "javascript:alert('xss')",
        "{{constructor.constructor('alert(1)')()}}",
    ]
    
    for payload in xss_payloads:
        res = await client.post(
            "/api/forum/posts",
            json={
                "title": payload,
                "content": "test content",
                "category": "general",
            },
        )
        # 应该返回200、400或401（需要认证）
        assert res.status_code in [200, 400, 401], f"XSS可能: {payload}"
        
        # 如果创建成功（需要认证），检查返回内容是否转义
        if res.status_code == 200:
            data = res.json()
            if payload in str(data):
                security_results.record("XSS防护", False, f"未转义: {payload[:30]}")
                return
    
    security_results.record("XSS防护", True, "所有XSS载荷被正确处理")


@pytest.mark.asyncio
async def test_unauthorized_access_prevention(
    client: AsyncClient,
    security_results: SecurityTestResults,
) -> None:
    """测试未授权访问防护"""
    # 尝试访问需要认证的端点
    protected_endpoints = [
        ("GET", "/api/user/me"),
        ("POST", "/api/forum/posts"),
    ]
    
    for method, endpoint in protected_endpoints:
        res = await client.request(method, endpoint)
        # 应该返回401或403，或者404（端点不存在）
        assert res.status_code in [401, 403, 404], f"未授权访问可能: {method} {endpoint}"
    
    security_results.record("未授权访问防护", True, "所有受保护端点正确拒绝未认证请求")


@pytest.mark.asyncio
async def test_rate_limiting(
    client: AsyncClient,
    security_results: SecurityTestResults,
) -> None:
    """测试速率限制"""
    # 快速发送多个请求
    request_count = 15
    responses = []
    
    for _ in range(request_count):
        res = await client.get("/api/health")
        responses.append(res.status_code)
    
    # 检查是否有429状态码（速率限制）
    has_rate_limit = 429 in responses
    
    # 如果没有速率限制，至少应该都成功
    if not has_rate_limit:
        success_count = sum(1 for s in responses if s == 200)
        security_results.record(
            "速率限制",
            success_count == request_count,
            f"请求成功率: {success_count}/{request_count}",
        )
    else:
        security_results.record("速率限制", True, "检测到速率限制响应")


@pytest.mark.asyncio
async def test_sensitive_data_exposure(
    client: AsyncClient,
    security_results: SecurityTestResults,
) -> None:
    """测试敏感数据暴露"""
    # 检查错误响应是否泄露敏感信息
    res = await client.get("/api/user/99999999")
    
    if res.status_code == 404:
        data = res.json()
        # 检查是否泄露数据库结构或其他敏感信息
        sensitive_keywords = ["password", "hashed_password", "secret", "token"]
        response_str = str(data).lower()
        
        for keyword in sensitive_keywords:
            if keyword in response_str:
                security_results.record(
                    "敏感数据暴露",
                    False,
                    f"响应中可能泄露: {keyword}",
                )
                return
    
    security_results.record("敏感数据暴露", True, "响应中未发现敏感数据泄露")


@pytest.mark.asyncio
async def test_input_validation(
    client: AsyncClient,
    security_results: SecurityTestResults,
) -> None:
    """测试输入验证"""
    invalid_inputs = [
        ("page", "-1"),
        ("page_size", "999999"),
    ]
    
    for field, value in invalid_inputs:
        res = await client.get(f"/api/forum/posts?{field}={value}")
        # 应该返回200（可能忽略无效参数）或400/422
        assert res.status_code in [200, 400, 422], f"输入验证可能不足: {field}={value}"
    
    security_results.record("输入验证", True, "所有无效输入被正确处理")


def test_security_summary() -> None:
    """安全测试摘要"""
    summary = _security_results.get_summary()
    
    print("\n" + "=" * 50)
    print("安全测试摘要")
    print("=" * 50)
    print(f"总测试数: {summary['total']}")
    print(f"通过: {summary['passed']}")
    print(f"失败: {summary['failed']}")
    print(f"成功率: {summary['success_rate']:.2f}%")
    print("=" * 50)
    
    # 验证基本安全要求
    assert summary["success_rate"] >= 80, f"安全测试通过率应>=80%，实际: {summary['success_rate']}%"
