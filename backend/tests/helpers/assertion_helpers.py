"""
断言辅助函数

提供统一的断言工具，简化测试代码并提高可读性。
"""
from typing import Any, Dict, List, Optional, Union
import pytest
from decimal import Decimal
from datetime import datetime, timedelta


def assert_response_success(
    response_data: Any,
    message: str = "操作成功",
    data_key: str = "data"
) -> None:
    """断言响应成功
    
    Args:
        response_data: 响应数据
        message: 期望的成功消息
        data_key: 数据键名
    """
    assert response_data is not None, "响应数据不能为None"
    
    if isinstance(response_data, dict):
        assert response_data.get("success") is True, f"响应不成功: {response_data}"
        assert message in response_data.get("message", ""), f"消息不匹配: {response_data}"
        
        if data_key and data_key in response_data:
            assert response_data[data_key] is not None, f"{data_key}数据不能为None"


def assert_response_error(
    response_data: Any,
    status_code: int = 400,
    message_contains: str = None,
    error_code: str = None
) -> None:
    """断言响应错误
    
    Args:
        response_data: 响应数据
        status_code: 期望的状态码
        message_contains: 错误消息应包含的文本
        error_code: 期望的错误码
    """
    assert response_data is not None, "响应数据不能为None"
    
    if isinstance(response_data, dict):
        assert response_data.get("success") is False, "响应应该失败但成功了"
        
        if message_contains and "message" in response_data:
            assert message_contains in str(response_data["message"]), \
                f"错误消息不包含 '{message_contains}': {response_data['message']}"
        
        if error_code and "error_code" in response_data:
            assert error_code == response_data["error_code"], \
                f"错误码不匹配: 期望 {error_code}, 实际 {response_data['error_code']}"


def assert_not_empty(
    data: Any,
    message: str = "数据不能为空"
) -> None:
    """断言数据非空
    
    Args:
        data: 要检查的数据
        message: 失败时的错误消息
    """
    if data is None:
        pytest.fail(message)
    
    if isinstance(data, (str, list, dict)):
        assert len(data) > 0, message


def assert_not_none(
    data: Any,
    message: str = "数据不能为None"
) -> None:
    """断言数据不为None
    
    Args:
        data: 要检查的数据
        message: 失败时的错误消息
    """
    assert data is not None, message


def assert_equals(
    actual: Any,
    expected: Any,
    message: str = None
) -> None:
    """断言两个值相等
    
    Args:
        actual: 实际值
        expected: 期望值
        message: 失败时的错误消息
    """
    if message:
        assert actual == expected, f"{message}: 期望 {expected}, 实际 {actual}"
    else:
        assert actual == expected, f"期望 {expected}, 实际 {actual}"


def assert_in_range(
    value: Union[int, float, Decimal],
    min_val: Union[int, float, Decimal],
    max_val: Union[int, float, Decimal],
    message: str = None
) -> None:
    """断言值在范围内
    
    Args:
        value: 要检查的值
        min_val: 最小值
        max_val: 最大值
        message: 失败时的错误消息
    """
    if message:
        assert min_val <= value <= max_val, \
            f"{message}: 期望 {min_val} <= {value} <= {max_val}"
    else:
        assert min_val <= value <= max_val, \
            f"期望 {min_val} <= {value} <= {max_val}"


def assert_greater_than(
    value: Union[int, float, Decimal],
    threshold: Union[int, float, Decimal],
    message: str = None
) -> None:
    """断言值大于阈值
    
    Args:
        value: 要检查的值
        threshold: 阈值
        message: 失败时的错误消息
    """
    if message:
        assert value > threshold, f"{message}: 期望 {value} > {threshold}"
    else:
        assert value > threshold, f"期望 {value} > {threshold}"


def assert_less_than(
    value: Union[int, float, Decimal],
    threshold: Union[int, float, Decimal],
    message: str = None
) -> None:
    """断言值小于阈值
    
    Args:
        value: 要检查的值
        threshold: 阈值
        message: 失败时的错误消息
    """
    if message:
        assert value < threshold, f"{message}: 期望 {value} < {threshold}"
    else:
        assert value < threshold, f"期望 {value} < {threshold}"


def assert_list_length(
    lst: List[Any],
    expected_length: int,
    message: str = None
) -> None:
    """断言列表长度
    
    Args:
        lst: 列表
        expected_length: 期望长度
        message: 失败时的错误消息
    """
    actual_length = len(lst)
    if message:
        assert actual_length == expected_length, \
            f"{message}: 期望长度 {expected_length}, 实际长度 {actual_length}"
    else:
        assert actual_length == expected_length, \
            f"期望长度 {expected_length}, 实际长度 {actual_length}"


def assert_dict_contains(
    data: Dict[str, Any],
    required_keys: List[str],
    message: str = None
) -> None:
    """断言字典包含指定键
    
    Args:
        data: 字典
        required_keys: 必须包含的键列表
        message: 失败时的错误消息
    """
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        if message:
            pytest.fail(f"{message}. 缺少键: {missing_keys}")
        else:
            pytest.fail(f"缺少必需键: {missing_keys}")


def assert_dict_excludes(
    data: Dict[str, Any],
    excluded_keys: List[str],
    message: str = None
) -> None:
    """断言字典不包含指定键
    
    Args:
        data: 字典
        excluded_keys: 必须排除的键列表
        message: 失败时的错误消息
    """
    found_keys = [key for key in excluded_keys if key in data]
    
    if found_keys:
        if message:
            pytest.fail(f"{message}. 找到不应存在的键: {found_keys}")
        else:
            pytest.fail(f"找到不应存在的键: {found_keys}")


def assert_timestamp_recent(
    timestamp: Union[datetime, str],
    max_age_seconds: int = 3600,
    message: str = None
) -> None:
    """断言时间戳是最近的
    
    Args:
        timestamp: 时间戳（datetime或ISO字符串）
        max_age_seconds: 最大允许的秒数
        message: 失败时的错误消息
    """
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail(f"无效的时间戳格式: {timestamp}")
            return
    
    now = datetime.now()
    age = (now - timestamp).total_seconds()
    
    if message:
        assert age < max_age_seconds, \
            f"{message}: 时间戳太旧 ({age}秒 > {max_age_seconds}秒)"
    else:
        assert age < max_age_seconds, \
            f"时间戳太旧 ({age}秒 > {max_age_seconds}秒)"


def assert_pagination(
    page: int,
    page_size: int,
    total: int,
    data: List[Any],
    message: str = None
) -> None:
    """断言分页数据正确
    
    Args:
        page: 当前页码
        page_size: 每页大小
        total: 总记录数
        data: 数据列表
        message: 失败时的错误消息
    """
    if message:
        assert isinstance(data, list), f"{message}: data必须是列表"
    else:
        assert isinstance(data, list), "data必须是列表"
    
    expected_count = page_size
    last_page = (total + page_size - 1) // page_size
    
    # 不是最后一页，应该有完整的数据
    if page < last_page:
        expected_count = page_size
    
    expected_count = min(page_size, total - (page - 1) * page_size)
    expected_count = max(0, expected_count)
    
    actual_count = len(data)
    
    if message:
        assert actual_count <= expected_count, \
            f"{message}: 期望最多 {expected_count} 条实际 {actual_count} 条"
    else:
        assert actual_count <= expected_count, \
            f"期望最多 {expected_count} 条实际 {actual_count} 条"


def assert_validation_error(
    response_data: Any,
    field_names: List[str],
    message: str = None
) -> None:
    """断言验证错误
    
    Args:
        response_data: 响应数据
        field_names: 应该出错的字段名
        message: 失败时的错误消息
    """
    assert_response_error(response_data, message="验证失败")
    
    if isinstance(response_data, dict) and "errors" in response_data:
        errors = response_data["errors"]
        
        if message:
            assert isinstance(errors, (str, list)), f"{message}: errors必须是字符串或列表"
        
        error_text = " ".join(errors) if isinstance(errors, list) else errors
        
        for field in field_names:
            assert field.lower() in error_text.lower(), \
                f"{message}: 期望 '{field}' 字段错误"


def assert_idempotency(
    response1: Any,
    response2: Any,
    check_fields: List[str] = None,
    message: str = None
) -> None:
    """断言两个响应相等（幂等性）
    
    Args:
        response1: 第一个响应
        response2: 第二个响应
        check_fields: 要检查的字段列表
        message: 失败时的错误消息
    """
    if check_fields is None:
        check_fields = ["data", "status"]
    
    for field in check_fields:
        if isinstance(response1, dict) and isinstance(response2, dict):
            assert response1.get(field) == response2.get(field), \
                f"{message if message else '幂等性'}: 字段 '{field}' 值不同:" \
                f" {response1.get(field)} != {response2.get(field)}"


def assert_coverage_increased(
    old_coverage: float,
    new_coverage: float,
    min_increase: float = 0.0,
    message: str = None
) -> None:
    """断言覆盖率增加
    
    Args:
        old_coverage: 旧覆盖率
        new_coverage: 新覆盖率
        min_increase: 最小增加量
        message: 失败时的错误消息
    """
    increase = new_coverage - old_coverage
    
    if message:
        assert increase >= min_increase, \
            f"{message}: 覆盖率应至少增加 {min_increase}%, " \
            f"实际增加 {increase}% (从 {old_coverage}% 到 {new_coverage}%)"
    else:
        assert increase >= min_increase, \
            f"覆盖率应至少增加 {min_increase}%, " \
            f"实际增加 {increase}% (从 {old_coverage}% 到 {new_coverage}%)"


def assert_data_type(
    data: Any,
    expected_type: type,
    message: str = None
) -> None:
    """断言数据类型
    
    Args:
        data: 要检查的数据
        expected_type: 期望的类型
        message: 失败时的错误消息
    """
    actual_type = type(data)
    
    if message:
        assert isinstance(data, expected_type), \
            f"{message}: 期望类型 {expected_type.__name__}, 实际类型 {actual_type.__name__}"
    else:
        assert isinstance(data, expected_type), \
            f"期望类型 {expected_type.__name__}, 实际类型 {actual_type.__name__}"


def assert_datetime_between(
    dt: datetime,
    start: datetime,
    end: datetime,
    message: str = None
) -> None:
    """断言日期时间在指定范围内
    
    Args:
        dt: 要检查的日期时间
        start: 开始时间
        end: 结束时间
        message: 失败时的错误消息
    """
    if message:
        assert start <= dt <= end, \
            f"{message}: 期望 {start} <= {dt} <= {end}"
    else:
        assert start <= dt <= end, f"期望 {start} <= {dt} <= {end}"


def assert_email_format(
    email: str,
    message: str = None
) -> None:
    """断言邮箱格式
    
    Args:
        email: 邮箱地址
        message: 失败时的错误消息
    """
    assert "@" in email, f"{message if message else '邮箱格式'}: 缺少 @ 符号"
    assert "." in email.split("@")[-1], \
        f"{message if message else '邮箱格式'}: 域名缺少 ."
    
    local, domain = email.rsplit("@", 1, 1)
    assert len(local) > 0, f"{message if message else '邮箱格式'}: 用户名不能为空"
    assert len(domain) > 0, f"{message if message else '邮箱格式'}: 域名不能为空"


def assert_phone_format(
    phone: str,
    message: str = None
) -> None:
    """断言电话号码格式
    
    Args:
        phone: 电话号码
        message: 失败时的错误消息
    """
    # 移除所有非数字字符
    digits_only = "".join(filter(str.isdigit, phone))
    
    if message:
        assert len(digits_only) >= 10 and len(digits_only) <= 15, \
            f"{message}: 电话号码应为10-15位数字"
    else:
        assert len(digits_only) >= 10 and len(digits_only) <= 15, \
            "电话号码应为10-15位数字"


def assert_status_code(
    status_code: int,
    expected_codes: Union[int, List[int]],
    message: str = None
) -> None:
    """断言状态码在预期范围内
    
    Args:
        status_code: 实际状态码
        expected_codes: 期望的状态码（单个或列表）
        message: 失败时的错误消息
    """
    if isinstance(expected_codes, int):
        expected_codes = [expected_codes]
    
    if message:
        assert status_code in expected_codes, \
            f"{message}: 期望状态码 {expected_codes}, 实际 {status_code}"
    else:
        assert status_code in expected_codes, \
            f"期望状态码 {expected_codes}, 实际 {status_code}"


def assert_not_contains(
    container: Union[str, List[Any], Dict[str, Any]],
    item: Any,
    message: str = None
) -> None:
    """断言容器不包含指定项
    
    Args:
        container: 容器（字符串、列表或字典）
        item: 要检查的项
        message: 失败时的错误消息
    """
    if isinstance(container, str):
        assert item not in container, \
            f"{message if message else '不包含'}: 字符串包含 '{item}'"
    elif isinstance(container, (list, tuple)):
        assert item not in container, \
            f"{message if message else '不包含'}: 列表包含 '{item}'"
    elif isinstance(container, dict):
        assert item not in container, \
            f"{message if message else '不包含'}: 字典包含键 '{item}'"
    else:
        raise TypeError(f"不支持的容器类型: {type(container)}")


def assert_all_items_match(
    items: List[Any],
    predicate: callable,
    message: str = None
) -> None:
    """断言所有项匹配谓词
    
    Args:
        items: 项列表
        predicate: 谓词函数
        message: 失败时的错误消息
    """
    for i, item in enumerate(items):
        if not predicate(item):
            if message:
                pytest.fail(f"{message}: 第 {i} 项 {item} 不匹配谓词")
            else:
                pytest.fail(f"第 {i} 项 {item} 不匹配谓词")


def assert_list_sorted(
    items: List[Any],
    key: str = None,
    reverse: bool = False,
    message: str = None
) -> None:
    """断言列表已排序
    
    Args:
        items: 列表
        key: 排序键（字典列表）
        reverse: 是否降序
        message: 失败时的错误消息
    """
    if key and all(isinstance(x, dict) for x in items):
        sorted_items = sorted(items, key=lambda x: x[key], reverse=reverse)
    else:
        sorted_items = sorted(items, reverse=reverse)
    
    if items != sorted_items:
        if message:
            pytest.fail(f"{message}: 列表未正确排序")
        else:
            pytest.fail("列表未正确排序")


def assert_string_length(
    s: str,
    min_length: int = 0,
    max_length: int = None,
    message: str = None
) -> None:
    """断言字符串长度
    
    Args:
        s: 字符串
        min_length: 最小长度
        max_length: 最大长度
        message: 失败时的错误消息
    """
    actual_length = len(s)
    
    if actual_length < min_length:
        if message:
            pytest.fail(f"{message}: 字符串长度 {actual_length} < {min_length}")
        else:
            pytest.fail(f"字符串长度 {actual_length} < {min_length}")
    
    if max_length and actual_length > max_length:
        if message:
            pytest.fail(f"{message}: 字符串长度 {actual_length} > {max_length}")
        else:
            pytest.fail(f"字符串长度 {actual_length} > {max_length}")


def assert_async_called_with(
    mock: Any,
    call_count: int = 1,
    message: str = None
) -> None:
    """断言异步Mock被调用指定次数
    
    Args:
        mock: Mock对象
        call_count: 期望的调用次数
        message: 失败时的错误消息
    """
    if message:
        assert mock.call_count == call_count, \
            f"{message}: 期望调用 {call_count} 次, 实际调用 {mock.call_count} 次"
    else:
        assert mock.call_count == call_count, \
            f"期望调用 {call_count} 次, 实际调用 {mock.call_count} 次"


def assert_mock_not_called(mock: Any, message: str = None) -> None:
    """断言Mock未被调用
    
    Args:
        mock: Mock对象
        message: 失败时的错误消息
    """
    if message:
        assert mock.call_count == 0, \
            f"{message}: Mock 不应被调用"
    else:
        assert mock.call_count == 0, "Mock 不应被调用"


def assert_dicts_equal(
    dict1: Dict[str, Any],
    dict2: Dict[str, Any],
    ignore_keys: List[str] = None,
    message: str = None
) -> None:
    """断言两个字典相等（可忽略某些键）
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        ignore_keys: 要忽略的键列表
        message: 失败时的错误消息
    """
    if ignore_keys is None:
        ignore_keys = []
    
    keys1 = set(dict1.keys()) - set(ignore_keys)
    keys2 = set(dict2.keys()) - set(ignore_keys)
    
    if keys1 != keys2:
        if message:
            pytest.fail(f"{message}: 键集合不同: {keys1} vs {keys2}")
        else:
            pytest.fail(f"键集合不同: {keys1} vs {keys2}")
    
    for key in keys1:
        if dict1[key] != dict2[key]:
            if message:
                pytest.fail(f"{message}: 键 '{key}' 值不同: " \
                    f"{dict1[key]} != {dict2[key]}")
            else:
                pytest.fail(f"键 '{key}' 值不同: {dict1[key]} != {dict2[key]}")


# 便捷断言类
class AssertionHelper:
    """断言助手类，方便在测试中使用"""
    
    def __init__(self, prefix: str = "断言"):
        self.prefix = prefix
    
    def success(self, *args, **kwargs) -> None:
        """成功断言"""
        assert_response_success(*args, **kwargs)
    
    def error(self, *args, **kwargs) -> None:
        """错误断言"""
        assert_response_error(*args, **kwargs)
    
    def not_empty(self, *args, **kwargs) -> None:
        """非空断言"""
        assert_not_empty(*args, **kwargs)
    
    def not_none(self, *args, **kwargs) -> None:
        """非None断言"""
        assert_not_none(*args, **kwargs)
    
    def equals(self, *args, **kwargs) -> None:
        """相等断言"""
        assert_equals(*args, **kwargs)
    
    def in_range(self, *args, **kwargs) -> None:
        """范围断言"""
        assert_in_range(*args, **kwargs)
    
    def greater_than(self, *args, **kwargs) -> None:
        """大于断言"""
        assert_greater_than(*args, **kwargs)
    
    def less_than(self, *args, **kwargs) -> None:
        """小于断言"""
        assert_less_than(*args, **kwargs)
    
    def list_length(self, *args, **kwargs) -> None:
        """列表长度断言"""
        assert_list_length(*args, **kwargs)
    
    def dict_contains(self, *args, **kwargs) -> None:
        """字典包含断言"""
        assert_dict_contains(*args, **kwargs)
    
    def dict_excludes(self, *args, **kwargs) -> None:
        """字典排除断言"""
        assert_dict_excludes(*args, **kwargs)
    
    def timestamp_recent(self, *args, **kwargs) -> None:
        """时间戳最近断言"""
        assert_timestamp_recent(*args, **kwargs)
    
    def pagination(self, *args, **kwargs) -> None:
        """分页断言"""
        assert_pagination(*args, **kwargs)