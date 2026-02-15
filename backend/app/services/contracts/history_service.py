from __future__ import annotations

import uuid
from typing import cast

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.contracts import ContractReviewHistory
from ...models.user import User
from ...schemas.contracts import (
    ContractCompareResponse,
    ContractDiffItem,
    ContractReviewHistoryItem,
    ContractReviewHistoryListResponse,
)
from ...utils.pii import sanitize_pii


class ContractHistoryService:
    """合同审查历史服务"""
    
    @staticmethod
    async def create_review_history(
        db: AsyncSession,
        user_id: int | None,
        filename: str,
        content_type: str | None,
        text_chars: int,
        text_preview: str,
        report_json: dict,
        report_markdown: str,
        request_id: str,
        focus: str | None = None,
        contract_type: str | None = None,
    ) -> ContractReviewHistory:
        """创建审查历史记录"""
        # 计算风险等级和数量
        risks = report_json.get("risks", [])
        risk_count = len(risks)
        risk_level = "low"
        
        if risk_count > 0:
            # 根据最高风险等级确定整体等级
            severity_priority = {"high": 3, "medium": 2, "low": 1}
            max_severity = max(
                (severity_priority.get(risk.get("severity", "low"), 1) for risk in risks),
                default=1
            )
            if max_severity == 3:
                risk_level = "high"
            elif max_severity == 2:
                risk_level = "medium"
            else:
                risk_level = "low"
        
        # 提取合同类型
        if not contract_type:
            contract_type = report_json.get("contract_type", "未知合同")
        
        history = ContractReviewHistory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            filename=sanitize_pii(filename),
            contract_type=contract_type,
            content_type=content_type,
            text_chars=text_chars,
            text_preview=sanitize_pii(text_preview[:1000]) if text_preview else "",
            risk_level=risk_level,
            risk_count=risk_count,
            report_json=report_json,
            report_markdown=report_markdown,
            request_id=request_id,
            focus=sanitize_pii(focus) if focus else None,
        )
        
        db.add(history)
        await db.commit()
        await db.refresh(history)
        
        return history
    
    @staticmethod
    async def get_review_history(
        db: AsyncSession,
        user_id: int | None,
        page: int = 1,
        page_size: int = 10,
    ) -> ContractReviewHistoryListResponse:
        """获取审查历史列表"""
        query = select(ContractReviewHistory)
        
        if user_id is not None:
            query = query.where(ContractReviewHistory.user_id == user_id)
        
        # 计算总数
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = cast(int, total_result.scalar())
        
        # 分页查询
        query = query.order_by(ContractReviewHistory.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        return ContractReviewHistoryListResponse(
            items=[
                ContractReviewHistoryItem(
                    id=item.id,
                    filename=item.filename,
                    contract_type=item.contract_type,
                    risk_level=item.risk_level,
                    risk_count=item.risk_count,
                    request_id=item.request_id,
                    created_at=item.created_at,
                )
                for item in items
            ],
            total=total,
            page=page,
            page_size=page_size,
        )
    
    @staticmethod
    async def get_review_detail(
        db: AsyncSession,
        review_id: str,
    ) -> ContractReviewHistory | None:
        """获取审查详情"""
        query = select(ContractReviewHistory).where(ContractReviewHistory.id == review_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_review(
        db: AsyncSession,
        review_id: str,
        user_id: int | None,
    ) -> bool:
        """删除审查记录"""
        query = delete(ContractReviewHistory).where(ContractReviewHistory.id == review_id)
        
        if user_id is not None:
            query = query.where(ContractReviewHistory.user_id == user_id)
        
        result = await db.execute(query)
        await db.commit()
        
        return result.rowcount > 0


class ContractCompareService:
    """合同比对服务"""
    
    @staticmethod
    async def compare_contracts(
        original_text: str,
        new_text: str,
        original_filename: str,
        new_filename: str,
    ) -> ContractCompareResponse:
        """比对两个合同的差异"""
        import difflib
        
        # 使用difflib进行文本比对
        differ = difflib.Differ()
        diff = list(differ.compare(original_text.splitlines(), new_text.splitlines()))
        
        # 解析差异
        differences: list[ContractDiffItem] = []
        current_line = 0
        current_page = 1
        
        added = 0
        removed = 0
        modified = 0
        
        for line in diff:
            current_line += 1
            # 简单模拟页码（每50行为一页）
            if current_line % 50 == 0:
                current_page += 1
            
            line_str = line[2:]  # 去掉差异标记前两个字符
            
            if line.startswith("+  "):
                # 新增行
                if line_str.strip():
                    differences.append(
                        ContractDiffItem(
                            type="add",
                            content=line_str.strip(),
                            position={"page": current_page, "line": current_line},
                        )
                    )
                    added += 1
            elif line.startswith("-  "):
                # 删除行
                if line_str.strip():
                    differences.append(
                        ContractDiffItem(
                            type="remove",
                            content=line_str.strip(),
                            position={"page": current_page, "line": current_line},
                        )
                    )
                    removed += 1
            elif line.startswith("? "):
                # 差异标记行（跳过）
                pass
            elif line.startswith("  "):
                # 未修改行（跳过）
                pass
            else:
                # 修改行（difflib中的^行）
                if "?" not in line and line_str.strip():
                    # 这可能是修改的行的一部分
                    differences.append(
                        ContractDiffItem(
                            type="modify",
                            content=line_str.strip(),
                            position={"page": current_page, "line": current_line},
                        )
                    )
                    modified += 1
        
        return ContractCompareResponse(
            original_filename=original_filename,
            new_filename=new_filename,
            differences=differences,
            summary={"added": added, "removed": removed, "modified": modified},
            request_id=str(uuid.uuid4()),
        )


def sanitize_text_preview(text: str, max_length: int = 1000) -> str:
    """清理文本预览"""
    if not text:
        return ""
    
    # 去除多余空行
    lines = [line for line in text.splitlines() if line.strip()]
    preview = "\n".join(lines)
    
    # 截断
    if len(preview) > max_length:
        preview = preview[:max_length] + "..."
    
    return preview