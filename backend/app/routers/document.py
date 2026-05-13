from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/documents", tags=["Documents"])
contract_router = APIRouter(prefix="/contracts", tags=["Contracts"])

# ==========================================
# Pydantic 请求模型
# ==========================================

class GenerateDocumentRequest(BaseModel):
    template_id: str
    fields: dict[str, str]

class ReviewContractRequest(BaseModel):
    contract_text: Optional[str] = None
    file_url: Optional[str] = None
    review_type: Optional[str] = None

# ==========================================
# 文档分类
# ==========================================

_DOCUMENT_CATEGORIES = [
    {"key": "complaint", "name": "起诉状", "description": "向法院提起诉讼的文书", "count": 15},
    {"key": "defense", "name": "答辩状", "description": "被告针对起诉进行的答辩", "count": 8},
    {"key": "appeal", "name": "上诉状", "description": "对一审判决不服提起上诉", "count": 6},
    {"key": "application", "name": "申请书", "description": "各类法律申请文书", "count": 12},
    {"key": "agreement", "name": "协议书", "description": "双方协商一致的协议", "count": 20},
    {"key": "contract", "name": "合同模板", "description": "各类合同标准模板", "count": 25},
    {"key": "lawyer_letter", "name": "律师函", "description": "律师出具的正式法律函件", "count": 5},
    {"key": "legal_opinion", "name": "法律意见书", "description": "律师出具的专业法律意见", "count": 4},
    {"key": "will", "name": "遗嘱", "description": "个人财产处置的遗嘱文书", "count": 3},
    {"key": "power_of_attorney", "name": "委托书", "description": "授权他人代为处理事务的文书", "count": 7},
]

# ==========================================
# 文档模板 Mock 数据（12+ 个）
# ==========================================

_DOCUMENT_TEMPLATES = [
    {
        "id": "1", "name": "民事起诉状（民间借贷纠纷）", "category": "起诉状",
        "description": "适用于个人之间借款纠纷的民事起诉状模板，包含借款事实、还款催收等要素",
        "download_count": 18560, "is_free": True, "price": 0,
        "preview_url": "/previews/civil-complaint-loan.png",
        "created_at": (datetime.now() - timedelta(days=180)).isoformat(),
        "fields": [
            {"name": "plaintiff_name", "type": "text", "label": "原告姓名", "required": True, "placeholder": "请输入原告姓名"},
            {"name": "plaintiff_idcard", "type": "text", "label": "原告身份证号", "required": True, "placeholder": "请输入原告身份证号"},
            {"name": "plaintiff_phone", "type": "text", "label": "原告联系电话", "required": True, "placeholder": "请输入联系电话"},
            {"name": "defendant_name", "type": "text", "label": "被告姓名", "required": True, "placeholder": "请输入被告姓名"},
            {"name": "defendant_idcard", "type": "text", "label": "被告身份证号", "required": False, "placeholder": "如知晓请填写"},
            {"name": "defendant_address", "type": "text", "label": "被告住址", "required": True, "placeholder": "请输入被告住址"},
            {"name": "loan_amount", "type": "number", "label": "借款金额（元）", "required": True, "placeholder": "请输入借款金额"},
            {"name": "loan_date", "type": "date", "label": "借款日期", "required": True, "placeholder": "选择借款日期"},
            {"name": "repay_date", "type": "date", "label": "约定还款日期", "required": False, "placeholder": "如约定了还款日期请选择"},
            {"name": "interest_rate", "type": "text", "label": "约定利息", "required": False, "placeholder": "如约定了利息请填写，如年利率24%"},
            {"name": "court", "type": "text", "label": "管辖法院", "required": True, "placeholder": "请输入有管辖权的法院名称"},
        ],
        "content_preview": "民事起诉状\n\n原告：{plaintiff_name}，身份证号：{plaintiff_idcard}，联系电话：{plaintiff_phone}。\n\n被告：{defendant_name}，身份证号：{defendant_idcard}，住址：{defendant_address}。\n\n诉讼请求：\n1. 请求判令被告返还原告借款本金{loan_amount}元及利息；\n2. 请求判令被告承担本案全部诉讼费用。\n\n事实与理由：...",
    },
    {
        "id": "2", "name": "民事答辩状（合同纠纷）", "category": "答辩状",
        "description": "针对合同纠纷的民事答辩状模板，可对原告诉请逐一答辩反驳",
        "download_count": 12340, "is_free": True, "price": 0,
        "preview_url": "/previews/civil-defense-contract.png",
        "created_at": (datetime.now() - timedelta(days=150)).isoformat(),
        "fields": [
            {"name": "defendant_name", "type": "text", "label": "答辩人姓名", "required": True, "placeholder": "请输入答辩人姓名"},
            {"name": "court", "type": "text", "label": "受理法院", "required": True, "placeholder": "请输入受理法院名称"},
            {"name": "case_number", "type": "text", "label": "案号", "required": True, "placeholder": "请输入案号"},
            {"name": "plaintiff_name", "type": "text", "label": "原告姓名", "required": True, "placeholder": "请输入原告姓名"},
            {"name": "defense_points", "type": "textarea", "label": "答辩要点", "required": True, "placeholder": "请逐条阐述答辩理由"},
            {"name": "evidence_list", "type": "textarea", "label": "证据清单", "required": False, "placeholder": "请列出提交的证据"},
        ],
        "content_preview": "民事答辩状\n\n答辩人：{defendant_name}\n\n就原告{plaintiff_name}诉答辩人合同纠纷一案（案号：{case_number}），答辩人提出如下答辩意见：\n\n{defense_points}\n\n此致\n{court}",
    },
    {
        "id": "3", "name": "民事上诉状", "category": "上诉状",
        "description": "对一审民事判决不服提起上诉的标准格式文书",
        "download_count": 8920, "is_free": True, "price": 0,
        "preview_url": "/previews/civil-appeal.png",
        "created_at": (datetime.now() - timedelta(days=120)).isoformat(),
        "fields": [
            {"name": "appellant_name", "type": "text", "label": "上诉人姓名", "required": True, "placeholder": "请输入上诉人姓名"},
            {"name": "original_court", "type": "text", "label": "原审法院", "required": True, "placeholder": "请输入原审法院名称"},
            {"name": "case_number", "type": "text", "label": "原审案号", "required": True, "placeholder": "请输入原审案号"},
            {"name": "appeal_court", "type": "text", "label": "上诉法院", "required": True, "placeholder": "请输入上诉法院名称"},
            {"name": "appeal_reasons", "type": "textarea", "label": "上诉理由", "required": True, "placeholder": "请详细阐述上诉理由"},
            {"name": "appeal_requests", "type": "textarea", "label": "上诉请求", "required": True, "placeholder": "请列出上诉请求"},
        ],
        "content_preview": "民事上诉状\n\n上诉人：{appellant_name}\n\n上诉人不服{original_court}（{case_number}）民事判决，现提起上诉。\n\n上诉请求：\n{appeal_requests}\n\n上诉理由：\n{appeal_reasons}\n\n此致\n{appeal_court}",
    },
    {
        "id": "4", "name": "离婚起诉状", "category": "起诉状",
        "description": "适用于离婚诉讼的标准起诉状模板，包含财产分割和子女抚养条款",
        "download_count": 25100, "is_free": False, "price": 9.90,
        "preview_url": "/previews/divorce-complaint.png",
        "created_at": (datetime.now() - timedelta(days=200)).isoformat(),
        "fields": [
            {"name": "plaintiff_name", "type": "text", "label": "原告姓名", "required": True, "placeholder": "请输入原告姓名"},
            {"name": "defendant_name", "type": "text", "label": "被告姓名", "required": True, "placeholder": "请输入被告姓名"},
            {"name": "marriage_date", "type": "date", "label": "结婚日期", "required": True, "placeholder": "选择结婚日期"},
            {"name": "children_info", "type": "textarea", "label": "子女信息", "required": False, "placeholder": "请输入子女姓名、出生日期等信息"},
            {"name": "property_info", "type": "textarea", "label": "共同财产", "required": False, "placeholder": "请列出夫妻共同财产"},
            {"name": "divorce_reason", "type": "textarea", "label": "离婚理由", "required": True, "placeholder": "请说明离婚的事实理由"},
            {"name": "custody_request", "type": "text", "label": "子女抚养权诉求", "required": False, "placeholder": "请写明对子女抚养权的主张"},
        ],
        "content_preview": "民事起诉状（离婚纠纷）\n\n原告：{plaintiff_name}\n被告：{defendant_name}\n\n诉讼请求：\n1. 请求判令原告与被告离婚；\n2. 请求判令依法分割夫妻共同财产；\n3. 请求判令子女抚养权归属及抚养费承担。\n\n事实与理由：...",
    },
    {
        "id": "5", "name": "财产保全申请书", "category": "申请书",
        "description": "在诉讼前或诉讼中申请查封冻结对方财产的标准申请书",
        "download_count": 6780, "is_free": True, "price": 0,
        "preview_url": "/previews/property-preservation.png",
        "created_at": (datetime.now() - timedelta(days=90)).isoformat(),
        "fields": [
            {"name": "applicant_name", "type": "text", "label": "申请人姓名", "required": True, "placeholder": "请输入申请人姓名"},
            {"name": "respondent_name", "type": "text", "label": "被申请人姓名", "required": True, "placeholder": "请输入被申请人姓名"},
            {"name": "court", "type": "text", "label": "管辖法院", "required": True, "placeholder": "请输入法院名称"},
            {"name": "preservation_amount", "type": "number", "label": "保全金额（元）", "required": True, "placeholder": "请输入申请保全的金额"},
            {"name": "preservation_target", "type": "textarea", "label": "保全标的物", "required": True, "placeholder": "请描述需要保全的财产，如银行账户、房产、车辆等"},
            {"name": "reason", "type": "textarea", "label": "申请理由", "required": True, "placeholder": "请说明申请财产保全的理由"},
        ],
        "content_preview": "财产保全申请书\n\n申请人：{applicant_name}\n被申请人：{respondent_name}\n\n申请事项：\n请求法院依法查封、冻结被申请人价值{preservation_amount}元的财产。\n\n事实与理由：\n{reason}",
    },
    {
        "id": "6", "name": "房屋租赁合同", "category": "合同模板",
        "description": "标准房屋租赁合同模板，适用于住宅租赁场景",
        "download_count": 32000, "is_free": False, "price": 19.90,
        "preview_url": "/previews/house-rental-contract.png",
        "created_at": (datetime.now() - timedelta(days=250)).isoformat(),
        "fields": [
            {"name": "lessor_name", "type": "text", "label": "出租方姓名", "required": True, "placeholder": "请输入出租方姓名"},
            {"name": "lessee_name", "type": "text", "label": "承租方姓名", "required": True, "placeholder": "请输入承租方姓名"},
            {"name": "property_address", "type": "text", "label": "房屋地址", "required": True, "placeholder": "请输入房屋详细地址"},
            {"name": "area", "type": "number", "label": "房屋面积（平方米）", "required": True, "placeholder": "请输入房屋面积"},
            {"name": "monthly_rent", "type": "number", "label": "月租金（元）", "required": True, "placeholder": "请输入月租金"},
            {"name": "deposit", "type": "number", "label": "押金（元）", "required": True, "placeholder": "请输入押金金额"},
            {"name": "start_date", "type": "date", "label": "租赁起租日", "required": True, "placeholder": "选择起租日期"},
            {"name": "end_date", "type": "date", "label": "租赁截止日", "required": True, "placeholder": "选择截止日期"},
            {"name": "payment_method", "type": "select", "label": "付款方式", "required": True, "options": ["月付", "季付", "半年付", "年付"]},
        ],
        "content_preview": "房屋租赁合同\n\n出租方（甲方）：{lessor_name}\n承租方（乙方）：{lessee_name}\n\n第一条 房屋基本情况\n房屋坐落于{property_address}，建筑面积{area}平方米。\n\n第二条 租赁期限\n租赁期限自{start_date}至{end_date}止。\n\n第三条 租金及押金\n月租金为{monthly_rent}元，押金为{deposit}元。付款方式为{payment_method}。",
    },
    {
        "id": "7", "name": "律师函（催款专用）", "category": "律师函",
        "description": "律师代为发送的正式催款函，具备法律效力",
        "download_count": 14500, "is_free": False, "price": 29.90,
        "preview_url": "/previews/lawyer-letter-payment.png",
        "created_at": (datetime.now() - timedelta(days=100)).isoformat(),
        "fields": [
            {"name": "sender_name", "type": "text", "label": "发函方", "required": True, "placeholder": "请输入发函方姓名/名称"},
            {"name": "recipient_name", "type": "text", "label": "收函方", "required": True, "placeholder": "请输入收函方姓名/名称"},
            {"name": "debt_amount", "type": "number", "label": "欠款金额（元）", "required": True, "placeholder": "请输入欠款金额"},
            {"name": "debt_reason", "type": "textarea", "label": "欠款事由", "required": True, "placeholder": "请说明欠款的事由和经过"},
            {"name": "deadline", "type": "date", "label": "还款期限", "required": True, "placeholder": "选择最后还款期限"},
            {"name": "lawyer_name", "type": "text", "label": "律师姓名", "required": True, "placeholder": "请输入律师姓名"},
            {"name": "law_firm", "type": "text", "label": "律师事务所", "required": True, "placeholder": "请输入律师事务所名称"},
        ],
        "content_preview": "律 师 函\n\n致：{recipient_name}\n\n本律师受{sender_name}委托，就贵方拖欠款项一事致函如下：\n\n据委托人反映，贵方因{debt_reason}，至今尚欠委托人款项人民币{debt_amount}元。\n\n请贵方于{deadline}前将上述款项支付至委托人指定账户，逾期本律师将代理委托人采取法律措施。\n\n{law_firm}\n律师：{lawyer_name}",
    },
    {
        "id": "8", "name": "合作协议书（通用版）", "category": "协议书",
        "description": "适用于各类商业合作的通用合作协议模板",
        "download_count": 9800, "is_free": False, "price": 15.90,
        "preview_url": "/previews/cooperation-agreement.png",
        "created_at": (datetime.now() - timedelta(days=80)).isoformat(),
        "fields": [
            {"name": "party_a", "type": "text", "label": "甲方名称", "required": True, "placeholder": "请输入甲方名称"},
            {"name": "party_b", "type": "text", "label": "乙方名称", "required": True, "placeholder": "请输入乙方名称"},
            {"name": "cooperation_content", "type": "textarea", "label": "合作内容", "required": True, "placeholder": "请描述合作的具体内容"},
            {"name": "profit_share", "type": "text", "label": "利润分配方式", "required": True, "placeholder": "请约定利润分配比例或方式"},
            {"name": "start_date", "type": "date", "label": "合作起始日", "required": True, "placeholder": "选择合作起始日"},
            {"name": "duration", "type": "text", "label": "合作期限", "required": True, "placeholder": "如：三年"},
        ],
        "content_preview": "合作协议书\n\n甲方：{party_a}\n乙方：{party_b}\n\n甲乙双方本着平等互利的原则，经友好协商，就{cooperation_content}事宜达成如下协议：\n\n一、合作内容\n...\n\n二、利润分配\n{profit_share}\n\n三、合作期限\n自{start_date}起，为期{duration}。",
    },
    {
        "id": "9", "name": "强制执行申请书", "category": "申请书",
        "description": "向法院申请强制执行的标准化文书",
        "download_count": 5600, "is_free": True, "price": 0,
        "preview_url": "/previews/enforcement-application.png",
        "created_at": (datetime.now() - timedelta(days=70)).isoformat(),
        "fields": [
            {"name": "applicant_name", "type": "text", "label": "申请人姓名", "required": True, "placeholder": "请输入申请人姓名"},
            {"name": "respondent_name", "type": "text", "label": "被执行人姓名", "required": True, "placeholder": "请输入被执行人姓名"},
            {"name": "court", "type": "text", "label": "执行法院", "required": True, "placeholder": "请输入执行法院名称"},
            {"name": "judgment_number", "type": "text", "label": "生效判决案号", "required": True, "placeholder": "请输入生效判决案号"},
            {"name": "execution_amount", "type": "number", "label": "执行标的额（元）", "required": True, "placeholder": "请输入执行标的额"},
            {"name": "execution_items", "type": "textarea", "label": "执行事项", "required": True, "placeholder": "请列明需要执行的具体事项"},
        ],
        "content_preview": "强制执行申请书\n\n申请人：{applicant_name}\n被执行人：{respondent_name}\n\n申请事项：\n请求法院依法强制执行（{judgment_number}）生效判决，执行标的额为{execution_amount}元。\n\n执行事项如下：\n{execution_items}",
    },
    {
        "id": "10", "name": "法律意见书（劳动争议）", "category": "法律意见书",
        "description": "针对劳动争议出具的专业法律意见书",
        "download_count": 3200, "is_free": False, "price": 49.90,
        "preview_url": "/previews/legal-opinion-labor.png",
        "created_at": (datetime.now() - timedelta(days=60)).isoformat(),
        "fields": [
            {"name": "client_name", "type": "text", "label": "委托人姓名", "required": True, "placeholder": "请输入委托人姓名"},
            {"name": "employer_name", "type": "text", "label": "用人单位", "required": True, "placeholder": "请输入用人单位名称"},
            {"name": "dispute_type", "type": "select", "label": "争议类型", "required": True, "options": ["解除劳动合同", "拖欠工资", "工伤赔偿", "社保纠纷", "加班费争议"]},
            {"name": "case_summary", "type": "textarea", "label": "案件基本情况", "required": True, "placeholder": "请描述案件事实经过"},
            {"name": "legal_analysis", "type": "textarea", "label": "法律分析要点", "required": False, "placeholder": "如需补充分析要点请填写"},
        ],
        "content_preview": "法律意见书\n\n致：{client_name}\n\n就贵方与{employer_name}之间的{dispute_type}事宜，本所出具如下法律意见：\n\n一、案件基本情况\n{case_summary}\n\n二、法律分析\n依据《中华人民共和国劳动合同法》相关规定...",
    },
    {
        "id": "11", "name": "自书遗嘱模板", "category": "遗嘱",
        "description": "法定格式的自书遗嘱模板，需亲笔书写签名",
        "download_count": 4500, "is_free": True, "price": 0,
        "preview_url": "/previews/will-template.png",
        "created_at": (datetime.now() - timedelta(days=50)).isoformat(),
        "fields": [
            {"name": "testator_name", "type": "text", "label": "立遗嘱人姓名", "required": True, "placeholder": "请输入立遗嘱人姓名"},
            {"name": "testator_idcard", "type": "text", "label": "身份证号", "required": True, "placeholder": "请输入身份证号"},
            {"name": "property_list", "type": "textarea", "label": "财产清单", "required": True, "placeholder": "请列明各项财产及其分配方案"},
            {"name": "heir_info", "type": "textarea", "label": "继承人信息", "required": True, "placeholder": "请填写各继承人的姓名、关系及继承份额"},
            {"name": "executor_name", "type": "text", "label": "遗嘱执行人", "required": False, "placeholder": "如有指定执行人请填写"},
        ],
        "content_preview": "遗 嘱\n\n立遗嘱人：{testator_name}，身份证号：{testator_idcard}。\n\n本人特立此遗嘱，对本人财产作如下处理：\n\n{property_list}\n\n继承人：\n{heir_info}",
    },
    {
        "id": "12", "name": "授权委托书（诉讼代理）", "category": "委托书",
        "description": "授权律师代理诉讼的标准委托书",
        "download_count": 11000, "is_free": True, "price": 0,
        "preview_url": "/previews/power-of-attorney.png",
        "created_at": (datetime.now() - timedelta(days=40)).isoformat(),
        "fields": [
            {"name": "principal_name", "type": "text", "label": "委托人姓名", "required": True, "placeholder": "请输入委托人姓名"},
            {"name": "principal_idcard", "type": "text", "label": "委托人身份证号", "required": True, "placeholder": "请输入身份证号"},
            {"name": "lawyer_name", "type": "text", "label": "受托律师姓名", "required": True, "placeholder": "请输入律师姓名"},
            {"name": "law_firm", "type": "text", "label": "律师事务所", "required": True, "placeholder": "请输入事务所名称"},
            {"name": "case_name", "type": "text", "label": "案件名称", "required": True, "placeholder": "请输入案件名称"},
            {"name": "court", "type": "text", "label": "受理法院", "required": True, "placeholder": "请输入受理法院"},
            {"name": "scope", "type": "select", "label": "授权范围", "required": True, "options": ["一般代理", "特别授权"]},
        ],
        "content_preview": "授权委托书\n\n委托人：{principal_name}，身份证号：{principal_idcard}。\n\n兹委托{law_firm}的{lawyer_name}律师，在{principal_name}与{case_name}一案中，作为委托人的诉讼代理人。\n\n委托权限：{scope}。\n\n此致\n{court}",
    },
    {
        "id": "13", "name": "交通事故赔偿起诉状", "category": "起诉状",
        "description": "交通事故人身损害赔偿纠纷的专用起诉状",
        "download_count": 7600, "is_free": False, "price": 12.90,
        "preview_url": "/previews/traffic-accident-complaint.png",
        "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
        "fields": [
            {"name": "plaintiff_name", "type": "text", "label": "受害人姓名", "required": True, "placeholder": "请输入受害人姓名"},
            {"name": "defendant_name", "type": "text", "label": "肇事方姓名", "required": True, "placeholder": "请输入肇事方姓名"},
            {"name": "accident_date", "type": "date", "label": "事故日期", "required": True, "placeholder": "选择事故日期"},
            {"name": "accident_location", "type": "text", "label": "事故地点", "required": True, "placeholder": "请输入事故地点"},
            {"name": "medical_expense", "type": "number", "label": "医疗费（元）", "required": True, "placeholder": "请输入已发生的医疗费用"},
            {"name": "other_loss", "type": "number", "label": "其他损失（元）", "required": False, "placeholder": "误工费、护理费、交通费等合计"},
            {"name": "compensation_total", "type": "number", "label": "赔偿总额（元）", "required": True, "placeholder": "请输入各项赔偿合计总额"},
        ],
        "content_preview": "民事起诉状（交通事故）\n\n原告：{plaintiff_name}\n被告：{defendant_name}\n\n诉讼请求：\n1. 请求判令被告赔偿原告医疗费等各项损失共计{compensation_total}元；\n2. 请求判令被告承担本案诉讼费用。\n\n事实与理由：\n{accident_date}，在{accident_location}发生交通事故...",
    },
    {
        "id": "14", "name": "保密协议（NDA）", "category": "合同模板",
        "description": "双方或多方之间的保密协议模板，保护商业秘密",
        "download_count": 8700, "is_free": False, "price": 25.90,
        "preview_url": "/previews/nda-agreement.png",
        "created_at": (datetime.now() - timedelta(days=20)).isoformat(),
        "fields": [
            {"name": "disclosing_party", "type": "text", "label": "信息披露方", "required": True, "placeholder": "请输入披露方名称"},
            {"name": "receiving_party", "type": "text", "label": "信息接收方", "required": True, "placeholder": "请输入接收方名称"},
            {"name": "confidential_scope", "type": "textarea", "label": "保密信息范围", "required": True, "placeholder": "请界定保密信息的具体范围"},
            {"name": "duration", "type": "text", "label": "保密期限", "required": True, "placeholder": "如：自签署之日起五年"},
            {"name": "penalty", "type": "number", "label": "违约金（元）", "required": True, "placeholder": "请输入违约赔偿金额"},
        ],
        "content_preview": "保密协议\n\n甲方（信息披露方）：{disclosing_party}\n乙方（信息接收方）：{receiving_party}\n\n第一条 保密信息范围\n{confidential_scope}\n\n第二条 保密期限\n{duration}\n\n第三条 违约责任\n如乙方违反本协议，应向甲方支付违约金{penalty}元。",
    },
]

# ==========================================
# 合同审查 Mock 数据（8+ 个）
# ==========================================

_CONTRACT_TEMPLATES = [
    {"id": "ct1", "name": "劳动合同（标准版）", "category": "劳动合同", "description": "符合劳动法规定的标准劳动合同模板", "download_count": 28500, "is_free": True},
    {"id": "ct2", "name": "商铺租赁合同", "category": "租赁合同", "description": "适用于商铺、写字楼等商业用途的租赁合同", "download_count": 15200, "is_free": False, "price": 19.90},
    {"id": "ct3", "name": "二手车买卖合同", "category": "买卖合同", "description": "个人之间二手车买卖的标准合同", "download_count": 9800, "is_free": True},
    {"id": "ct4", "name": "借款合同（抵押担保）", "category": "借款合同", "description": "附有房产抵押担保的借款合同模板", "download_count": 6200, "is_free": False, "price": 29.90},
    {"id": "ct5", "name": "股东合作协议", "category": "合作协议", "description": "公司设立时股东之间的合作协议", "download_count": 11200, "is_free": False, "price": 39.90},
    {"id": "ct6", "name": "员工保密协议", "category": "保密协议", "description": "企业与员工签订的保密与竞业限制协议", "download_count": 13400, "is_free": True},
]

_CONTRACT_REVIEWS = [
    {
        "id": "r1", "filename": "张三劳动合同.pdf", "contract_type": "劳动合同",
        "status": "completed", "risk_level": "low", "risk_count": 2,
        "text_chars": 4820, "text_preview": "甲方（用人单位）：北京某某科技有限公司\n乙方（劳动者）：张三\n第一条 劳动合同期限\n本合同期限为三年，自2026年1月1日至2028年12月31日...",
        "request_id": "req-001", "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
        "report": {
            "summary": "该劳动合同整体合规性较好，存在2项低风险条款。合同期限、薪酬、社保等核心条款较为完善，但试用期约定和加班条款存在可优化空间。",
            "overall_risk": "low",
            "risks": [
                {"level": "low", "clause": "第三条 试用期", "content": "试用期为6个月", "issue": "三年期限劳动合同的试用期不得超过6个月，当前约定处于上限，建议降低至3个月以降低用工风险。", "suggestion": "修改试用期为3个月", "reference": "《劳动合同法》第十九条"},
                {"level": "low", "clause": "第八条 加班", "content": "加班费按基本工资计算", "issue": "加班费计算基数约定不清，"基本工资"定义模糊，可能在实际计算时产生争议。", "suggestion": "明确加班费计算基数包含基本工资和岗位津贴", "reference": "《劳动法》第四十四条"},
            ],
            "missing_clauses": ["竞业限制条款建议补充", "保密义务条款建议补充"],
            "score": 85,
        },
    },
    {
        "id": "r2", "filename": "办公室租赁合同.docx", "contract_type": "租赁合同",
        "status": "completed", "risk_level": "medium", "risk_count": 5,
        "text_chars": 7650, "text_preview": "出租方（甲方）：李四\n承租方（乙方）：某某咨询有限公司\n第一条 租赁物\n甲方将位于北京市朝阳区某某大厦1201室出租给乙方使用...",
        "request_id": "req-002", "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
        "report": {
            "summary": "该租赁合同存在5项中等风险条款，主要集中在押金退还条件、维修责任划分、提前解约违约金等方面。建议在签署前与出租方协商修改。",
            "overall_risk": "medium",
            "risks": [
                {"level": "high", "clause": "第五条 押金", "content": "押金在合同期满后60日内退还", "issue": "押金退还期限长达60日，超出合理范围，存在出租方拖延退还的隐患。", "suggestion": "修改为合同期满后15日内退还押金", "reference": "《民法典》第七百零三条"},
                {"level": "medium", "clause": "第七条 维修责任", "content": "所有维修费用由承租方承担", "issue": "该条款将房屋主体结构等的维修责任转嫁给承租方，显失公平。", "suggestion": "区分大修（出租方承担）和日常维护（承租方承担）", "reference": "《民法典》第七百一十二条"},
                {"level": "medium", "clause": "第十条 违约责任", "content": "提前解约须支付6个月租金作为违约金", "issue": "违约金标准过高，可能被法院认定为过高而予以调减。", "suggestion": "建议降低为2-3个月租金", "reference": "《民法典》第五百八十五条"},
                {"level": "medium", "clause": "第三条 租金调整", "content": "每年租金递增10%", "issue": "租金年增幅10%显著高于市场平均水平，长期来看承租方负担过重。", "suggestion": "建议降低为每年递增3%-5%或与CPI挂钩", "reference": "市场惯例"},
                {"level": "low", "clause": "第十二条 争议解决", "content": "争议由甲方所在地法院管辖", "issue": "单方约定管辖法院对承租方有失公平。", "suggestion": "改为租赁物所在地或被告所在地法院管辖", "reference": "《民事诉讼法》第三十三条"},
            ],
            "missing_clauses": ["装修折旧处理条款", "不可抗力条款", "消防责任条款"],
            "score": 62,
        },
    },
    {
        "id": "r3", "filename": "设备采购合同.pdf", "contract_type": "买卖合同",
        "status": "completed", "risk_level": "high", "risk_count": 8,
        "text_chars": 10200, "text_preview": "买方：某某制造有限公司\n卖方：某某设备销售有限公司\n第一条 合同标的\n买方向卖方购买工业自动化生产线设备一套...",
        "request_id": "req-003", "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
        "report": {
            "summary": "该设备采购合同存在多项高风险条款，特别是在验收标准、质量保证、违约责任等方面对买方极为不利。强烈建议在签署前进行全面修改。",
            "overall_risk": "high",
            "risks": [
                {"level": "high", "clause": "第五条 验收", "content": "设备到场即视为验收合格", "issue": "该条款严重不合理，设备到场不等同于验收合格，剥夺了买方对设备质量的检查权利。", "suggestion": "增加安装调试后验收、试运行验收等阶段性验收条款", "reference": "《民法典》第六百二十一条"},
                {"level": "high", "clause": "第八条 质保", "content": "质保期为设备到场后3个月", "issue": "质保期过短，且从到场日（而非验收合格日）起算，设备安装调试期间即消耗质保期。", "suggestion": "质保期延长至12个月，自验收合格之日起算", "reference": "《民法典》第六百一十七条"},
                {"level": "high", "clause": "第十条 付款", "content": "合同签订后3日内支付90%货款", "issue": "付款比例严重不均衡，买方在未收到设备时即需支付绝大部分款项，风险极高。", "suggestion": "改为分阶段付款：签约30%、发货30%、验收30%、质保期满10%", "reference": "行业惯例"},
                {"level": "high", "clause": "第十二条 免责", "content": "卖方对设备造成的生产损失不承担任何责任", "issue": "完全排除间接损失的免责条款可能因显失公平而被认定无效，但会给买方维权增加难度。", "suggestion": "明确卖方在设备存在质量问题时对直接损失和合理间接损失的赔偿义务", "reference": "《民法典》第四百九十七条"},
                {"level": "medium", "clause": "第十五条 技术服务", "content": "安装调试费用另计", "issue": "设备采购通常包含安装调试服务，另行计费增加买方成本。", "suggestion": "将安装调试费用包含在合同总价中", "reference": "行业惯例"},
                {"level": "medium", "clause": "第三条 交货期限", "content": "交货期限为180个工作日", "issue": "以工作日计算交货期较为模糊，实际天数长达约9个月。", "suggestion": "明确具体交货日期或缩短至90个自然日内", "reference": "《民法典》第六百零一条"},
                {"level": "low", "clause": "第十八条 知识产权", "content": "设备所含软件的知识产权归属约定不明", "issue": "未明确设备配套软件的使用许可范围和期限。", "suggestion": "补充软件使用许可条款，明确使用范围和期限", "reference": "《著作权法》"},
                {"level": "low", "clause": "第二十条 不可抗力", "content": "未约定不可抗力条款", "issue": "缺少不可抗力条款，极端情况下双方权责不清。", "suggestion": "补充不可抗力条款", "reference": "《民法典》第一百八十条"},
            ],
            "missing_clauses": ["培训条款", "备品备件条款", "技术升级条款", "保密条款"],
            "score": 35,
        },
    },
    {
        "id": "r4", "filename": "个人借款合同.doc", "contract_type": "借款合同",
        "status": "completed", "risk_level": "low", "risk_count": 1,
        "text_chars": 2350, "text_preview": "出借方：王五\n借款方：赵六\n第一条 借款金额及用途\n出借方同意向借款方提供借款人民币伍拾万元整...",
        "request_id": "req-004", "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
        "report": {
            "summary": "该借款合同较为规范，仅有一项低风险提示。建议补充抵押登记条款以确保优先受偿权。",
            "overall_risk": "low",
            "risks": [
                {"level": "low", "clause": "第四条 担保", "content": "以赵六名下房产作为抵押担保", "issue": "仅约定抵押担保但未明确办理抵押登记的义务方和时限，未办理登记的抵押权不得对抗善意第三人。", "suggestion": "在合同中明确约定抵押登记办理时间和费用承担", "reference": "《民法典》第四百零二条"},
            ],
            "missing_clauses": ["提前还款条款", "加速到期条款"],
            "score": 88,
        },
    },
    {
        "id": "r5", "filename": "战略合作协议.pdf", "contract_type": "合作协议",
        "status": "in_progress", "risk_level": "medium", "risk_count": 4,
        "text_chars": 12800, "text_preview": "甲方：某某互联网科技有限公司\n乙方：某某金融信息服务有限公司\n鉴于双方在各自领域的资源优势...",
        "request_id": "req-005", "created_at": (datetime.now() - timedelta(hours=6)).isoformat(),
        "report": {
            "summary": "该战略合作协议框架性较强，但缺乏明确的执行机制和退出条款。整体风险中等，建议补充具体条款后再签署。",
            "overall_risk": "medium",
            "risks": [
                {"level": "medium", "clause": "第四条 知识产权", "content": "合作期间产生的知识产权归双方共有", "issue": "共有知识产权的使用、许可和收益分配机制未明确，容易产生纠纷。", "suggestion": "细化共有知识产权的管理规则，明确各自使用权限和收益分配比例", "reference": "《民法典》"},
                {"level": "medium", "clause": "第七条 排他性", "content": "双方在合作期间不得与第三方进行同类合作", "issue": "排他性条款范围过于宽泛，可能不必要地限制双方的其他商业机会。", "suggestion": "限定排他性条款的具体业务领域和地域范围", "reference": "《反垄断法》"},
                {"level": "medium", "clause": "第十条 终止", "content": "任何一方可以提前30天通知终止协议", "issue": "终止权过于宽松，一方投入大量资源后另一方可能随意退出。", "suggestion": "增加终止的限制条件，如重大违约情况下方可单方终止", "reference": "《民法典》"},
                {"level": "low", "clause": "第十二条 保密", "content": "保密期限为合同终止后1年", "issue": "保密期过短，核心商业秘密的保护期限建议延长。", "suggestion": "建议核心商业秘密保密期限延长至合同终止后3-5年", "reference": "《反不正当竞争法》"},
            ],
            "missing_clauses": ["争议解决条款", "法律适用条款", "通知送达条款"],
            "score": 58,
        },
    },
    {
        "id": "r6", "filename": "员工竞业限制协议.docx", "contract_type": "保密协议",
        "status": "completed", "risk_level": "high", "risk_count": 6,
        "text_chars": 4100, "text_preview": "甲方：某某生物科技有限公司\n乙方：刘七（研发总监）\n第一条 竞业限制范围\n乙方离职后不得从事与甲方有竞争关系的业务...",
        "request_id": "req-006", "created_at": (datetime.now() - timedelta(days=12)).isoformat(),
        "report": {
            "summary": "该竞业限制协议存在严重合规问题。竞业范围过于宽泛、补偿金标准过低、限制期限过长等问题可能导致协议被认定无效。",
            "overall_risk": "high",
            "risks": [
                {"level": "high", "clause": "第一条 竞业范围", "content": "不得从事任何与生物科技相关的行业", "issue": "竞业限制范围覆盖整个生物科技行业，过于宽泛，超出合理范围，可能被认定无效。", "suggestion": "限定为与甲方主营业务有直接竞争关系的细分领域", "reference": "《劳动合同法》第二十四条"},
                {"level": "high", "clause": "第三条 补偿", "content": "竞业限制补偿金为每月1000元", "issue": "补偿金标准过低，以研发总监薪资水平来看，1000元/月的补偿明显不合理。", "suggestion": "补偿金不低于劳动合同解除前十二个月平均工资的30%", "reference": "《最高人民法院关于审理劳动争议案件适用法律问题的解释（一）》第三十六条"},
                {"level": "high", "clause": "第五条 期限", "content": "竞业限制期限为三年", "issue": "竞业限制期限法定上限为二年，三年约定违反了法律规定。", "suggestion": "修改为不超过二年", "reference": "《劳动合同法》第二十四条"},
                {"level": "medium", "clause": "第六条 违约责任", "content": "违约金为100万元", "issue": "虽然约定了高额违约金，但由于竞业条款本身存在严重合规问题，违约金条款可能无法执行。", "suggestion": "先修正竞业范围和期限的合规性问题后，再设定合理违约金", "reference": "《劳动合同法》"},
                {"level": "medium", "clause": "第七条 补偿支付", "content": "补偿金按季度支付", "issue": "按季支付存在违约风险，如企业在第三个月不支付，员工维权存在空窗期。", "suggestion": "改为按月支付", "reference": "《最高人民法院关于审理劳动争议案件适用法律问题的解释（一）》"},
                {"level": "low", "clause": "第九条 协议生效", "content": "协议自签署之日起生效", "issue": "竞业限制协议一般在劳动合同解除或终止后生效，签署日生效与法理不符。", "suggestion": "明确竞业限制义务自劳动合同解除或终止之日起生效", "reference": "《劳动合同法》"},
            ],
            "missing_clauses": ["补偿金调整机制", "竞业限制解除条件"],
            "score": 28,
        },
    },
    {
        "id": "r7", "filename": "二手房买卖合同.pdf", "contract_type": "买卖合同",
        "status": "completed", "risk_level": "low", "risk_count": 1,
        "text_chars": 5600, "text_preview": "出卖方：陈八\n买受方：周九\n第一条 房屋基本情况\n出卖方将其所有的位于上海市浦东新区某某路100号房产出售给买受方...",
        "request_id": "req-007", "created_at": (datetime.now() - timedelta(days=14)).isoformat(),
        "report": {
            "summary": "该二手房买卖合同整体较为规范，条款完备。仅有1项低风险提示，建议确认房屋权属状况后再签署。",
            "overall_risk": "low",
            "risks": [
                {"level": "low", "clause": "第三条 产权状况", "content": "出卖方保证房屋产权清晰无争议", "issue": "出卖方单方保证条款缺乏核实机制，建议增加产权调查义务。", "suggestion": "建议在合同中约定签约前双方共同到不动产登记中心查询产权状况", "reference": "《民法典》"},
            ],
            "missing_clauses": [],
            "score": 92,
        },
    },
    {
        "id": "r8", "filename": "劳务派遣合同.docx", "contract_type": "劳动合同",
        "status": "pending", "risk_level": "medium", "risk_count": 0,
        "text_chars": 3400, "text_preview": "甲方（派遣单位）：某某人力资源服务有限公司\n乙方（用工单位）：某某物流有限公司\n第一条 派遣岗位和人数...",
        "request_id": "req-008", "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
        "report": {
            "summary": "劳务派遣合同正在审查中，初步扫描发现存在同工同酬和派遣比例方面的潜在风险，审查完成后将提供详细报告。",
            "overall_risk": "medium",
            "risks": [],
            "missing_clauses": [],
            "score": None,
        },
    },
    {
        "id": "r9", "filename": "股权转让协议.pdf", "contract_type": "合作协议",
        "status": "completed", "risk_level": "high", "risk_count": 7,
        "text_chars": 9200, "text_preview": "转让方：某某投资管理合伙企业\n受让方：某某实业有限公司\n第一条 转让标的\n转让方将其持有的某某科技有限公司30%股权转让给受让方...",
        "request_id": "req-009", "created_at": (datetime.now() - timedelta(days=20)).isoformat(),
        "report": {
            "summary": "该股权转让协议存在多项重大风险，特别是转让价款支付方式、陈述与保证条款过于单薄、未涉及公司债务与担保等问题，建议在签署前进行全面的尽职调查。",
            "overall_risk": "high",
            "risks": [
                {"level": "high", "clause": "第三条 价款支付", "content": "协议签署后5日内一次性支付全部转让价款", "issue": "一次性先行支付全部价款，受让方承担了全部风险，转让方完成工商变更的积极性将大幅降低。", "suggestion": "改为分期支付：签约后支付30%，工商变更完成支付60%，资料交接完毕支付10%", "reference": "《民法典》"},
                {"level": "high", "clause": "第五条 陈述与保证", "content": "转让方保证股权不存在任何瑕疵", "issue": "陈述与保证条款过于简单，未涉及公司债务、诉讼、税务、知识产权等关键事项。", "suggestion": "详细列举转让方的各项陈述与保证内容，包括但不限于公司财务状况、债务、法律诉讼、知识产权等", "reference": "《公司法》"},
                {"level": "high", "clause": "第八条 违约责任", "content": "任何一方违约只需退还已收款或已付款项", "issue": "违约责任与交易风险完全不成比例，无法对违约方形成有效约束。", "suggestion": "设定合理违约金，如转让价款的20%-30%", "reference": "《民法典》第五百八十五条"},
                {"level": "medium", "clause": "第二条 交割条件", "content": "未约定交割先决条件", "issue": "未设定任何交割先决条件，如其他股东放弃优先购买权、政府审批等。", "suggestion": "增加交割先决条件条款", "reference": "《公司法》第七十一条"},
                {"level": "medium", "clause": "第六条 税务", "content": "税费各自承担", "issue": "简单约定各自承担可能导致税务负担不明确。", "suggestion": "明确各项税费（个人所得税、印花税等）的承担方", "reference": "《税收征收管理法》"},
                {"level": "medium", "clause": "第十条 过渡期", "content": "未约定过渡期安排", "issue": "未约定签署后至交割完成前的过渡期管理安排，存在公司被不当经营的风险。", "suggestion": "增加过渡期条款，限制转让方在过渡期的重大经营决策权", "reference": "《公司法》"},
                {"level": "low", "clause": "第十二条 管辖", "content": "争议由北京仲裁委员会仲裁", "issue": "仲裁条款有效，但建议同时明确仲裁规则和仲裁庭组成方式。", "suggestion": "补充约定仲裁适用简易程序或普通程序、仲裁庭组成方式等", "reference": "《仲裁法》"},
            ],
            "missing_clauses": ["保密条款", "竞业禁止条款", "优先购买权放弃声明"],
            "score": 30,
        },
    },
]


# ==========================================
# Document Router Endpoints
# ==========================================

@router.get("/templates")
async def get_document_templates(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    category: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
):
    templates = list(_DOCUMENT_TEMPLATES)

    if category:
        templates = [t for t in templates if t["category"] == category]
    if keyword:
        kw = keyword.lower()
        templates = [
            t for t in templates
            if kw in t["name"].lower() or kw in t["description"].lower()
        ]

    total = len(templates)
    start = (page - 1) * page_size
    end = start + page_size
    items = templates[start:end]

    return {
        "items": [
            {
                "id": t["id"],
                "name": t["name"],
                "category": t["category"],
                "description": t["description"],
                "download_count": t["download_count"],
                "is_free": t["is_free"],
                "price": t["price"],
                "preview_url": t.get("preview_url"),
                "created_at": t["created_at"],
            }
            for t in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/templates/{template_id}")
async def get_document_template_detail(template_id: str):
    for t in _DOCUMENT_TEMPLATES:
        if t["id"] == template_id:
            return {
                "id": t["id"],
                "name": t["name"],
                "category": t["category"],
                "description": t["description"],
                "download_count": t["download_count"],
                "is_free": t["is_free"],
                "price": t["price"],
                "preview_url": t.get("preview_url"),
                "created_at": t["created_at"],
                "fields": t["fields"],
                "content_preview": t.get("content_preview"),
            }
    return {"detail": "模板不存在"}, 404


@router.post("/generate")
async def generate_document(request: GenerateDocumentRequest):
    for t in _DOCUMENT_TEMPLATES:
        if t["id"] == request.template_id:
            content = t.get("content_preview", "")
            for field_name, field_value in request.fields.items():
                content = content.replace(f"{{{field_name}}}", field_value)
            return {
                "document_type": t["category"],
                "title": t["name"].replace("模板", "").strip() + "（已生成）",
                "content": content,
                "created_at": datetime.now().isoformat(),
                "template_key": t["id"],
                "template_version": 1,
                "download_url": f"/api/documents/download/{t['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx",
            }
    return {"detail": "模板不存在"}, 404


@router.get("/categories")
async def get_document_categories():
    return {"categories": _DOCUMENT_CATEGORIES}


# ==========================================
# Contract Router Endpoints
# ==========================================

@contract_router.get("/reviews")
async def get_contract_reviews(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: Optional[str] = Query(default=None),
):
    reviews = list(_CONTRACT_REVIEWS)

    if status:
        reviews = [r for r in reviews if r["status"] == status]

    total = len(reviews)
    start = (page - 1) * page_size
    end = start + page_size
    items = reviews[start:end]

    return {
        "items": [
            {
                "id": r["id"],
                "filename": r["filename"],
                "contract_type": r["contract_type"],
                "status": r["status"],
                "risk_level": r["risk_level"],
                "risk_count": r["risk_count"],
                "request_id": r["request_id"],
                "created_at": r["created_at"],
            }
            for r in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@contract_router.post("/review")
async def review_contract(request: ReviewContractRequest):
    review_id = f"r{len(_CONTRACT_REVIEWS) + 1}"
    return {
        "review_id": review_id,
        "request_id": f"req-{len(_CONTRACT_REVIEWS) + 1:03d}",
        "status": "pending",
        "message": "合同已提交审查，预计30秒内完成",
        "estimated_seconds": 30,
        "created_at": datetime.now().isoformat(),
    }


@contract_router.get("/reviews/{review_id}")
async def get_contract_review_detail(review_id: str):
    for r in _CONTRACT_REVIEWS:
        if r["id"] == review_id:
            return {
                "id": r["id"],
                "filename": r["filename"],
                "contract_type": r["contract_type"],
                "status": r["status"],
                "risk_level": r["risk_level"],
                "risk_count": r["risk_count"],
                "text_chars": r["text_chars"],
                "text_preview": r["text_preview"],
                "request_id": r["request_id"],
                "created_at": r["created_at"],
                "report_json": r["report"],
            }
    return {"detail": "审查记录不存在"}, 404


@contract_router.get("/templates")
async def get_contract_templates():
    return {"items": _CONTRACT_TEMPLATES, "total": len(_CONTRACT_TEMPLATES)}