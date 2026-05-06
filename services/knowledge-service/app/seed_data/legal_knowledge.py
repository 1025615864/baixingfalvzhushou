"""法律知识种子数据"""
from typing import List, Dict


LEGAL_KNOWLEDGE_SEED_DATA: List[Dict] = [
    {
        "title": "中华人民共和国民法典 - 合同编",
        "category": "民法",
        "knowledge_type": "law",
        "content": "《中华人民共和国民法典》合同编规定了合同的订立、效力、履行、变更、转让、权利义务终止、违约责任等内容。",
        "keywords": "民法典,合同,订立,效力,履行",
        "source": "官方发布",
        "law_number": "民法典",
        "jurisdiction": "全国",
        "effective_date": "2021-01-01"
    },
    {
        "title": "中华人民共和国劳动法 - 工作时间与休息休假",
        "category": "劳动法",
        "knowledge_type": "law",
        "content": "《中华人民共和国劳动法》规定国家实行劳动者每日工作时间不超过八小时、平均每周工作时间不超过四十四小时的工时制度。",
        "keywords": "劳动法,工时,休息,休假,加班",
        "source": "官方发布",
        "law_number": "劳动法",
        "jurisdiction": "全国",
        "effective_date": "2018-12-29"
    },
    {
        "title": "中华人民共和国公司法 - 公司设立",
        "category": "公司法",
        "knowledge_type": "law",
        "content": "《中华人民共和国公司法》规定设立公司应当依法制定公司章程。公司章程对公司、股东、董事、监事、高级管理人员具有约束力。",
        "keywords": "公司法,公司设立,章程,股东,董事",
        "source": "官方发布",
        "law_number": "公司法",
        "jurisdiction": "全国",
        "effective_date": "2023-12-29"
    },
    {
        "title": "中华人民共和国刑法 - 故意伤害罪",
        "category": "刑法",
        "knowledge_type": "law",
        "content": "《中华人民共和国刑法》第二百三十四条规定，故意伤害他人身体的，处三年以下有期徒刑、拘役或者管制。",
        "keywords": "刑法,故意伤害,有期徒刑,刑罚",
        "source": "官方发布",
        "law_number": "刑法",
        "jurisdiction": "全国",
        "effective_date": "2023-03-14"
    },
    {
        "title": "中华人民共和国婚姻法 - 离婚财产分割",
        "category": "婚姻法",
        "knowledge_type": "law",
        "content": "《中华人民共和国民法典》婚姻家庭编规定，离婚时，夫妻的共同财产由双方协议处理；协议不成的，由人民法院根据财产的具体情况，按照照顾子女、女方和无过错方权益的原则判决。",
        "keywords": "婚姻法,离婚,财产分割,共同财产",
        "source": "官方发布",
        "law_number": "民法典",
        "jurisdiction": "全国",
        "effective_date": "2021-01-01"
    },
    {
        "title": "中华人民共和国消费者权益保护法 - 退货换货",
        "category": "消费者权益",
        "knowledge_type": "law",
        "content": "《中华人民共和国消费者权益保护法》规定，经营者提供的商品或者服务不符合质量要求的，消费者可以依照国家规定、当事人约定退货，或者要求经营者履行更换、修理等义务。",
        "keywords": "消费者权益,退货,换货,质量,经营者",
        "source": "官方发布",
        "law_number": "消费者权益保护法",
        "jurisdiction": "全国",
        "effective_date": "2013-10-25"
    },
    {
        "title": "中华人民共和国交通事故处理程序",
        "category": "交通事故",
        "knowledge_type": "procedure",
        "content": "道路交通事故处理程序规定：发生交通事故后，当事人应当立即停车，保护现场，抢救受伤人员，并迅速报告执勤的交通警察或者公安机关交通管理部门。",
        "keywords": "交通事故,处理程序,保护现场,报警",
        "source": "公安部规章",
        "law_number": "道路交通事故处理程序规定",
        "jurisdiction": "全国",
        "effective_date": "2018-05-01"
    },
    {
        "title": "房屋租赁合同要点",
        "category": "房产",
        "knowledge_type": "guide",
        "content": "房屋租赁合同应当约定租赁期限、租金及支付方式、房屋维修责任、违约金等条款。租赁期限不得超过二十年，超过部分无效。",
        "keywords": "房屋租赁,合同要点,租赁期限,租金",
        "source": "法律指南",
        "jurisdiction": "全国",
        "effective_date": "2021-01-01"
    },
    {
        "title": "劳动仲裁程序指南",
        "category": "劳动法",
        "knowledge_type": "guide",
        "content": "劳动争议仲裁是劳动争议当事人向人民法院提起诉讼的必经程序。申请劳动仲裁的时效期间为一年，从当事人知道或者应当知道其权利被侵害之日起计算。",
        "keywords": "劳动仲裁,争议,时效,诉讼",
        "source": "法律指南",
        "jurisdiction": "全国",
        "effective_date": "2021-01-01"
    },
    {
        "title": "知识产权保护基本知识",
        "category": "知识产权",
        "knowledge_type": "guide",
        "content": "知识产权包括专利权、商标权、著作权等。发明专利权的期限为二十年，实用新型专利权和外观设计专利权的期限为十年，商标权的期限为十年，可以续展。",
        "keywords": "知识产权,专利,商标,著作权,保护期限",
        "source": "法律指南",
        "jurisdiction": "全国",
        "effective_date": "2021-01-01"
    }
]


GUIDE_CASES_SEED_DATA: List[Dict] = [
    {
        "case_number": "(2019)最高法民终1234号",
        "title": "某房地产开发有限公司与某建筑公司建设工程施工合同纠纷案",
        "case_type": "民事",
        "court_name": "最高人民法院",
        "court_level": "最高院",
        "judge_date": "2019-12-20",
        "cause_of_action": "建设工程施工合同纠纷",
        "judgment_result": "维持原判",
        "key_points": "1. 建设工程价款优先受偿权的认定 2. 工程质量问题与价款支付的关系 3. 违约责任的承担方式",
        "applicable_laws": "《合同法》第286条，《建设工程施工合同解释》第17条",
        "is_guiding_case": True,
        "source": "最高人民法院公报",
        "facts": "原告某房地产开发公司与被告某建筑公司签订建设工程施工合同，约定由被告承建某商业综合体项目。合同履行过程中，因工程款支付问题产生争议。",
        "litigation_history": "一审法院判决被告支付工程款及利息，二审维持原判。"
    },
    {
        "case_number": "(2020)最高法刑再123号",
        "title": "张某故意伤害案",
        "case_type": "刑事",
        "court_name": "最高人民法院",
        "court_level": "最高院",
        "judge_date": "2020-06-15",
        "cause_of_action": "故意伤害罪",
        "judgment_result": "改判",
        "key_points": "1. 正当防卫的认定标准 2. 防卫过当的判断 3. 刑事附带民事赔偿责任",
        "applicable_laws": "《刑法》第20条、第234条",
        "is_guiding_case": True,
        "source": "最高人民法院公报",
        "facts": "被告人张某与被害人李某因邻里纠纷发生争执，张某持木棍击打李某，致李某轻伤。一审认定故意伤害罪，判处有期徒刑一年。",
        "litigation_history": "再审认定张某行为属于防卫过当，改判免予刑事处罚。"
    },
    {
        "case_number": "(2021)粤高法民初456号",
        "title": "某科技公司与某员工竞业限制纠纷案",
        "case_type": "民事",
        "court_name": "广东省高级人民法院",
        "court_level": "高院",
        "judge_date": "2021-08-20",
        "cause_of_action": "竞业限制纠纷",
        "judgment_result": "部分支持",
        "key_points": "1. 竞业限制协议的效力 2. 经济补偿金的支付标准 3. 违约责任的认定",
        "applicable_laws": "《劳动合同法》第23条、第24条",
        "is_guiding_case": False,
        "source": "广东省高级人民法院",
        "facts": "原告某科技公司诉称被告离职员工违反竞业限制约定，要求支付违约金及赔偿损失。",
        "litigation_history": "一审判决被告支付违约金，但适当调低数额。"
    }
]


COMMON_COURT_LEVELS = [
    {"code": "基层", "name": "基层人民法院", "level": 1},
    {"code": "中院", "name": "中级人民法院", "level": 2},
    {"code": "高院", "name": "高级人民法院", "level": 3},
    {"code": "最高院", "name": "最高人民法院", "level": 4},
]


COMMON_CASE_TYPES = [
    {"code": "civil", "name": "民事案件"},
    {"code": "criminal", "name": "刑事案件"},
    {"code": "administrative", "name": "行政案件"},
    {"code": "execution", "name": "执行案件"},
]


COMMON_CAUSE_OF_ACTIONS = [
    "合同纠纷",
    "侵权责任纠纷",
    "劳动争议",
    "婚姻家庭纠纷",
    "建设工程施工合同纠纷",
    "买卖合同纠纷",
    "借款合同纠纷",
    "房屋买卖合同纠纷",
    "知识产权纠纷",
    "交通事故责任纠纷",
]
