"""推荐系统 API 路由 —— 律师 / 文章 / 服务推荐 + 首页聚合 + 反馈"""

from datetime import datetime, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/recommendations", tags=["Recommendation"])

# ==================== Mock 数据 ====================

_mock_lawyers: list[dict] = [
    {
        "id": "lawyer_001", "name": "张明远", "title": "高级合伙人 · 民商事诉讼",
        "description": "北京大学法学硕士，专注民商事诉讼二十年，擅长合同纠纷、公司治理、股权争议。累计代理案件350+件，胜诉率92%。",
        "image_url": "https://cdn.example.com/avatars/lawyer_001.jpg",
        "tags": ["合同纠纷", "公司法", "股权争议", "资深律师"],
        "score": 0.97, "reason": "您在合同纠纷领域有多次浏览记录，张律师是该领域评分最高的专家",
        "rating": 4.9, "review_count": 218, "consultation_count": 520,
        "lawyer_id": 1, "is_verified": True, "match_score": 0.97,
        "city": "北京", "firm_name": "京华律师事务所",
    },
    {
        "id": "lawyer_002", "name": "李思远", "title": "合伙人 · 刑事辩护",
        "description": "中国政法大学刑法学博士，十五年刑事辩护经验。曾办理多起在全国有重大影响的刑事案件，擅长经济犯罪辩护与取保候审。",
        "image_url": "https://cdn.example.com/avatars/lawyer_002.jpg",
        "tags": ["刑事辩护", "经济犯罪", "取保候审", "二审辩护"],
        "score": 0.93, "reason": "您最近搜索过'刑事辩护'相关关键词，李律师在该领域经验丰富",
        "rating": 4.7, "review_count": 156, "consultation_count": 380,
        "lawyer_id": 2, "is_verified": True, "match_score": 0.93,
        "city": "北京", "firm_name": "京华律师事务所",
    },
    {
        "id": "lawyer_003", "name": "王晓瑞", "title": "专职律师 · 知识产权",
        "description": "华东政法大学知识产权法硕士，十年知识产权维权经验。代理商标侵权、专利维权、著作权纠纷案件120+件。",
        "image_url": "https://cdn.example.com/avatars/lawyer_003.jpg",
        "tags": ["知识产权", "商标维权", "专利诉讼", "著作权"],
        "score": 0.91, "reason": "您关注的知识产权保护话题与此律师专长高度匹配",
        "rating": 4.8, "review_count": 98, "consultation_count": 260,
        "lawyer_id": 3, "is_verified": True, "match_score": 0.91,
        "city": "上海", "firm_name": "天元律师事务所",
    },
    {
        "id": "lawyer_004", "name": "赵铭轩", "title": "副主任 · 投资并购",
        "description": "哈佛大学法学院LLM，十二年跨境投资并购经验。主导过多个超亿元并购项目，擅长尽职调查与交易结构设计。",
        "image_url": "https://cdn.example.com/avatars/lawyer_004.jpg",
        "tags": ["投资并购", "尽职调查", "资本市场", "跨境交易"],
        "score": 0.88, "reason": "与您同城的用户中有32%咨询过投资并购法律问题",
        "rating": 4.9, "review_count": 74, "consultation_count": 190,
        "lawyer_id": 4, "is_verified": True, "match_score": 0.88,
        "city": "上海", "firm_name": "天元律师事务所",
    },
    {
        "id": "lawyer_005", "name": "陈浩宇", "title": "专职律师 · 劳动争议",
        "description": "西南政法大学劳动法方向硕士，八年专注于劳动争议与工伤赔偿。代理劳动争议案件180+件，农民工维权公益律师。",
        "image_url": "https://cdn.example.com/avatars/lawyer_005.jpg",
        "tags": ["劳动争议", "工伤赔偿", "社保纠纷", "经济补偿"],
        "score": 0.86, "reason": "您浏览过'被公司辞退怎么办'相关文章，陈律师专攻劳动关系纠纷",
        "rating": 4.5, "review_count": 132, "consultation_count": 410,
        "lawyer_id": 5, "is_verified": True, "match_score": 0.86,
        "city": "广州", "firm_name": "正法律师事务所",
    },
    {
        "id": "lawyer_006", "name": "刘慧娴", "title": "主任 · 婚姻家事",
        "description": "中国人民大学法学博士，十八年婚姻家事领域经验。擅长离婚财产分割、子女抚养权争议、遗产继承规划。",
        "image_url": "https://cdn.example.com/avatars/lawyer_006.jpg",
        "tags": ["离婚纠纷", "财产分割", "子女抚养", "遗产继承"],
        "score": 0.90, "reason": "婚姻家事类问题在您的城市用户中咨询量排名前三",
        "rating": 4.9, "review_count": 289, "consultation_count": 640,
        "lawyer_id": 6, "is_verified": True, "match_score": 0.90,
        "city": "广州", "firm_name": "正法律师事务所",
    },
    {
        "id": "lawyer_007", "name": "周博文", "title": "合伙人 · 房地产与建设工程",
        "description": "清华大学民商法硕士，十五年房地产法律服务经验。擅长商品房买卖纠纷、建设工程合同、拆迁补偿。",
        "image_url": "https://cdn.example.com/avatars/lawyer_007.jpg",
        "tags": ["房产纠纷", "建设工程", "拆迁补偿", "物业纠纷"],
        "score": 0.83, "reason": "房地产纠纷在平台整体咨询量中占比21%，是热门法律服务方向",
        "rating": 4.6, "review_count": 175, "consultation_count": 450,
        "lawyer_id": 7, "is_verified": True, "match_score": 0.83,
        "city": "深圳", "firm_name": "鹏城律师事务所",
    },
    {
        "id": "lawyer_008", "name": "吴嘉禾", "title": "专职律师 · 消费者权益",
        "description": "武汉大学经济法硕士，九年消费者权益保护经验。专注网购维权、食品安全索赔、金融消费纠纷。",
        "image_url": "https://cdn.example.com/avatars/lawyer_008.jpg",
        "tags": ["消费维权", "网购纠纷", "食品安全", "退一赔三"],
        "score": 0.80, "reason": "您所在的年龄段用户（25-35岁）中消费维权咨询量显著增长",
        "rating": 4.4, "review_count": 88, "consultation_count": 310,
        "lawyer_id": 8, "is_verified": False, "match_score": 0.80,
        "city": "杭州", "firm_name": "钱塘律师事务所",
    },
    {
        "id": "lawyer_009", "name": "郑知行", "title": "高级顾问 · 税务筹划",
        "description": "厦门大学财税法学博士，注册会计师兼执业律师。专攻企业税务筹划、税务争议解决与个税申报合规。",
        "image_url": "https://cdn.example.com/avatars/lawyer_009.jpg",
        "tags": ["税务筹划", "税务争议", "企业税务", "个税合规"],
        "score": 0.78, "reason": "您浏览过大量企业经营管理类内容，税务是企业高频法律需求",
        "rating": 4.7, "review_count": 63, "consultation_count": 180,
        "lawyer_id": 9, "is_verified": True, "match_score": 0.78,
        "city": "厦门", "firm_name": "鹭岛律师事务所",
    },
    {
        "id": "lawyer_010", "name": "孙雅婷", "title": "合伙人 · 行政诉讼",
        "description": "吉林大学宪法与行政法学博士，十四年行政诉讼经验。擅长行政处罚复议、征地拆迁诉讼、信息公开申请。",
        "image_url": "https://cdn.example.com/avatars/lawyer_010.jpg",
        "tags": ["行政诉讼", "行政复议", "征地拆迁", "信息公开"],
        "score": 0.76, "reason": "平台近期行政诉讼类内容阅读量上升47%，您可能对此感兴趣",
        "rating": 4.5, "review_count": 92, "consultation_count": 240,
        "lawyer_id": 10, "is_verified": True, "match_score": 0.76,
        "city": "成都", "firm_name": "锦城律师事务所",
    },
]

_mock_articles: list[dict] = [
    {
        "id": "article_001", "title": "劳动合同到期不续签，公司需要支付经济补偿吗？",
        "description": "详解《劳动合同法》第46条，劳动合同期满终止时用人单位应支付经济补偿金的法定情形与计算方式。",
        "image_url": "https://cdn.example.com/articles/labor_contract.jpg",
        "tags": ["劳动法", "经济补偿", "合同到期", "员工权益"],
        "score": 0.96, "reason": "您最近3天浏览了5篇劳动法相关内容",
        "category": "劳动就业", "view_count": 12580, "match_score": 0.96,
        "created_at": "2025-05-10T09:00:00",
    },
    {
        "id": "article_002", "title": "2025年最新婚姻法司法解释：离婚冷静期适用详解",
        "description": "深度解读2025年婚姻家庭编司法解释，离婚冷静期的适用范围、例外情形及实务操作指南。",
        "image_url": "https://cdn.example.com/articles/marriage_explanation.jpg",
        "tags": ["婚姻法", "离婚冷静期", "司法解释", "家事法律"],
        "score": 0.94, "reason": "与您同城用户最常阅读的法律文章之一",
        "category": "婚姻家庭", "view_count": 18200, "match_score": 0.94,
        "created_at": "2025-05-08T14:00:00",
    },
    {
        "id": "article_003", "title": "遭遇网络诈骗后如何快速维权？律师教你五步操作指南",
        "description": "从证据固定、报案流程、银行止付到民事诉讼，全方位网络诈骗维权实操指南，附报警材料清单模板。",
        "image_url": "https://cdn.example.com/articles/online_fraud.jpg",
        "tags": ["网络诈骗", "维权指南", "刑事报案", "证据保全"],
        "score": 0.92, "reason": "当前社会热点话题，近一周平台阅读量增长63%",
        "category": "刑事法律", "view_count": 23100, "match_score": 0.92,
        "created_at": "2025-05-12T10:30:00",
    },
    {
        "id": "article_004", "title": "二手房买卖避坑指南：这8个合同条款一定要看清",
        "description": "资深房产律师总结的二手房交易8大关键条款——产权核验、定金条款、交房标准、户口迁移等核心要点。",
        "image_url": "https://cdn.example.com/articles/house_guide.jpg",
        "tags": ["房产交易", "合同审查", "二手房", "法律风险"],
        "score": 0.89, "reason": "您搜索过'买房注意事项'，该文章系统梳理了购房法律要点",
        "category": "房产物业", "view_count": 9800, "match_score": 0.89,
        "created_at": "2025-05-05T08:00:00",
    },
    {
        "id": "article_005", "title": "创业公司股权分配方案：从4人合伙到融资稀释全解析",
        "description": "创业股权分配的'坑'有哪些？动态股权、限制性股权、期权池设置与投资人进入后的稀释机制全面解读。",
        "image_url": "https://cdn.example.com/articles/startup_equity.jpg",
        "tags": ["公司法", "股权架构", "创业法律", "融资"],
        "score": 0.87, "reason": "您关注了多个创业法律话题，该文章是平台年度精选内容",
        "category": "公司治理", "view_count": 7600, "match_score": 0.87,
        "created_at": "2025-04-28T16:00:00",
    },
    {
        "id": "article_006", "title": "交通事故赔偿标准2025版：伤残等级与赔偿金额对照表",
        "description": "2025年度最新人身损害赔偿标准，含医疗费、误工费、护理费、残疾赔偿金、精神抚慰金的计算方式与司法实践。",
        "image_url": "https://cdn.example.com/articles/traffic_compensation.jpg",
        "tags": ["交通事故", "人身损害", "赔偿标准", "保险理赔"],
        "score": 0.85, "reason": "交通法律类内容在您所在省份的用户中阅读转化率最高",
        "category": "交通事故", "view_count": 15600, "match_score": 0.85,
        "created_at": "2025-05-01T11:00:00",
    },
    {
        "id": "article_007", "title": "民间借贷利息上限最新规定：超过这个利率法院不支持",
        "description": "结合2025年LPR最新报价，详解民间借贷利率司法保护上限的变化、计算方式及新旧规定过渡适用规则。",
        "image_url": "https://cdn.example.com/articles/private_lending.jpg",
        "tags": ["民间借贷", "利率上限", "债务纠纷", "LPR"],
        "score": 0.83, "reason": "平台纠纷解决类文章中读者留存率最高的内容之一",
        "category": "债权债务", "view_count": 11200, "match_score": 0.83,
        "created_at": "2025-05-03T09:30:00",
    },
    {
        "id": "article_008", "title": "公司不交社保怎么办？5种维权途径及赔偿标准全知道",
        "description": "用人单位未依法缴纳社会保险的维权路径：劳动监察投诉、社保稽核、劳动仲裁、诉讼及税务举报的全流程指南。",
        "image_url": "https://cdn.example.com/articles/social_insurance.jpg",
        "tags": ["社保权益", "劳动维权", "企业合规", "赔偿标准"],
        "score": 0.90, "reason": "您注册时勾选了'劳动权益保障'为关注领域",
        "category": "劳动就业", "view_count": 19400, "match_score": 0.90,
        "created_at": "2025-05-11T07:00:00",
    },
    {
        "id": "article_009", "title": "借钱不还怎么办？民事诉讼全流程：从起诉到强制执行",
        "description": "民间借贷纠纷诉讼全攻略：诉前准备、证据清单、起诉状模板、财产保全申请及强制执行程序的完整操作指引。",
        "image_url": "https://cdn.example.com/articles/lawsuit_guide.jpg",
        "tags": ["民事诉讼", "强制执行", "起诉流程", "债权追讨"],
        "score": 0.81, "reason": "结合您的浏览历史，债务纠纷类文章对您参考价值较高",
        "category": "债权债务", "view_count": 14300, "match_score": 0.81,
        "created_at": "2025-05-06T13:00:00",
    },
    {
        "id": "article_010", "title": "小区物业不作为，业主可以拒交物业费吗？律师权威解答",
        "description": "从《民法典》物业服务合同角度，分析业主在哪些情形下有权要求减免物业费，以及合规维权方式。",
        "image_url": "https://cdn.example.com/articles/property_dispute.jpg",
        "tags": ["物业纠纷", "民法典", "业主权益", "物业服务"],
        "score": 0.79, "reason": "平台推荐算法识别到您对消费者权益类话题有持续关注",
        "category": "房产物业", "view_count": 8700, "match_score": 0.79,
        "created_at": "2025-05-02T15:00:00",
    },
    {
        "id": "article_011", "title": "电商平台买到假货，如何主张'退一赔三'？维权流程详解",
        "description": "基于《消费者权益保护法》第55条，详解网购假货认定的证据链要求、赔偿计算及平台责任。",
        "image_url": "https://cdn.example.com/articles/consumer_rights.jpg",
        "tags": ["消费者权益", "退一赔三", "网购维权", "假冒伪劣"],
        "score": 0.84, "reason": "您最近点击过多个消费者维权相关内容",
        "category": "消费维权", "view_count": 10800, "match_score": 0.84,
        "created_at": "2025-05-09T10:00:00",
    },
    {
        "id": "article_012", "title": "遗嘱怎么写才有效？六种遗嘱形式的法律要件对比",
        "description": "自书遗嘱、代书遗嘱、打印遗嘱、录音录像遗嘱、口头遗嘱、公证遗嘱——六种形式的法定要求与效力层级全解析。",
        "image_url": "https://cdn.example.com/articles/will_guide.jpg",
        "tags": ["遗嘱继承", "遗产规划", "家事法律", "公证"],
        "score": 0.82, "reason": "中老年用户群体中关注度最高的普法内容",
        "category": "婚姻家庭", "view_count": 9200, "match_score": 0.82,
        "created_at": "2025-05-04T16:30:00",
    },
]

_mock_services: list[dict] = [
    {
        "id": "service_001", "name": "在线律师咨询",
        "description": "一对一线上律师咨询，30分钟内专业律师回复。覆盖民事、刑事、行政等全领域，首次咨询享15分钟免费。",
        "image_url": "https://cdn.example.com/services/online_consult.jpg",
        "tags": ["法律咨询", "线上服务", "即时响应"],
        "score": 0.98, "reason": "平台最受欢迎的服务，超过85%的用户将咨询作为第一步",
    },
    {
        "id": "service_002", "name": "合同审查与起草",
        "description": "专业律师为您审查各类合同风险条款，或根据需求定制起草合同。覆盖买卖、租赁、劳务、合伙等常见合同类型。",
        "image_url": "https://cdn.example.com/services/contract_review.jpg",
        "tags": ["合同审查", "合同起草", "风险排查"],
        "score": 0.94, "reason": "您最近上传过合同文件，合同审查服务适合您的当前需求",
    },
    {
        "id": "service_003", "name": "律师函发送",
        "description": "由执业律师为您的纠纷出具正式律师函，具有法律效力的书面催告文件。适用于欠款催收、违约通知、侵权警告等场景。",
        "image_url": "https://cdn.example.com/services/lawyer_letter.jpg",
        "tags": ["律师函", "催告通知", "正式维权"],
        "score": 0.90, "reason": "纠纷解决类服务中转化率最高的产品",
    },
    {
        "id": "service_004", "name": "诉讼代理",
        "description": "全流程诉讼代理服务，从起诉立案、证据准备、庭审代理到执行申请一站式办理。",
        "image_url": "https://cdn.example.com/services/litigation.jpg",
        "tags": ["诉讼代理", "出庭应诉", "强制执行"],
        "score": 0.87, "reason": "服务评价4.8分，用户回购率最高的法律服务之一",
    },
    {
        "id": "service_005", "name": "企业法律顾问",
        "description": "为中小企业提供常年法律顾问服务：合同管理、劳动合规、股权架构、知识产权保护、法律风险体检。",
        "image_url": "https://cdn.example.com/services/corporate_counsel.jpg",
        "tags": ["法律顾问", "企业合规", "常年服务"],
        "score": 0.85, "reason": "您浏览过企业经营管理内容，常年顾问可系统性解决法律风险",
    },
    {
        "id": "service_006", "name": "知识产权申请与维权",
        "description": "商标注册、专利申请、著作权登记的一站式代理服务，以及侵权监测与维权诉讼支持。",
        "image_url": "https://cdn.example.com/services/ip_service.jpg",
        "tags": ["商标注册", "专利申请", "版权保护"],
        "score": 0.82, "reason": "近三个月知识产权相关服务咨询量增长42%",
    },
    {
        "id": "service_007", "name": "劳动争议仲裁代理",
        "description": "为劳动者或用人单位代理劳动争议仲裁与诉讼，涵盖违法辞退、欠薪追讨、工伤认定、竞业限制争议。",
        "image_url": "https://cdn.example.com/services/labor_arbitration.jpg",
        "tags": ["劳动仲裁", "工伤认定", "欠薪维权"],
        "score": 0.88, "reason": "您关注的劳动权益话题与该服务高度相关",
    },
]

_mock_feedbacks: list[dict] = []


# ==================== 请求模型 ====================

class FeedbackRequest(BaseModel):
    recommendation_id: str
    rating: float
    reason: Optional[str] = None


# ==================== 端点 1: 推荐律师 ====================

@router.get("/lawyers")
async def recommend_lawyers(
    limit: int = Query(default=8, ge=1, le=20, description="返回律师数量"),
    category: Optional[str] = Query(default=None, description="按领域筛选：合同纠纷/刑事辩护/知识产权/劳动争议 等"),
    city: Optional[str] = Query(default=None, description="按城市筛选"),
):
    """获取个性化律师推荐（基于用户画像与浏览历史）"""
    results = list(_mock_lawyers)
    if category:
        results = [l for l in results if category in l.get("tags", [])]
    if city:
        results = [l for l in results if l.get("city") == city]
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:limit]
    return {
        "lawyers": results,
        "total": len(results),
        "recommendation_source": "collaborative_filtering_v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ==================== 端点 2: 推荐文章 ====================

@router.get("/articles")
async def recommend_articles(
    limit: int = Query(default=10, ge=1, le=30, description="返回文章数量"),
    category: Optional[str] = Query(default=None, description="按分类筛选：劳动就业/婚姻家庭/刑事法律/房产物业 等"),
):
    """获取推荐法律知识文章"""
    results = list(_mock_articles)
    if category:
        results = [a for a in results if a.get("category") == category]
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:limit]
    return {
        "articles": results,
        "total": len(results),
        "recommendation_source": "content_based_v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ==================== 端点 3: 推荐服务 ====================

@router.get("/services")
async def recommend_services():
    """获取推荐法律服务"""
    results = sorted(_mock_services, key=lambda x: x["score"], reverse=True)
    return {
        "services": results,
        "total": len(results),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ==================== 端点 4: 首页聚合推荐 ====================

@router.get("/homepage")
async def get_homepage_recommendations(
    lawyer_limit: int = Query(default=4, ge=1, le=10, description="首页展示律师数量"),
    article_limit: int = Query(default=6, ge=1, le=10, description="首页展示文章数量"),
):
    """获取首页聚合推荐数据：精选律师 + 热门文章 + 推荐服务"""
    top_lawyers = sorted(_mock_lawyers, key=lambda x: x["score"], reverse=True)[:lawyer_limit]
    top_articles = sorted(_mock_articles, key=lambda x: x["score"], reverse=True)[:article_limit]
    top_services = sorted(_mock_services, key=lambda x: x["score"], reverse=True)[:4]

    hot_tags = [
        {"tag": "合同纠纷", "count": 3240},
        {"tag": "劳动争议", "count": 2850},
        {"tag": "婚姻家庭", "count": 2410},
        {"tag": "交通事故", "count": 1980},
        {"tag": "消费维权", "count": 1650},
        {"tag": "民间借贷", "count": 1520},
        {"tag": "知识产权", "count": 1180},
        {"tag": "刑事辩护", "count": 960},
    ]

    return {
        "featured_lawyers": top_lawyers,
        "hot_articles": top_articles,
        "popular_services": top_services,
        "hot_tags": hot_tags,
        "recommendation_source": "homepage_aggregator_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ==================== 端点 5: 推荐反馈 ====================

@router.post("/feedback")
async def submit_feedback(body: FeedbackRequest):
    """记录用户对推荐结果的反馈"""
    _mock_feedbacks.append({
        "recommendation_id": body.recommendation_id,
        "rating": body.rating,
        "reason": body.reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {
        "success": True,
        "message": "反馈已记录，感谢您帮助改进推荐系统" if body.rating >= 3 else "反馈已记录，我们会持续优化推荐效果",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }