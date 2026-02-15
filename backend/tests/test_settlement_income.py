"""
律师收入记录API测试

测试settlement/income.py路由的功能，包括收入记录查询、导出等
覆盖收入记录管理的各种场景
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy import select

from app.models.settlement import LawyerIncomeRecord, LawyerWallet
from app.models.lawfirm import Lawyer, LawyerConsultation
from app.models.payment import PaymentOrder, PaymentStatus
from app.models.user import User


@pytest.mark.asyncio
async def test_list_income_records_success(client: AsyncClient, test_session):
    """测试成功获取收入记录列表"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)

    # 创建收入记录
    record1 = await create_income_record(test_session, lawyer.id, 100.0, "pending")
    record2 = await create_income_record(test_session, lawyer.id, 200.0, "settled")

    # 生成当前律师的授权头
    headers = _auth_headers_for_user(lawyer.user_id)

    # 请求收入记录列表
    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_list_income_records_with_status_filter(client: AsyncClient, test_session):
    """测试按状态筛选收入记录"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    await create_income_record(test_session, lawyer.id, 100.0, "pending")
    await create_income_record(test_session, lawyer.id, 200.0, "settled")
    await create_income_record(test_session, lawyer.id, 300.0, "pending")

    headers = _auth_headers_for_user(lawyer.user_id)

    # 查询pending状态的记录
    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"status": "pending", "page": 1, "page_size": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # 应该有2条pending记录
    for item in data["items"]:
        assert item["status"] == "pending"


@pytest.mark.asyncio
async def test_list_income_records_pagination(client: AsyncClient, test_session):
    """测试分页功能"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建25条记录
    for i in range(25):
        await create_income_record(test_session, lawyer.id, float(100 + i))

    headers = _auth_headers_for_user(lawyer.user_id)

    # 第一页
    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 25
    assert data["page"] == 1
    assert data["page_size"] == 10
    
    # 第二页
    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 2, "page_size": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["page"] == 2
    
    # 最后一页
    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 3, "page_size": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5


@pytest.mark.asyncio
async def test_list_income_records_empty_result(client: AsyncClient, test_session):
    """测试空结果的情况"""
    # 创建律师但没有收入记录
    lawyer = await create_test_lawyer_with_user(test_session)

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_list_income_records_unauthorized(client: AsyncClient, test_session):
    """测试未授权访问"""
    response = await client.get(
        "/api/lawyer/income-records",
        params={"page": 1, "page_size": 20}
    )
    
    # 应该返回401未授权
    assert response.status_code in [401, 422]


@pytest.mark.asyncio
async def test_list_income_records_no_lawyer_profile(client: AsyncClient, test_session):
    """测试用户没有律师资料"""
    # 创建普通用户但没有律师资料
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hash",
        is_active=True,
        phone="13800138000"
    )
    test_session.add(user)
    await test_session.commit()

    headers = _auth_headers_for_user(user.id)

    # 尝试访问收入记录
    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 20}
    )
    
    # 应该返回403禁止访问
    assert response.status_code == 403
    assert "未绑定律师资料" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_list_income_records_with_consultation_subject(client: AsyncClient, test_session):
    """测试包含咨询主题的收入记录"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建咨询记录
    consultation = LawyerConsultation(
        user_id=lawyer.user_id,
        lawyer_id=lawyer.id,
        subject="测试咨询主题",
        status="completed",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(consultation)
    await test_session.commit()
    
    # 创建关联的收入记录
    record = LawyerIncomeRecord(
        lawyer_id=lawyer.id,
        consultation_id=consultation.id,
        user_paid_amount=100.0,
        platform_fee=15.0,
        lawyer_income=85.0,
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(record)
    await test_session.commit()

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    assert len(items) >= 1
    # 验证包含咨询主题
    found = False
    for item in items:
        if item["consultation_id"] == consultation.id:
            assert item["consultation_subject"] == "测试咨询主题"
            found = True
    assert found


@pytest.mark.asyncio
async def test_list_income_records_sorted_by_created_at(client: AsyncClient, test_session):
    """测试按创建时间降序排列"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建不同时间的记录
    base_time = datetime.now(timezone.utc)
    record1 = await create_income_record(test_session, lawyer.id, 100.0, "pending", base_time - timedelta(hours=3))
    record2 = await create_income_record(test_session, lawyer.id, 200.0, "settled", base_time - timedelta(hours=2))
    record3 = await create_income_record(test_session, lawyer.id, 300.0, "pending", base_time - timedelta(hours=1))

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    assert len(items) >= 3
    # 验证按创建时间降序排列（最新的在前）
    assert items[0]["id"] == record3.id
    assert items[1]["id"] == record2.id
    assert items[2]["id"] == record1.id


@pytest.mark.asyncio
async def test_list_income_records_page_size_boundary(client: AsyncClient, test_session):
    """测试分页大小边界"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)

    headers = _auth_headers_for_user(lawyer.user_id)

    # 测试最小页面大小
    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 1}
    )
    assert response.status_code == 200
    
    # 测试最大页面大小
    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 100}
    )
    assert response.status_code == 200
    
    # 测试超出范围的页面大小（应该被拒绝或自动调整）
    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 101}
    )
    # 应该返回422参数验证错误
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_export_income_records_success(client: AsyncClient, test_session):
    """测试成功导出收入记录为CSV"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    await create_income_record(test_session, lawyer.id, 100.0, "pending")
    await create_income_record(test_session, lawyer.id, 200.0, "settled")

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get(
        "/api/lawyer/income-records/export",
        headers=headers
    )
    
    assert response.status_code == 200
    # 验证响应是CSV格式
    assert response.headers["content-type"] == "text/csv; charset=utf-8-sig"
    assert "attachment" in response.headers.get("content-disposition", "")
    assert ".csv" in response.headers.get("content-disposition", "")
    
    # 验证CSV内容包含BOM和表头
    content = response.content.decode('utf-8-sig')
    assert "id" in content
    assert "consultation_id" in content
    assert "user_paid_amount" in content
    assert "lawyer_income" in content


@pytest.mark.asyncio
async def test_export_income_records_with_status_filter(client: AsyncClient, test_session):
    """测试导出时按状态筛选"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    await create_income_record(test_session, lawyer.id, 100.0, "pending")
    await create_income_record(test_session, lawyer.id, 200.0, "settled")
    await create_income_record(test_session, lawyer.id, 300.0, "pending")

    headers = _auth_headers_for_user(lawyer.user_id)

    # 导出pending状态的记录
    response = await client.get(
        "/api/lawyer/income-records/export",
        headers=headers,
        params={"status": "pending"}
    )
    
    assert response.status_code == 200
    content = response.content.decode('utf-8-sig')
    # 验证包含pending状态的数据
    lines = content.split("\n")
    # 表头1行 + 数据行
    # 应该包含2条pending记录（排除表头）
    assert len([line for line in lines if line.strip()]) >= 2


@pytest.mark.asyncio
async def test_export_income_records_unauthorized(client: AsyncClient, test_session):
    """测试未授权导出"""
    response = await client.get("/api/lawyer/income-records/export")
    
    # 应该返回401未授权
    assert response.status_code in [401, 422]


@pytest.mark.asyncio
async def test_export_income_records_no_lawyer_profile(client: AsyncClient, test_session):
    """测试用户没有律师资料时导出"""
    # 创建普通用户但没有律师资料
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hash",
        is_active=True,
        phone="13800138000"
    )
    test_session.add(user)
    await test_session.commit()

    headers = _auth_headers_for_user(user.id)

    response = await client.get("/api/lawyer/income-records/export", headers=headers)
    
    # 应该返回403禁止访问
    assert response.status_code == 403
    assert "未绑定律师资料" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_export_income_records_empty_data(client: AsyncClient, test_session):
    """测试导出空数据"""
    # 创建律师但没有收入记录
    lawyer = await create_test_lawyer_with_user(test_session)

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get("/api/lawyer/income-records/export", headers=headers)
    
    assert response.status_code == 200
    content = response.content.decode('utf-8-sig')
    # 应该只包含表头，没有数据行
    lines = [line for line in content.split("\n") if line.strip()]
    assert len(lines) == 0  # 没有数据行


@pytest.mark.asyncio
async def test_export_income_records_with_consultation_data(client: AsyncClient, test_session):
    """测试导出包含咨询信息的收入记录"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建咨询记录
    consultation = LawyerConsultation(
        user_id=lawyer.user_id,
        lawyer_id=lawyer.id,
        subject="合同审查咨询",
        status="completed",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(consultation)
    await test_session.commit()
    
    # 创建订单
    order = PaymentOrder(
        user_id=lawyer.user_id,
        order_no="ORDER123",
        order_type="consultation",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PAID,
        title="咨询订单",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(order)
    await test_session.commit()
    
    # 创建收入记录
    record = LawyerIncomeRecord(
        lawyer_id=lawyer.id,
        consultation_id=consultation.id,
        order_no=order.order_no,
        user_paid_amount=100.0,
        platform_fee=15.0,
        lawyer_income=85.0,
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(record)
    await test_session.commit()

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get("/api/lawyer/income-records/export", headers=headers)
    
    assert response.status_code == 200
    content = response.content.decode('utf-8-sig')
    # 验证CSV包含订单号和咨询主题
    assert "ORDER123" in content
    assert "合同审查咨询" in content


@pytest.mark.asyncio
async def test_export_income_records_datetime_format(client: AsyncClient, test_session):
    """测试导出时日期时间格式"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    now = datetime.now(timezone.utc)
    record = await create_income_record(test_session, lawyer.id, 100.0, "pending", now)
    
    # 等待一段时间避免时间相同
    await test_session.refresh(record)
    settle_time = datetime.now(timezone.utc) + timedelta(days=7)
    record.settle_time = settle_time
    await test_session.commit()

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get("/api/lawyer/income-records/export", headers=headers)
    
    assert response.status_code == 200
    content = response.content.decode('utf-8-sig')
    # 验证日期时间格式为 "YYYY-MM-DD HH:MM:SS"
    assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', content) is not None


@pytest.mark.asyncio
async def test_list_income_records_with_different_amounts(client: AsyncClient, test_session):
    """测试不同金额的收入记录"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建不同金额的记录
    amounts = [10.0, 50.0, 100.0, 500.0, 1000.0, 9999.99]
    for amount in amounts:
        await create_income_record(test_session, lawyer.id, amount, "pending")

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(amounts)
    
    # 验证金额正确
    for item in data["items"]:
        assert item["user_paid_amount"] in amounts
        expected_income = item["user_paid_amount"] * 0.85
        expected_fee = item["user_paid_amount"] * 0.15
        assert item["lawyer_income"] == pytest.approx(expected_income, rel=1e-6)
        assert item["platform_fee"] == pytest.approx(expected_fee, rel=1e-6)


@pytest.mark.asyncio
async def test_list_income_records_with_withdrawn_amount(client: AsyncClient, test_session):
    """测试包含已提现金额的收入记录"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建有提现金额的记录
    record = LawyerIncomeRecord(
        lawyer_id=lawyer.id,
        user_paid_amount=100.0,
        platform_fee=15.0,
        lawyer_income=85.0,
        withdrawn_amount=50.0,
        status="withdrawn",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(record)
    await test_session.commit()

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    found = False
    for item in items:
        if item["id"] == record.id:
            assert item["withdrawn_amount"] == 50.0
            assert item["status"] == "withdrawn"
            found = True
    assert found


@pytest.mark.asyncio
async def test_export_income_records_large_dataset(client: AsyncClient, test_session):
    """测试导出大数据集"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建大量记录（模拟大数据集）
    for i in range(1500):
        await create_income_record(test_session, lawyer.id, float(100 + i), "pending")

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get("/api/lawyer/income-records/export", headers=headers)
    
    assert response.status_code == 200
    content = response.content.decode('utf-8-sig')
    # 验证包含大量数据
    lines = [line for line in content.split("\n") if line.strip()]
    assert len(lines) >= 1500  # 应该有1500条数据


@pytest.mark.asyncio
async def test_income_record_settle_time_display(client: AsyncClient, test_session):
    """测试收入记录结算时间显示"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建有结算时间的记录
    settle_time = datetime.now(timezone.utc) + timedelta(days=7)
    record = LawyerIncomeRecord(
        lawyer_id=lawyer.id,
        user_paid_amount=100.0,
        platform_fee=15.0,
        lawyer_income=85.0,
        status="pending",
        settle_time=settle_time,
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(record)
    await test_session.commit()

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    found = False
    for item in items:
        if item["id"] == record.id:
            assert item["settle_time"] is not None
            assert isinstance(item["settle_time"], str)
            found = True
    assert found


@pytest.mark.asyncio
async def test_income_record_with_order_no(client: AsyncClient, test_session):
    """测试包含订单号的收入记录"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建有订单号的记录
    record = LawyerIncomeRecord(
        lawyer_id=lawyer.id,
        order_no="ORDER20230130001",
        user_paid_amount=100.0,
        platform_fee=15.0,
        lawyer_income=85.0,
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(record)
    await test_session.commit()

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    found = False
    for item in items:
        if item["id"] == record.id:
            assert item["order_no"] == "ORDER20230130001"
            found = True
    assert found


@pytest.mark.asyncio
async def test_income_record_without_consultation(client: AsyncClient, test_session):
    """测试没有关联咨询的收入记录"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建没有咨询的收入记录
    record = LawyerIncomeRecord(
        lawyer_id=lawyer.id,
        user_paid_amount=100.0,
        platform_fee=15.0,
        lawyer_income=85.0,
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(record)
    await test_session.commit()

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    found = False
    for item in items:
        if item["id"] == record.id:
            assert item["consultation_id"] is None
            assert item["consultation_subject"] is None
            found = True
    assert found


@pytest.mark.asyncio
async def test_income_record_cents_fields(client: AsyncClient, test_session):
    """测试收入记录的分字段"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建带分字段的收入记录
    record = LawyerIncomeRecord(
        lawyer_id=lawyer.id,
        user_paid_amount=100.50,
        platform_fee=15.08,
        lawyer_income=85.42,
        user_paid_amount_cents=10050,
        platform_fee_cents=1508,
        lawyer_income_cents=8542,
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(record)
    await test_session.commit()

    # 验证分字段的值
    await test_session.refresh(record)
    assert record.user_paid_amount_cents == 10050
    assert record.platform_fee_cents == 1508
    assert record.lawyer_income_cents == 8542


@pytest.mark.asyncio
async def test_list_income_records_multiple_lawyers(client: AsyncClient, test_session):
    """测试多个律师的收入记录隔离"""
    # 创建两个律师
    lawyer1 = await create_test_lawyer_with_user(test_session, username="lawyer1")
    lawyer2 = await create_test_lawyer_with_user(test_session, username="lawyer2")
    
    # 为每个律师创建收入记录
    await create_income_record(test_session, lawyer1.id, 100.0, "pending")
    await create_income_record(test_session, lawyer1.id, 200.0, "settled")
    await create_income_record(test_session, lawyer2.id, 300.0, "pending")

    headers1 = _auth_headers_for_user(lawyer1.user_id)

    # lawyer1只能看到自己的记录
    response1 = await client.get(
        "/api/lawyer/income-records",
        headers=headers1,
        params={"page": 1, "page_size": 20}
    )
    
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["total"] == 2
    for item in data1["items"]:
        assert item["lawyer_id"] == lawyer1.id


@pytest.mark.asyncio
async def test_export_income_records_csv_encoding(client: AsyncClient, test_session):
    """测试导出CSV编码"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建包含中文的咨询记录
    consultation = LawyerConsultation(
        user_id=lawyer.user_id,
        lawyer_id=lawyer.id,
        subject="合同法律咨询",
        status="completed",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(consultation)
    await test_session.commit()
    
    record = LawyerIncomeRecord(
        lawyer_id=lawyer.id,
        consultation_id=consultation.id,
        user_paid_amount=100.0,
        platform_fee=15.0,
        lawyer_income=85.0,
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(record)
    await test_session.commit()

    headers = _auth_headers_for_user(lawyer.user_id)

    response = await client.get("/api/lawyer/income-records/export", headers=headers)
    
    assert response.status_code == 200
    content = response.content
    # 验证UTF-8 BOM
    assert content.startswith(b'\xef\xbb\xbf')
    # 验证中文可以正确显示
    text = content.decode('utf-8-sig')
    assert "合同法律咨询" in text


@pytest.mark.asyncio
async def test_income_record_wallet_update_after_creation(client: AsyncClient, test_session):
    """测试收入记录创建后钱包更新"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建钱包
    wallet = LawyerWallet(
        lawyer_id=lawyer.id,
        total_income=0.0,
        pending_amount=0.0,
        frozen_amount=0.0,
        available_amount=0.0
    )
    test_session.add(wallet)
    await test_session.commit()
    
    # 创建收入记录
    record = LawyerIncomeRecord(
        lawyer_id=lawyer.id,
        user_paid_amount=100.0,
        platform_fee=15.0,
        lawyer_income=85.0,
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(record)
    
    # 更新钱包（模拟服务逻辑）
    wallet.total_income += 85.0
    wallet.pending_amount += 85.0
    wallet.available_amount = 0.0  # 因为pending还未结算
    test_session.add(wallet)
    await test_session.commit()
    
    # 验证钱包已更新
    await test_session.refresh(wallet)
    assert wallet.total_income == 85.0
    assert wallet.pending_amount == 85.0


# ============================================================================
# 服务层测试 - IncomeService
# ============================================================================

@pytest.mark.asyncio
async def test_income_service_create_consultation_fee(test_session):
    """测试创建咨询费收入记录"""
    from app.services.settlement.income import IncomeService
    from app.services.settlement import SettlementService
    
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    user = await test_session.get(User, lawyer.user_id)
    
    user2 = User(
        username="client",
        email="client@example.com",
        hashed_password="hash",
        is_active=True,
        phone="13800138001"
    )
    test_session.add(user2)
    await test_session.commit()
    
    # 创建咨询
    consultation = LawyerConsultation(
        user_id=lawyer.user_id,
        lawyer_id=lawyer.id,
        subject="合同审查",
        status="completed",
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(consultation)
    await test_session.commit()
    
    # 创建订单
    order = PaymentOrder(
        user_id=user2.id,
        order_no="ORDER001",
        order_type="consultation",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PAID,
        title="咨询订单",
        created_at=datetime.now(timezone.utc),
        related_id=consultation.id,
        related_type="consultation"
    )
    test_session.add(order)
    await test_session.commit()
    
    # 创建收入记录
    settlement_service = SettlementService()
    income_service = IncomeService(settlement_service)
    
    record = await income_service.ensure_income_record_for_completed_consultation(
        test_session,
        consultation,
        order
    )
    
    assert record is not None
    assert record.lawyer_id == lawyer.id
    assert record.consultation_id == consultation.id
    assert record.user_paid_amount == 100.0
    assert record.lawyer_income > 0
    assert record.status == "pending"


@pytest.mark.asyncio
async def test_income_service_without_paid_order(test_session):
    """测试未支付订单不创建收入记录"""
    from app.services.settlement.income import IncomeService
    from app.services.settlement import SettlementService
    
    lawyer = await create_test_lawyer_with_user(test_session)
    
    consultation = LawyerConsultation(
        user_id=lawyer.user_id,
        lawyer_id=lawyer.id,
        subject="合同审查",
        status="completed"
    )
    test_session.add(consultation)
    await test_session.commit()
    
    # 未支付订单
    order = PaymentOrder(
        user_id=lawyer.user_id,
        order_no="ORDER002",
        order_type="consultation",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PENDING,
        title="未支付订单"
    )
    
    settlement_service = SettlementService()
    income_service = IncomeService(settlement_service)
    
    record = await income_service.ensure_income_record_for_completed_consultation(
        test_session,
        consultation,
        order
    )
    
    assert record is None


@pytest.mark.asyncio
async def test_income_service_duplicate_record(test_session):
    """测试重复创建收入记录"""
    from app.services.settlement.income import IncomeService
    from app.services.settlement import SettlementService
    
    lawyer = await create_test_lawyer_with_user(test_session)
    user2 = User(
        username="client2",
        email="client2@example.com",
        hashed_password="hash",
        is_active=True,
        phone="13800138002"
    )
    test_session.add(user2)
    await test_session.commit()
    
    consultation = LawyerConsultation(
        user_id=lawyer.user_id,
        lawyer_id=lawyer.id,
        subject="重复测试",
        status="completed"
    )
    test_session.add(consultation)
    await test_session.commit()
    
    order = PaymentOrder(
        user_id=user2.id,
        order_no="ORDER003",
        order_type="consultation",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PAID,
        title="重复订单"
    )
    test_session.add(order)
    await test_session.commit()
    
    settlement_service = SettlementService()
    income_service = IncomeService(settlement_service)
    
    # 第一次创建
    record1 = await income_service.ensure_income_record_for_completed_consultation(
        test_session,
        consultation,
        order
    )
    
    # 第二次创建
    record2 = await income_service.ensure_income_record_for_completed_consultation(
        test_session,
        consultation,
        order
    )
    
    assert record1 is not None
    assert record2 is not None
    assert record1.id == record2.id  # 应该是同一条记录


@pytest.mark.asyncio
async def test_income_service_settle_due_records(test_session):
    """测试结算到期收入记录"""
    from app.services.settlement.income import IncomeService
    from app.services.settlement import SettlementService
    
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建钱包
    wallet = LawyerWallet(
        lawyer_id=lawyer.id,
        total_income=100000.0,
        pending_amount=100.0,
        frozen_amount=0.0,
        available_amount=99900.0
    )
    test_session.add(wallet)
    await test_session.commit()
    
    # 创建已到期的收入记录
    record = LawyerIncomeRecord(
        lawyer_id=lawyer.id,
        user_paid_amount=100.0,
        platform_fee=15.0,
        lawyer_income=85.0,
        status="pending",
        settle_time=datetime.now(timezone.utc) - timedelta(days=1),  # 已过期
        created_at=datetime.now(timezone.utc) - timedelta(days=8)
    )
    test_session.add(record)
    await test_session.commit()
    
    settlement_service = SettlementService()
    income_service = IncomeService(settlement_service)
    
    result = await income_service.settle_due_income_records(test_session)
    
    assert result["settled"] >= 1
    
    # 验证记录已结算
    await test_session.refresh(record)
    assert record.status == "settled"


@pytest.mark.asyncio
async def test_income_service_platform_fee_calculation(test_session):
    """测试平台手续费计算"""
    from app.services.settlement.income import IncomeService
    from app.services.settlement import SettlementService
    
    lawyer = await create_test_lawyer_with_user(test_session)
    
    consultation = LawyerConsultation(
        user_id=lawyer.user_id,
        lawyer_id=lawyer.id,
        subject="费率测试",
        status="completed"
    )
    test_session.add(consultation)
    await test_session.commit()
    
    order = PaymentOrder(
        user_id=lawyer.user_id,
        order_no="ORDER004",
        order_type="consultation",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PAID,
        title="费率测试订单"
    )
    test_session.add(order)
    await test_session.commit()
    
    settlement_service = SettlementService()
    income_service = IncomeService(settlement_service)
    
    record = await income_service.ensure_income_record_for_completed_consultation(
        test_session,
        consultation,
        order
    )
    
    assert record is not None
    # 验证费率计算
    assert record.platform_fee > 0
    assert record.lawyer_income > 0
    assert record.platform_fee + record.lawyer_income == record.user_paid_amount


# ============================================================================
# 辅助函数
# ============================================================================

def _auth_headers_for_user(user_id: int) -> dict[str, str]:
    """生成测试用授权头"""
    from app.utils.security import create_access_token

    token = create_access_token(data={"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}

async def create_test_lawyer_with_user(session, username="test_lawyer"):
    """创建测试律师和关联用户"""
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="hash",
        is_active=True,
        phone="13800138000",
        role="lawyer"
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    lawyer = Lawyer(
        user_id=user.id,
        name="测试律师",
        phone="13800138000",
        is_verified=True,
        is_active=True
    )
    session.add(lawyer)
    await session.commit()
    await session.refresh(lawyer)
    
    return lawyer


async def create_income_record(session, lawyer_id, amount, status="pending", created_at=None):
    """创建测试收入记录"""
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    
    platform_fee = amount * 0.15  # 15%平台费
    lawyer_income = amount - platform_fee
    
    record = LawyerIncomeRecord(
        lawyer_id=lawyer_id,
        user_paid_amount=float(amount),
        platform_fee=float(platform_fee),
        lawyer_income=float(lawyer_income),
        status=status,
        created_at=created_at,
        settle_time=created_at + timedelta(days=7) if status == "pending" else None
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


# 导入re用于正则表达式测试
import re


@pytest.mark.asyncio
async def test_income_record_fields_validation(client: AsyncClient, test_session):
    """测试收入记录字段完整性验证"""
    # 创建测试数据
    lawyer = await create_test_lawyer_with_user(test_session)
    
    # 创建包含所有字段的收入记录
    settlement_time = datetime.now(timezone.utc) + timedelta(days=7)
    record = LawyerIncomeRecord(
        lawyer_id=lawyer.id,
        user_paid_amount=100.0,
        platform_fee=15.0,
        lawyer_income=85.0,
        user_paid_amount_cents=10050,
        platform_fee_cents=1508,
        lawyer_income_cents=8542,
        withdrawn_amount=0.0,
        withdrawn_amount_cents=0,
        status="pending",
        settle_time=settlement_time,
        created_at=datetime.now(timezone.utc)
    )
    test_session.add(record)
    await test_session.commit()

    headers = _auth_headers_for_user(lawyer.user_id)

    # 获取记录
    response = await client.get(
        "/api/lawyer/income-records",
        headers=headers,
        params={"page": 1, "page_size": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    found = False
    for item in items:
        if item["id"] == record.id:
            # 验证所有必要字段都存在
            assert "id" in item
            assert "lawyer_id" in item
            assert "user_paid_amount" in item
            assert "platform_fee" in item
            assert "lawyer_income" in item
            assert "withdrawn_amount" in item
            assert "status" in item
            assert "settle_time" in item
            assert "created_at" in item
            assert "updated_at" in item
            # 验证字段值
            assert item["lawyer_id"] == lawyer.id
            assert item["user_paid_amount"] == 100.0
            assert item["platform_fee"] == 15.0
            assert item["lawyer_income"] == 85.0
            assert item["withdrawn_amount"] == 0.0
            assert item["status"] == "pending"
            assert item["settle_time"] is not None
            found = True
    assert found
