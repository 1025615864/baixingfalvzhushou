"""AI咨询关键词提取服务

从AI咨询内容中提取法律相关的关键词，用于律师匹配推荐
"""
import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class KeywordExtractionService:
    """关键词提取服务"""

    # 法律领域关键词映射
    LEGAL_DOMAINS = {
        "劳动纠纷": [
            "劳动合同", "工资", "加班费", "社保", "公积金", "工伤", "解除劳动合同",
            "辞退", "裁员", "试用期", "竞业限制", "经济补偿", "赔偿金", "劳动仲裁",
            "劳动关系", "劳务派遣", "非全日制", "最低工资", "带薪年假", "病假",
            "产假", "婚假", "工伤认定", "职业病", "劳动监察", "劳动争议"
        ],
        "婚姻家庭": [
            "离婚", "财产分割", "子女抚养", "抚养费", "探视权", "赡养", "继承",
            "遗嘱", "遗赠", "夫妻共同财产", "婚前财产", "彩礼", "嫁妆", "家暴",
            "家庭暴力", "婚姻无效", "撤销婚姻", "同居关系", "非婚生子女", "收养",
            "监护", "抚养权", "探望权", "分居", "协议离婚", "诉讼离婚"
        ],
        "合同纠纷": [
            "合同", "违约", "违约金", "解除合同", "撤销合同", "无效合同", "合同诈骗",
            "买卖合同", "租赁合同", "借款合同", "服务合同", "建设工程合同", "承揽合同",
            "定金", "订金", "押金", "保证金", "违约责任", "合同履行", "合同变更",
            "合同转让", "合同解除", "合同终止", "合同无效", "合同撤销", "合同纠纷"
        ],
        "交通事故": [
            "交通事故", "责任认定", "赔偿", "伤残鉴定", "误工费", "护理费", "营养费",
            "交通费", "住宿费", "精神损害赔偿", "死亡赔偿金", "残疾赔偿金", "被扶养人生活费",
            "车辆损失", "保险理赔", "交强险", "商业险", "责任划分", "全责", "主责",
            "次责", "同等责任", "无责", "逃逸", "酒驾", "醉驾", "无证驾驶"
        ],
        "借贷纠纷": [
            "借款", "贷款", "借条", "欠条", "利息", "高利贷", "民间借贷", "银行贷款",
            "信用卡", "逾期", "催收", "担保", "抵押", "质押", "保证", "连带责任",
            "债务", "债权", "债务重组", "破产", "清算", "执行", "强制执行", "财产保全"
        ],
        "房产纠纷": [
            "房产", "房屋买卖", "房屋租赁", "房屋拆迁", "房屋征收", "产权", "房产证",
            "不动产登记", "抵押贷款", "公积金贷款", "二手房", "新房", "商品房", "经济适用房",
            "公房", "小产权房", "违章建筑", "物业纠纷", "业主委员会", "物业管理", "车位"
        ],
        "知识产权": [
            "专利", "商标", "著作权", "版权", "商业秘密", "不正当竞争", "侵权", "许可",
            "转让", "专利申请", "商标注册", "软件著作权", "著作权登记", "技术秘密",
            "商业秘密保护", "反不正当竞争", "假冒伪劣", "盗版", "侵权责任", "赔偿"
        ],
        "刑事辩护": [
            "刑事", "犯罪", "辩护", "取保候审", "监视居住", "逮捕", "拘留", "起诉",
            "判决", "量刑", "缓刑", "减刑", "假释", "无罪辩护", "罪轻辩护", "自首",
            "立功", "坦白", "认罪认罚", "刑事附带民事", "刑事赔偿", "国家赔偿"
        ],
        "行政诉讼": [
            "行政", "行政诉讼", "行政复议", "行政处罚", "行政许可", "行政强制", "行政征收",
            "行政裁决", "行政确认", "行政给付", "行政赔偿", "政府信息公开", "行政复议",
            "行政诉讼", "国家赔偿", "行政不作为", "行政违法", "行政侵权"
        ],
        "公司法": [
            "公司", "股东", "股权", "股权转让", "股东会", "董事会", "监事会", "公司章程",
            "公司设立", "公司变更", "公司注销", "公司清算", "公司破产", "公司合并", "公司分立",
            "公司增资", "公司减资", "公司解散", "公司治理", "股东权利", "股东义务", "股东责任"
        ],
        "侵权责任": [
            "侵权", "人身损害", "财产损害", "精神损害", "产品责任", "环境污染", "高度危险",
            "饲养动物", "物件损害", "医疗损害", "教育机构责任", "安全保障义务", "网络侵权",
            "名誉权", "肖像权", "隐私权", "姓名权", "荣誉权", "人格权", "身份权"
        ],
        "消费者权益": [
            "消费者", "消费者权益", "产品质量", "食品安全", "虚假宣传", "欺诈", "退换货",
            "三包", "售后服务", "价格欺诈", "霸王条款", "预付卡", "网购", "直播带货",
            "消费者协会", "投诉", "举报", "维权", "赔偿", "惩罚性赔偿"
        ]
    }

    # 常见法律术语
    LEGAL_TERMS = [
        "起诉", "上诉", "申诉", "抗诉", "执行", "保全", "证据", "举证", "质证",
        "鉴定", "勘验", "送达", "管辖", "回避", "代理", "辩护", "仲裁", "调解",
        "和解", "判决", "裁定", "决定", "命令", "通知", "公告", "送达", "执行",
        "强制执行", "申请执行", "执行异议", "执行复议", "执行监督", "执行回转",
        "再审", "二审", "终审", "一审", "二审", "三审", "审判监督", "检察监督"
    ]

    def __init__(self):
        """初始化关键词提取服务"""
        # 构建关键词到领域的反向映射
        self._keyword_to_domain = {}
        for domain, keywords in self.LEGAL_DOMAINS.items():
            for keyword in keywords:
                if keyword not in self._keyword_to_domain:
                    self._keyword_to_domain[keyword] = []
                self._keyword_to_domain[keyword].append(domain)

    def extract_keywords(self, text: str, max_keywords: int = 10) -> list[str]:
        """
        从文本中提取法律关键词

        Args:
            text: 输入文本
            max_keywords: 最大返回关键词数量

        Returns:
            关键词列表，按相关性排序
        """
        if not text or not isinstance(text, str):
            return []

        text = text.strip()
        if not text:
            return []

        # 提取所有匹配的关键词
        matched_keywords = []

        # 检查法律领域关键词
        for keyword, domains in self._keyword_to_domain.items():
            if keyword in text:
                matched_keywords.append((keyword, len(domains)))

        # 检查法律术语
        for term in self.LEGAL_TERMS:
            if term in text and term not in [kw[0] for kw in matched_keywords]:
                matched_keywords.append((term, 1))

        # 按匹配的领域数量排序（匹配领域越多，相关性越高）
        matched_keywords.sort(key=lambda x: x[1], reverse=True)

        # 提取关键词
        keywords = [kw[0] for kw in matched_keywords[:max_keywords]]

        logger.debug(f"从文本中提取关键词: {keywords}")
        return keywords

    def extract_domains(self, text: str) -> list[str]:
        """
        从文本中提取法律领域

        Args:
            text: 输入文本

        Returns:
            法律领域列表，按匹配度排序
        """
        if not text or not isinstance(text, str):
            return []

        text = text.strip()
        if not text:
            return []

        # 统计每个领域的匹配关键词数量
        domain_scores = {}
        for domain, keywords in self.LEGAL_DOMAINS.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            if score > 0:
                domain_scores[domain] = score

        # 按分数排序
        sorted_domains = sorted(
            domain_scores.items(),
            key=lambda x: x[1],
            reverse=True)

        domains = [d[0] for d in sorted_domains]
        logger.debug(f"从文本中提取法律领域: {domains}")
        return domains

    def extract_with_confidence(self, text: str) -> dict:
        """
        从文本中提取关键词和领域，并返回置信度

        Args:
            text: 输入文本

        Returns:
            包含关键词、领域和置信度的字典
        """
        keywords = self.extract_keywords(text)
        domains = self.extract_domains(text)

        # 计算置信度
        confidence = 0.0
        if keywords:
            # 基于关键词数量和领域匹配度计算置信度
            keyword_score = min(len(keywords) / 5.0, 1.0)  # 最多5个关键词得满分
            domain_score = min(len(domains) / 3.0, 1.0)  # 最多3个领域得满分
            confidence = (keyword_score + domain_score) / 2.0

        return {
            "keywords": keywords,
            "domains": domains,
            "confidence": round(confidence, 2)
        }


# 全局实例
_keyword_extraction_service = None


def get_keyword_extraction_service() -> KeywordExtractionService:
    """获取关键词提取服务实例（懒加载）"""
    global _keyword_extraction_service
    if _keyword_extraction_service is None:
        _keyword_extraction_service = KeywordExtractionService()
    return _keyword_extraction_service
