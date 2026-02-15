"""
文档导出性能测试

测试PDF和Word生成的性能指标，包括执行时间、内存使用、并发性能等。
"""

import asyncio
import gc
import time
import tracemalloc
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contracts import ContractReviewHistory
from app.services.document_export.pdf_generator import PDFGenerationError, generate_contract_pdf
from app.services.document_export.word_generator import WordGenerationError, generate_contract_word


# ============================================================================
# 辅助函数
# ============================================================================

def _create_test_review(
    risk_count: int = 5,
    edit_count: int = 3,
    missing_count: int = 2,
    risk_level: str = "medium",
    filename: str = "test_contract.pdf",
) -> ContractReviewHistory:
    """
    创建测试用审查记录
    
    Args:
        risk_count: 风险项数量
        edit_count: 建议修改数量
        missing_count: 缺失条款数量
        risk_level: 风险等级
        filename: 文件名
    
    Returns:
        ContractReviewHistory: 审查记录对象
    """
    review = ContractReviewHistory(
        id=f"review_{int(time.time() * 1000)}",
        user_id=1,
        filename=filename,
        contract_type="劳动合同",
        content_type="application/pdf",
        text_chars=5000,
        text_preview="合同文本预览内容...",
        risk_level=risk_level,
        risk_count=risk_count,
        request_id=f"req_{int(time.time() * 1000)}",
        report_markdown="# 测试报告",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    # 构建report_json
    report_json = {
        "risk_level": risk_level,
        "risk_count": risk_count,
        "risk_items": [],
        "recommended_edits": [],
        "missing_clauses": [],
    }
    
    # 添加风险项
    for i in range(risk_count):
        risk_item = {
            "title": f"风险项 {i+1}",
            "type": "法律风险" if i % 2 == 0 else "合规风险",
            "severity": "高" if i < 2 else "中" if i < 4 else "低",
            "location": f"第 {i*2+1} 条",
            "description": f"这是第 {i+1} 个风险项的详细描述。" * (5 if risk_count > 10 else 2),
            "legal_basis": f"《劳动合同法》第{i+10}条" * (2 if risk_count > 10 else 1),
            "suggestion": f"建议修改为：{i+1}..." * (3 if risk_count > 10 else 1),
        }
        report_json["risk_items"].append(risk_item)
    
    # 添加建议修改
    for i in range(edit_count):
        edit = {
            "location": f"第 {i+10} 条",
            "original": f"原文内容 {i+1}。" * (3 if edit_count > 8 else 1),
            "suggested": f"修改后内容 {i+1}。" * (3 if edit_count > 8 else 1),
        }
        report_json["recommended_edits"].append(edit)
    
    # 添加缺失条款
    for i in range(missing_count):
        clause = {
            "type": f"条款类型 {i+1}",
            "description": f"缺失条款描述 {i+1}。" * (4 if missing_count > 5 else 1),
            "suggested_text": f"建议添加的条款文本 {i+1}。" * (4 if missing_count > 5 else 1),
        }
        report_json["missing_clauses"].append(clause)
    
    review.report_json = report_json
    return review


async def _mock_get_review_detail(db: AsyncSession, review_id: str) -> Any:
    """
    模拟获取审查详情
    
    Args:
        db: 数据库会话
        review_id: 审查记录ID
    
    Returns:
        审查记录对象
    """
    # 根据review_id生成不同规模的测试数据
    if "small" in review_id:
        return _create_test_review(risk_count=5, edit_count=3, missing_count=2, filename="小规模报告.pdf")
    elif "large" in review_id:
        return _create_test_review(
            risk_count=20, edit_count=15, missing_count=8, filename="大规模报告.pdf", risk_level="high"
        )
    else:
        return _create_test_review(risk_count=10, edit_count=8, missing_count=4)


def _print_performance_metrics(
    test_name: str,
    execution_time: float,
    memory_used_mb: float,
    expected_time: float,
    passed: bool,
) -> None:
    """
    打印性能指标
    
    Args:
        test_name: 测试名称
        execution_time: 执行时间（秒）
        memory_used_mb: 内存使用（MB）
        expected_time: 预期时间（秒）
        passed: 是否通过
    """
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"\n{'='*70}")
    print(f"测试用例: {test_name}")
    print(f"{'='*70}")
    print(f"状态: {status}")
    print(f"执行时间: {execution_time:.4f} 秒")
    print(f"预期时间: < {expected_time:.2f} 秒")
    print(f"内存使用: {memory_used_mb:.2f} MB")
    print(f"时间性能: {((expected_time/execution_time)*100):.1f}%")
    print(f"{'='*70}\n")


# ============================================================================
# PDF生成性能测试
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.performance
async def test_pdf_generation_performance_small_report():
    """
    测试小规模报告PDF生成性能（预期<2秒）
    
    测试场景：5个风险项、3个建议修改、2个缺失条款的小型报告
    """
    # 跳过测试如果weasyprint不可用
    try:
        from weasyprint import HTML  # noqa: F401
    except ImportError:
        pytest.skip("weasyprint未安装，跳过PDF生成测试")
    
    review_id = f"small_review_{int(time.time())}"
    
    # 开始内存跟踪
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    
    # 测量执行时间
    start_time = time.time()
    
    try:
        with patch(
            "app.services.document_export.pdf_generator.ContractHistoryService.get_review_detail",
            side_effect=_mock_get_review_detail,
        ):
            # 创建模拟数据库会话
            db = MagicMock(spec=AsyncSession)
            
            # 生成PDF
            pdf_bytes = await generate_contract_pdf(
                db=db,
                review_id=review_id,
                options={"includeDetailedRisks": True, "includeRecommendedEdits": True, "includeMissingClauses": True},
            )
            
            execution_time = time.time() - start_time
            
            # 测量内存使用
            snapshot_after = tracemalloc.take_snapshot()
            top_stats = snapshot_after.compare_to(snapshot_before, "lineno")
            memory_used = sum(stat.size_diff for stat in top_stats) / (1024 * 1024)
            
            # 性能断言
            assert pdf_bytes is not None, "PDF生成失败"
            assert len(pdf_bytes) > 1000, "PDF文件过小"
            assert execution_time < 2.0, f"小规模PDF生成时间 {execution_time:.4f}s 超过预期 2.0s"
            assert memory_used < 20, f"内存使用 {memory_used:.2f}MB 超过预期 20MB"
            
            # 打印性能指标
            _print_performance_metrics(
                test_name="test_pdf_generation_performance_small_report",
                execution_time=execution_time,
                memory_used_mb=memory_used,
                expected_time=2.0,
                passed=True,
            )
            
            print(f"PDF文件大小: {len(pdf_bytes)} bytes")
            
    finally:
        tracemalloc.stop()
        gc.collect()


@pytest.mark.asyncio
@pytest.mark.performance
async def test_pdf_generation_performance_large_report():
    """
    测试大规模报告PDF生成性能（预期<5秒）
    
    测试场景：20个风险项、15个建议修改、8个缺失条款的大型报告
    """
    try:
        from weasyprint import HTML  # noqa: F401
    except ImportError:
        pytest.skip("weasyprint未安装，跳过PDF生成测试")
    
    review_id = f"large_review_{int(time.time())}"
    
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    
    start_time = time.time()
    
    try:
        with patch(
            "app.services.document_export.pdf_generator.ContractHistoryService.get_review_detail",
            side_effect=_mock_get_review_detail,
        ):
            db = MagicMock(spec=AsyncSession)
            
            pdf_bytes = await generate_contract_pdf(
                db=db,
                review_id=review_id,
                options={"includeDetailedRisks": True, "includeRecommendedEdits": True, "includeMissingClauses": True},
            )
            
            execution_time = time.time() - start_time
            
            snapshot_after = tracemalloc.take_snapshot()
            top_stats = snapshot_after.compare_to(snapshot_before, "lineno")
            memory_used = sum(stat.size_diff for stat in top_stats) / (1024 * 1024)
            
            assert pdf_bytes is not None, "PDF生成失败"
            assert len(pdf_bytes) > 5000, "PDF文件过小"
            assert execution_time < 5.0, f"大规模PDF生成时间 {execution_time:.4f}s 超过预期 5.0s"
            assert memory_used < 50, f"内存使用 {memory_used:.2f}MB 超过预期 50MB"
            
            _print_performance_metrics(
                test_name="test_pdf_generation_performance_large_report",
                execution_time=execution_time,
                memory_used_mb=memory_used,
                expected_time=5.0,
                passed=True,
            )
            
            print(f"PDF文件大小: {len(pdf_bytes)} bytes")
            
    finally:
        tracemalloc.stop()
        gc.collect()


# ============================================================================
# Word生成性能测试
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.performance
async def test_word_generation_performance_small_report():
    """
    测试小规模报告Word生成性能（预期<1秒）
    
    测试场景：5个风险项、3个建议修改、2个缺失条款的小型报告
    """
    try:
        from docx import Document  # noqa: F401
    except ImportError:
        pytest.skip("python-docx未安装，跳过Word生成测试")
    
    review_id = f"small_word_review_{int(time.time())}"
    
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    
    start_time = time.time()
    
    try:
        with patch(
            "app.services.document_export.word_generator.ContractHistoryService.get_review_detail",
            side_effect=_mock_get_review_detail,
        ):
            db = MagicMock(spec=AsyncSession)
            
            word_bytes = await generate_contract_word(
                db=db,
                review_id=review_id,
                options={"includeDetailedRisks": True, "includeRecommendedEdits": True, "includeMissingClauses": True},
            )
            
            execution_time = time.time() - start_time
            
            snapshot_after = tracemalloc.take_snapshot()
            top_stats = snapshot_after.compare_to(snapshot_before, "lineno")
            memory_used = sum(stat.size_diff for stat in top_stats) / (1024 * 1024)
            
            assert word_bytes is not None, "Word生成失败"
            assert len(word_bytes) > 1000, "Word文件过小"
            assert execution_time < 1.0, f"小规模Word生成时间 {execution_time:.4f}s 超过预期 1.0s"
            assert memory_used < 15, f"内存使用 {memory_used:.2f}MB 超过预期 15MB"
            
            _print_performance_metrics(
                test_name="test_word_generation_performance_small_report",
                execution_time=execution_time,
                memory_used_mb=memory_used,
                expected_time=1.0,
                passed=True,
            )
            
            print(f"Word文件大小: {len(word_bytes)} bytes")
            
    finally:
        tracemalloc.stop()
        gc.collect()


@pytest.mark.asyncio
@pytest.mark.performance
async def test_word_generation_performance_large_report():
    """
    测试大规模报告Word生成性能（预期<3秒）
    
    测试场景：20个风险项、15个建议修改、8个缺失条款的大型报告
    """
    try:
        from docx import Document  # noqa: F401
    except ImportError:
        pytest.skip("python-docx未安装，跳过Word生成测试")
    
    review_id = f"large_word_review_{int(time.time())}"
    
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    
    start_time = time.time()
    
    try:
        with patch(
            "app.services.document_export.word_generator.ContractHistoryService.get_review_detail",
            side_effect=_mock_get_review_detail,
        ):
            db = MagicMock(spec=AsyncSession)
            
            word_bytes = await generate_contract_word(
                db=db,
                review_id=review_id,
                options={"includeDetailedRisks": True, "includeRecommendedEdits": True, "includeMissingClauses": True},
            )
            
            execution_time = time.time() - start_time
            
            snapshot_after = tracemalloc.take_snapshot()
            top_stats = snapshot_after.compare_to(snapshot_before, "lineno")
            memory_used = sum(stat.size_diff for stat in top_stats) / (1024 * 1024)
            
            assert word_bytes is not None, "Word生成失败"
            assert len(word_bytes) > 5000, "Word文件过小"
            assert execution_time < 3.0, f"大规模Word生成时间 {execution_time:.4f}s 超过预期 3.0s"
            assert memory_used < 30, f"内存使用 {memory_used:.2f}MB 超过预期 30MB"
            
            _print_performance_metrics(
                test_name="test_word_generation_performance_large_report",
                execution_time=execution_time,
                memory_used_mb=memory_used,
                expected_time=3.0,
                passed=True,
            )
            
            print(f"Word文件大小: {len(word_bytes)} bytes")
            
    finally:
        tracemalloc.stop()
        gc.collect()


# ============================================================================
# 缓存优化测试
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.performance
async def test_pdf_generation_caching_optimization():
    """
    测试CSS缓存优化效果
    
    验证多次生成PDF时，缓存的CSS是否带来性能提升
    """
    try:
        from weasyprint import HTML  # noqa: F401
    except ImportError:
        pytest.skip("weasyprint未安装，跳过PDF生成测试")
    
    review_ids = [f"cache_test_{i}_{int(time.time())}" for i in range(5)]
    
    with patch(
        "app.services.document_export.pdf_generator.ContractHistoryService.get_review_detail",
        side_effect=_mock_get_review_detail,
    ):
        db = MagicMock(spec=AsyncSession)
        
        # 第一次生成（CSS需要加载）
        tracemalloc.start()
        snapshot_before = tracemalloc.take_snapshot()
        
        start_time = time.time()
        pdf_bytes_1 = await generate_contract_pdf(db=db, review_id=review_ids[0])
        first_gen_time = time.time() - start_time
        
        snapshot_after = tracemalloc.take_snapshot()
        first_gen_memory = sum(stat.size_diff for stat in snapshot_after.compare_to(snapshot_before, "lineno")) / (1024 * 1024)
        
        tracemalloc.stop()
        gc.collect()
        
        # 后续几次生成（CSS已缓存）
        subsequent_times = []
        subsequent_memories = []
        
        for i in range(1, 5):
            tracemalloc.start()
            snapshot_before = tracemalloc.take_snapshot()
            
            start_time = time.time()
            pdf_bytes = await generate_contract_pdf(db=db, review_id=review_ids[i])
            gen_time = time.time() - start_time
            
            snapshot_after = tracemalloc.take_snapshot()
            memory_used = sum(stat.size_diff for stat in snapshot_after.compare_to(snapshot_before, "lineno")) / (1024 * 1024)
            
            subsequent_times.append(gen_time)
            subsequent_memories.append(memory_used)
            
            tracemalloc.stop()
            gc.collect()
        
        avg_subsequent_time = sum(subsequent_times) / len(subsequent_times)
        avg_subsequent_memory = sum(subsequent_memories) / len(subsequent_memories)
        
        # 打印结果
        print(f"\n{'='*70}")
        print(f"CSS缓存优化测试结果")
        print(f"{'='*70}")
        print(f"首次生成时间: {first_gen_time:.4f} 秒")
        print(f"首次生成内存: {first_gen_memory:.2f} MB")
        print(f"后续平均时间: {avg_subsequent_time:.4f} 秒")
        print(f"后续平均内存: {avg_subsequent_memory:.2f} MB")
        
        if avg_subsequent_time < first_gen_time:
            improvement = ((first_gen_time - avg_subsequent_time) / first_gen_time) * 100
            print(f"时间优化: {improvement:.1f}%")
        
        if avg_subsequent_memory < first_gen_memory:
            improvement = ((first_gen_memory - avg_subsequent_memory) / first_gen_memory) * 100
            print(f"内存优化: {improvement:.1f}%")
        
        print(f"{'='*70}\n")
        
        # 性能断言：后续生成应该更快或相当
        assert avg_subsequent_time <= first_gen_time * 1.2, "缓存优化效果不明显"
        assert avg_subsequent_memory <= first_gen_memory * 1.2, "缓存内存优化效果不明显"


# ============================================================================
# 并发性能测试
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.performance
async def test_concurrent_generation_performance():
    """
    测试并发生成性能
    
    测试同时生成多个PDF和Word文档的性能表现
    """
    try:
        from weasyprint import HTML  # noqa: F401
        from docx import Document  # noqa: F401
    except ImportError:
        pytest.skip("缺少必要的依赖，跳过并发测试")
    
    review_ids_pdf = [f"concurrent_pdf_{i}_{int(time.time())}" for i in range(5)]
    review_ids_word = [f"concurrent_word_{i}_{int(time.time())}" for i in range(5)]
    
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    
    start_time = time.time()
    
    try:
        with patch(
            "app.services.document_export.pdf_generator.ContractHistoryService.get_review_detail",
            side_effect=_mock_get_review_detail,
        ), patch(
            "app.services.document_export.word_generator.ContractHistoryService.get_review_detail",
            side_effect=_mock_get_review_detail,
        ):
            db = MagicMock(spec=AsyncSession)
            
            # 并发生成PDF和Word
            tasks = []
            
            for review_id in review_ids_pdf:
                tasks.append(generate_contract_pdf(db=db, review_id=review_id))
            
            for review_id in review_ids_word:
                tasks.append(generate_contract_word(db=db, review_id=review_id))
            
            results = await asyncio.gather(*tasks)
            
            total_time = time.time() - start_time
            avg_time_per_doc = total_time / len(results)
            
            snapshot_after = tracemalloc.take_snapshot()
            peak_memory = tracemalloc.get_traced_memory()[1] / (1024 * 1024)
            
            # 验证结果
            assert len(results) == 10, "未生成所有文档"
            assert all(result is not None for result in results), "部分文档生成失败"
            
            # 打印结果
            print(f"\n{'='*70}")
            print(f"并发生成性能测试结果")
            print(f"{'='*70}")
            print(f"并发文档数: 10 (5 PDF + 5 Word)")
            print(f"总执行时间: {total_time:.4f} 秒")
            print(f"平均每文档: {avg_time_per_doc:.4f} 秒")
            print(f"峰值内存: {peak_memory:.2f} MB")
            print(f"{'='*70}\n")
            
            # 性能断言
            assert total_time < 8.0, f"并发总时间 {total_time:.4f}s 超过预期 8.0s"
            assert avg_time_per_doc < 2.0, f"平均时间 {avg_time_per_doc:.4f}s 超过预期 2.0s"
            assert peak_memory < 100, f"峰值内存 {peak_memory:.2f}MB 超过预期 100MB"
            
    finally:
        tracemalloc.stop()
        gc.collect()


# ============================================================================
# 内存效率测试
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.performance
async def test_pdf_memory_efficiency():
    """
    测试PDF生成的内存效率
    
    验证内存使用是否合理，是否有内存泄漏
    """
    try:
        from weasyprint import HTML  # noqa: F401
    except ImportError:
        pytest.skip("weasyprint未安装，跳过PDF生成测试")
    
    review_ids = [f"memory_test_{i}_{int(time.time())}" for i in range(10)]
    memory_snapshots = []
    
    with patch(
        "app.services.document_export.pdf_generator.ContractHistoryService.get_review_detail",
        side_effect=_mock_get_review_detail,
    ):
        db = MagicMock(spec=AsyncSession)
        
        # 连续生成10次PDF，记录每次的内存使用
        for i, review_id in enumerate(review_ids):
            tracemalloc.start()
            snapshot_before = tracemalloc.take_snapshot()
            
            await generate_contract_pdf(db=db, review_id=review_id)
            
            snapshot_after = tracemalloc.take_snapshot()
            memory_used = sum(stat.size_diff for stat in snapshot_after.compare_to(snapshot_before, "lineno")) / (1024 * 1024)
            memory_snapshots.append(memory_used)
            
            tracemalloc.stop()
            gc.collect()
        
        avg_memory = sum(memory_snapshots) / len(memory_snapshots)
        max_memory = max(memory_snapshots)
        min_memory = min(memory_snapshots)
        
        # 检查内存增长趋势（最后3次 vs 前3次）
        early_avg = sum(memory_snapshots[:3]) / 3
        late_avg = sum(memory_snapshots[-3:]) / 3
        memory_growth = ((late_avg - early_avg) / early_avg) * 100 if early_avg > 0 else 0
        
        # 打印结果
        print(f"\n{'='*70}")
        print(f"PDF内存效率测试结果")
        print(f"{'='*70}")
        print(f"测试次数: 10")
        print(f"平均内存: {avg_memory:.2f} MB")
        print(f"最小内存: {min_memory:.2f} MB")
        print(f"最大内存: {max_memory:.2f} MB")
        print(f"早期平均: {early_avg:.2f} MB (前3次)")
        print(f"后期平均: {late_avg:.2f} MB (后3次)")
        print(f"内存增长: {memory_growth:.1f}%")
        print(f"{'='*70}\n")
        
        # 性能断言
        assert avg_memory < 25, f"平均内存 {avg_memory:.2f}MB 超过预期 25MB"
        assert max_memory < 35, f"最大内存 {max_memory:.2f}MB 超过预期 35MB"
        assert abs(memory_growth) < 30, f"内存增长 {memory_growth:.1f}% 超过预期 30%，可能存在内存泄漏"


# ============================================================================
# 性能基准测试
# ============================================================================


@pytest.mark.performance
def test_performance_benchmark_summary():
    """
    性能基准测试总结
    
    打印所有性能基准指标
    """
    print(f"\n{'='*70}")
    print(f"文档导出性能基准")
    print(f"{'='*70}")
    print(f"{'测试用例':<40} {'预期时间':<12} {'预期内存':<12}")
    print(f"{'-'*70}")
    print(f"{'小规模PDF生成':<40} {'< 2.0s':<12} {'< 20MB':<12}")
    print(f"{'大规模PDF生成':<40} {'< 5.0s':<12} {'< 50MB':<12}")
    print(f"{'小规模Word生成':<40} {'< 1.0s':<12} {'< 15MB':<12}")
    print(f"{'大规模Word生成':<40} {'< 3.0s':<12} {'< 30MB':<12}")
    print(f"{'并发生成（10个文档）':<40} {'< 8.0s':<12} {'< 100MB':<12}")
    print(f"{'内存泄漏测试':<40} {'N/A':<12} {'< 30%增长':<12}")
    print(f"{'='*70}\n")


# ============================================================================
# 测试组织
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance", "-s"])
