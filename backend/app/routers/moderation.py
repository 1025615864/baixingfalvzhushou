from datetime import datetime
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/moderation", tags=["Moderation"])


_mock_queue: list[dict] = [
    {
        "id": "md-001", "content_type": "post", "title": "请问劳动仲裁需要准备哪些材料？",
        "content_preview": "我在公司工作了三年，最近被无故辞退，想申请劳动仲裁，但不太清楚需要准备什么材料...",
        "author_name": "张先生", "submit_time": "2025-05-12T14:30:00", "status": "pending", "priority": "medium",
    },
    {
        "id": "md-002", "content_type": "comment", "title": "评论：交通事故责任认定",
        "content_preview": "这个律师就是在胡说八道，我上次找他咨询完全没用，建议大家别找他，加我微信xxx了解更多...",
        "author_name": "愤怒的用户", "submit_time": "2025-05-12T13:15:00", "status": "pending", "priority": "high",
    },
    {
        "id": "md-003", "content_type": "review", "title": "王律师服务评价",
        "content_preview": "王律师非常专业，帮我处理了房产纠纷案子，态度好、收费合理，强烈推荐！",
        "author_name": "李女士", "submit_time": "2025-05-12T11:00:00", "status": "pending", "priority": "low",
    },
    {
        "id": "md-004", "content_type": "lawyer", "title": "律师认证申请 - 赵明远",
        "content_preview": "赵明远，执业证号：14401201810xxxxxx，执业机构：北京大成律师事务所，执业年限：12年，擅长领域：刑事辩护、企业法律顾问...",
        "author_name": "赵明远", "submit_time": "2025-05-12T10:30:00", "status": "pending", "priority": "high",
    },
    {
        "id": "md-005", "content_type": "post", "title": "离婚后子女抚养权变更流程",
        "content_preview": "离婚两年了，孩子一直跟着前妻，现在前妻再婚了，孩子跟我反映继父对他不好，我想变更抚养权...",
        "author_name": "刘先生", "submit_time": "2025-05-12T09:00:00", "status": "pending", "priority": "medium",
    },
    {
        "id": "md-006", "content_type": "comment", "title": "评论：合同纠纷案例分享",
        "content_preview": "很有用的案例分享，收藏了。我之前也遇到过类似情况，最后通过调解解决了。",
        "author_name": "法律爱好者", "submit_time": "2025-05-12T08:45:00", "status": "pending", "priority": "low",
    },
    {
        "id": "md-007", "content_type": "review", "title": "调解服务评价",
        "content_preview": "根本没用！等了半个月才安排调解，结果对方根本没来，平台也不管，浪费我时间！",
        "author_name": "陈先生", "submit_time": "2025-05-11T16:00:00", "status": "pending", "priority": "medium",
    },
    {
        "id": "md-008", "content_type": "post", "title": "公司拖欠工资怎么办？",
        "content_preview": "已经三个月没发工资了，老板说公司资金周转困难，让我们再等等，合同也没签，怎么办？",
        "author_name": "王女士", "submit_time": "2025-05-11T15:20:00", "status": "pending", "priority": "high",
    },
    {
        "id": "md-009", "content_type": "lawyer", "title": "律师认证申请 - 孙晓琳",
        "content_preview": "孙晓琳，执业证号：13101202xxxxxxxx，执业机构：上海锦天城律师事务所，执业年限：8年，擅长领域：婚姻家事、遗产继承...提供的执业证照片模糊不清，需核实。",
        "author_name": "孙晓琳", "submit_time": "2025-05-11T14:00:00", "status": "pending", "priority": "high",
    },
    {
        "id": "md-010", "content_type": "comment", "title": "评论：工伤认定指南",
        "content_preview": "这个信息严重误导！我老公是工地受伤的，根本不需要这么多手续，去当地人社局直接办理就行，这篇文章写得乱七八糟。",
        "author_name": "工地家属", "submit_time": "2025-05-11T11:30:00", "status": "pending", "priority": "medium",
    },
    {
        "id": "md-011", "content_type": "post", "title": "民间借贷纠纷，借条过期了还能起诉吗？",
        "content_preview": "三年前借给朋友10万块，借条上写的一年还，到现在还没还。最近听说诉讼时效是三年，是不是已经过期了...",
        "author_name": "周先生", "submit_time": "2025-05-12T16:00:00", "status": "approved", "priority": "low",
    },
    {
        "id": "md-012", "content_type": "review", "title": "张律师服务评价",
        "content_preview": "张律师非常耐心，解答了我的所有疑问，还帮我起草了协议书，非常感谢！",
        "author_name": "赵女士", "submit_time": "2025-05-10T10:00:00", "status": "approved", "priority": "low",
    },
    {
        "id": "md-013", "content_type": "comment", "title": "评论：离婚财产分割指南",
        "content_preview": "文章写得不错，但还漏了一个重要问题——婚前财产增值部分怎么算？希望补充一下。",
        "author_name": "求知者", "submit_time": "2025-05-10T09:30:00", "status": "approved", "priority": "low",
    },
    {
        "id": "md-014", "content_type": "lawyer", "title": "律师认证申请 - 黄大伟",
        "content_preview": "黄大伟，执业证号：11101201xxxxxxxx，执业机构：中伦律师事务所，执业年限：15年，擅长领域：公司法、IPO、并购重组...",
        "author_name": "黄大伟", "submit_time": "2025-05-10T08:00:00", "status": "approved", "priority": "medium",
    },
    {
        "id": "md-015", "content_type": "post", "title": "邻居装修导致我家墙面开裂，怎么维权？",
        "content_preview": "楼上邻居大规模装修，导致我家天花板出现裂缝，找物业不管，找邻居不理，该找哪个部门？",
        "author_name": "吴女士", "submit_time": "2025-05-09T11:00:00", "status": "pending", "priority": "medium",
    },
    {
        "id": "md-016", "content_type": "comment", "title": "评论：继承法科普",
        "content_preview": "哈哈说的真好笑，你讲的这些法律找人就给你办了？我告诉你现实中根本行不通！（附联系电话138xxxx）",
        "author_name": "现实主义者", "submit_time": "2025-05-13T08:00:00", "status": "pending", "priority": "high",
    },
    {
        "id": "md-017", "content_type": "lawyer", "title": "律师认证申请 - 林芳",
        "content_preview": "林芳，执业证号：未提供，执业机构：自称\"自由执业律师\"，执业年限：宣传\"20年经验\"，但系统查无此人执业信息，疑似虚假认证。",
        "author_name": "林芳", "submit_time": "2025-05-13T09:30:00", "status": "pending", "priority": "high",
    },
    {
        "id": "md-018", "content_type": "post", "title": "网贷逾期被暴力催收怎么办？",
        "content_preview": "因为生意失败还不上网贷，催收公司天天打电话骚扰我家人和单位，还发威胁短信，我该怎么办？",
        "author_name": "匿名用户", "submit_time": "2025-05-09T14:30:00", "status": "rejected", "priority": "medium",
        "reject_reason": "内容涉及敏感金融话题且含诱导性表述，已建议用户联系银保监会投诉渠道",
    },
    {
        "id": "md-019", "content_type": "review", "title": "AI合同审查评价",
        "content_preview": "用了AI合同审查功能，识别出了买卖合同中的三个风险点，很实用！",
        "author_name": "小企业主", "submit_time": "2025-05-08T15:00:00", "status": "approved", "priority": "low",
    },
    {
        "id": "md-020", "content_type": "comment", "title": "评论：刑事辩护基础知识",
        "content_preview": "你这讲的根本不对，我之前在检察院工作过，程序根本不是你这样走的，误导公众！",
        "author_name": "前检察官", "submit_time": "2025-05-08T10:00:00", "status": "pending", "priority": "high",
    },
]


_mock_records: list[dict] = [
    {"id": "rc-001", "item_id": "md-011", "content_type": "post", "action": "approve", "reviewer_id": 1, "reviewer_name": "管理员张三", "remark": "内容合法合规", "review_time": "2025-05-12T17:00:00"},
    {"id": "rc-002", "item_id": "md-012", "content_type": "review", "action": "approve", "reviewer_id": 1, "reviewer_name": "管理员张三", "remark": "评价真实有效", "review_time": "2025-05-10T16:00:00"},
    {"id": "rc-003", "item_id": "md-013", "content_type": "comment", "action": "approve", "reviewer_id": 2, "reviewer_name": "管理员李四", "remark": "正常讨论", "review_time": "2025-05-10T15:30:00"},
    {"id": "rc-004", "item_id": "md-014", "content_type": "lawyer", "action": "approve", "reviewer_id": 1, "reviewer_name": "管理员张三", "remark": "执业证信息已核实", "review_time": "2025-05-10T14:00:00"},
    {"id": "rc-005", "item_id": "md-018", "content_type": "post", "action": "reject", "reviewer_id": 2, "reviewer_name": "管理员李四", "remark": "诱导性内容，建议引导至正规投诉渠道", "review_time": "2025-05-09T16:00:00"},
    {"id": "rc-006", "item_id": "md-019", "content_type": "review", "action": "approve", "reviewer_id": 1, "reviewer_name": "管理员张三", "remark": "正常使用反馈", "review_time": "2025-05-08T17:00:00"},
    {"id": "rc-007", "item_id": "md-015", "content_type": "post", "action": "approve", "reviewer_id": 3, "reviewer_name": "管理员王五", "remark": "内容合规", "review_time": "2025-05-10T11:00:00"},
    {"id": "rc-008", "item_id": "md-010", "content_type": "comment", "action": "reject", "reviewer_id": 2, "reviewer_name": "管理员李四", "remark": "存在误导性信息，不实表述", "review_time": "2025-05-11T14:00:00"},
    {"id": "rc-009", "item_id": "md-008", "content_type": "post", "action": "approve", "reviewer_id": 3, "reviewer_name": "管理员王五", "remark": "常见法律咨询，无违规内容", "review_time": "2025-05-11T16:30:00"},
]


_mock_rules: list[dict] = [
    {
        "id": "rule-001", "name": "敏感词过滤规则", "category": "keyword_filter",
        "description": "自动检测并拦截包含政治敏感词、色情词汇、暴力词汇的内容",
        "keywords": ["敏感政治人物姓名", "违法药品名称", "赌博相关词汇"],
        "enabled": True, "severity": "high", "updated_at": "2025-05-01T10:00:00",
    },
    {
        "id": "rule-002", "name": "联系方式检测", "category": "contact_filter",
        "description": "检测内容中的手机号、微信号、QQ号等联系方式，防止站外引流",
        "keywords": ["手机号正则", "微信号模式", "QQ号模式", "二维码图片"],
        "enabled": True, "severity": "high", "updated_at": "2025-05-01T10:00:00",
    },
    {
        "id": "rule-003", "name": "广告推广检测", "category": "ad_filter",
        "description": "识别内容中的广告推广信息，包括法律咨询推广、代理服务推广等",
        "keywords": ["免费咨询", "加我微信", "扫码联系", "限时优惠", "包打赢"],
        "enabled": True, "severity": "medium", "updated_at": "2025-04-28T14:00:00",
    },
    {
        "id": "rule-004", "name": "执业资质审核", "category": "lawyer_verify",
        "description": "审核律师认证申请，核实执业证号、执业机构、执业年限等信息真实性",
        "keywords": ["执业证号格式校验", "执业机构真实性", "执业年限合理性"],
        "enabled": True, "severity": "high", "updated_at": "2025-04-25T09:00:00",
    },
    {
        "id": "rule-005", "name": "虚假评价检测", "category": "review_filter",
        "description": "检测疑似刷单、恶意差评、虚假好评等异常评价行为",
        "keywords": ["短时间内大量评价", "相似内容重复评价", "新注册账号评价"],
        "enabled": True, "severity": "medium", "updated_at": "2025-04-20T16:00:00",
    },
    {
        "id": "rule-006", "name": "发布频率限制", "category": "rate_limit",
        "description": "限制用户单位时间内的发帖/评论/评价次数，防止刷屏和垃圾信息",
        "keywords": ["单用户每日发帖上限5篇", "单用户每小时评论上限10条", "单用户每日评价上限3条"],
        "enabled": True, "severity": "low", "updated_at": "2025-04-15T11:00:00",
    },
    {
        "id": "rule-007", "name": "法律风险内容识别", "category": "legal_risk",
        "description": "识别内容中可能涉及的法律风险，如教唆违法、虚假法律建议等",
        "keywords": ["教你如何逃避", "不用请律师", "私下解决就行", "不用报警"],
        "enabled": True, "severity": "high", "updated_at": "2025-04-10T08:30:00",
    },
    {
        "id": "rule-008", "name": "未成年人保护规则", "category": "minor_protection",
        "description": "涉及未成年人信息的特殊审核规则，保护未成年人隐私和权益",
        "keywords": ["未成年人姓名", "学校名称", "未成年人照片", "校园暴力描述"],
        "enabled": True, "severity": "high", "updated_at": "2025-04-05T13:00:00",
    },
]

_next_record_id = 10


def _paginate(data: list[dict], page: int, page_size: int) -> dict:
    total = len(data)
    start = (page - 1) * page_size
    items = data[start:start + page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ==================== 1. 审核队列 ====================
class ApproveBody(BaseModel):
    remark: Optional[str] = None


class RejectBody(BaseModel):
    reason: str
    remark: Optional[str] = None


class BatchReviewBody(BaseModel):
    item_ids: list[str]
    action: str
    reason: Optional[str] = None


class ReviewBody(BaseModel):
    action: str
    reason: Optional[str] = None
    note: Optional[str] = None


class BatchReviewFrontendBody(BaseModel):
    ids: list[str]
    action: str
    reason: Optional[str] = None
    note: Optional[str] = None


class KeywordCheckBody(BaseModel):
    content: str
    categories: Optional[list[str]] = None


@router.get("/queue")
async def get_moderation_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
):
    data = list(_mock_queue)
    if status:
        data = [i for i in data if i["status"] == status]
    if content_type:
        data = [i for i in data if i["content_type"] == content_type]
    if keyword:
        kw = keyword.lower()
        data = [i for i in data if kw in i["title"].lower() or kw in i["content_preview"].lower()]
    if risk_level:
        data = [i for i in data if i.get("priority") == risk_level]
    return _paginate(data, page, page_size)


# ==================== 2. 审核统计 ====================
@router.get("/stats")
async def get_moderation_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    pending_items = [i for i in _mock_queue if i["status"] == "pending"]
    return {
        "total_pending": len(pending_items),
        "pending_posts": sum(1 for i in pending_items if i["content_type"] == "post"),
        "pending_comments": sum(1 for i in pending_items if i["content_type"] == "comment"),
        "pending_reviews": sum(1 for i in pending_items if i["content_type"] == "review"),
        "pending_lawyers": sum(1 for i in pending_items if i["content_type"] == "lawyer"),
        "avg_review_time_minutes": 8.5,
        "approved_today": 3,
        "rejected_today": 1,
        "total_checks": len(_mock_records),
        "blocked_count": sum(1 for r in _mock_records if r["action"] == "reject"),
        "warning_count": 2,
        "passed_count": sum(1 for r in _mock_records if r["action"] == "approve"),
        "block_rate": round(sum(1 for r in _mock_records if r["action"] == "reject") / max(len(_mock_records), 1) * 100, 1),
        "categories": {"post": 5, "comment": 2, "review": 1, "lawyer": 1},
    }


# ==================== 3. 单条审核 - 通过 ====================
@router.post("/queue/{item_id}/approve")
async def approve_item(item_id: str, body: ApproveBody = ApproveBody()):
    global _next_record_id
    now = datetime.now().isoformat()
    for item in _mock_queue:
        if item["id"] == item_id:
            item["status"] = "approved"
            item["reviewed_at"] = now
            _mock_records.append({
                "id": f"rc-{_next_record_id:03d}", "item_id": item_id,
                "content_type": item["content_type"], "action": "approve",
                "reviewer_id": 1, "reviewer_name": "管理员张三",
                "remark": body.remark, "review_time": now,
            })
            _next_record_id += 1
            return item
    return {"detail": "审核项不存在"}


# ==================== 4. 单条审核 - 拒绝 ====================
@router.post("/queue/{item_id}/reject")
async def reject_item(item_id: str, body: RejectBody):
    global _next_record_id
    now = datetime.now().isoformat()
    for item in _mock_queue:
        if item["id"] == item_id:
            item["status"] = "rejected"
            item["reject_reason"] = body.reason
            item["reviewed_at"] = now
            _mock_records.append({
                "id": f"rc-{_next_record_id:03d}", "item_id": item_id,
                "content_type": item["content_type"], "action": "reject",
                "reviewer_id": 1, "reviewer_name": "管理员张三",
                "remark": body.reason + (f"（备注：{body.remark}）" if body.remark else ""),
                "review_time": now,
            })
            _next_record_id += 1
            return item
    return {"detail": "审核项不存在"}


# ==================== 5. 批量审核 ====================
@router.post("/queue/batch")
async def batch_review(body: BatchReviewBody):
    global _next_record_id
    now = datetime.now().isoformat()
    results = []
    for item_id in body.item_ids:
        for item in _mock_queue:
            if item["id"] == item_id and item["status"] == "pending":
                item["status"] = "approved" if body.action == "approve" else "rejected"
                if body.action == "reject" and body.reason:
                    item["reject_reason"] = body.reason
                item["reviewed_at"] = now
                _mock_records.append({
                    "id": f"rc-{_next_record_id:03d}", "item_id": item_id,
                    "content_type": item["content_type"], "action": body.action,
                    "reviewer_id": 1, "reviewer_name": "管理员张三",
                    "remark": body.reason if body.action == "reject" else None,
                    "review_time": now,
                })
                _next_record_id += 1
                results.append({"item_id": item_id, "success": True, "status": item["status"]})
                break
        else:
            results.append({"item_id": item_id, "success": False, "reason": "未找到或已处理"})
    return {"results": results, "batch_action": body.action, "processed_at": now}


# ==================== 6. 审核规则 ====================
@router.get("/rules")
async def get_moderation_rules():
    return {"rules": _mock_rules, "total": len(_mock_rules)}


# ==================== 前端兼容端点 ====================

# 审核记录（前端 apiGetModerationRecords）
@router.get("/records")
async def get_moderation_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    content_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    reviewer_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    data = list(_mock_records)
    if content_type:
        data = [r for r in data if r["content_type"] == content_type]
    if action:
        data = [r for r in data if r["action"] == action]
    if reviewer_id:
        data = [r for r in data if str(r["reviewer_id"]) == reviewer_id]
    if start_date:
        data = [r for r in data if r["review_time"] >= start_date]
    if end_date:
        data = [r for r in data if r["review_time"] <= end_date]
    return _paginate(data, page, page_size)


# 前端单条审核路径: POST /moderation/{id}/review
@router.post("/{item_id}/review")
async def submit_review(item_id: str, body: ReviewBody):
    global _next_record_id
    now = datetime.now().isoformat()
    for item in _mock_queue:
        if item["id"] == item_id:
            if body.action not in ("approve", "reject"):
                return {"detail": "无效的审核操作"}
            item["status"] = "approved" if body.action == "approve" else "rejected"
            if body.action == "reject":
                item["reject_reason"] = body.reason
            item["reviewed_at"] = now
            _mock_records.append({
                "id": f"rc-{_next_record_id:03d}", "item_id": item_id,
                "content_type": item["content_type"], "action": body.action,
                "reviewer_id": 1, "reviewer_name": "管理员张三",
                "remark": body.note or body.reason,
                "review_time": now,
            })
            _next_record_id += 1
            return item
    return {"detail": "审核项不存在"}


# 前端批量审核路径: POST /moderation/batch-review
@router.post("/batch-review")
async def batch_review_frontend(body: BatchReviewFrontendBody):
    global _next_record_id
    now = datetime.now().isoformat()
    results = []
    for item_id in body.ids:
        for item in _mock_queue:
            if item["id"] == item_id and item["status"] == "pending":
                item["status"] = "approved" if body.action == "approve" else "rejected"
                if body.action == "reject" and body.reason:
                    item["reject_reason"] = body.reason
                item["reviewed_at"] = now
                _mock_records.append({
                    "id": f"rc-{_next_record_id:03d}", "item_id": item_id,
                    "content_type": item["content_type"], "action": body.action,
                    "reviewer_id": 1, "reviewer_name": "管理员张三",
                    "remark": body.note or body.reason,
                    "review_time": now,
                })
                _next_record_id += 1
                results.append({"item_id": item_id, "success": True, "status": item["status"]})
                break
        else:
            results.append({"item_id": item_id, "success": False, "reason": "未找到或已处理"})
    return {"results": results, "batch_action": body.action, "processed_at": now}


# 内容详情
@router.get("/content/{content_type}/{content_id}")
async def get_content_detail(content_type: str, content_id: str):
    for item in _mock_queue:
        if item["id"] == content_id:
            return {
                "id": item["id"],
                "content_type": item["content_type"],
                "title": item["title"],
                "content_full": item["content_preview"] + "\n\n【完整内容】\n以上为该内容的预览摘要。审核通过后将公开展示完整内容。",
                "author_name": item["author_name"],
                "submit_time": item["submit_time"],
                "status": item["status"],
                "priority": item["priority"],
                "metadata": {"ip": "112.96.xxx.xxx", "device": "Android 14", "location": "北京市朝阳区"},
            }
    return {"detail": "内容不存在"}


# 关键词检查
@router.post("/keyword/check")
async def check_keywords(body: KeywordCheckBody):
    sensitive_map = {
        "政治": ["敏感词A", "敏感词B"],
        "色情": ["色情词1", "色情词2"],
        "广告": ["加微信", "扫码", "免费咨询"],
        "暴力": ["暴力词1"],
        "违法": ["违法词1", "违法词2"],
    }
    found: list[str] = []
    content_lower = body.content.lower()
    for cat, keywords in sensitive_map.items():
        for kw in keywords:
            if kw.lower() in content_lower:
                found.append(kw)

    categories_filtered = body.categories or list(sensitive_map.keys())
    relevant_categories = [c for c in categories_filtered if c in sensitive_map]

    if found:
        return {
            "flagged": True,
            "keywords_found": found,
            "risk_score": min(len(found) * 25, 100),
            "categories": relevant_categories,
            "severity": "high" if len(found) >= 3 else ("medium" if len(found) >= 2 else "low"),
        }
    return {
        "flagged": False,
        "keywords_found": [],
        "risk_score": 0,
        "categories": relevant_categories,
        "severity": "none",
    }