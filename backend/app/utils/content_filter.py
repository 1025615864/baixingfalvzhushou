"""内容过滤工具 - 敏感词过滤"""
import re

__all__ = [
    "ContentFilter",
    "SENSITIVE_WORDS",
    "AD_WORDS",
    "DEFAULT_AD_WORDS_THRESHOLD",
    "DEFAULT_CHECK_URL",
    "DEFAULT_CHECK_PHONE",
    "apply_content_filter_config",
    "check_post_content",
    "check_comment_content",
    "needs_review",
    "add_sensitive_word",
    "remove_sensitive_word",
    "get_all_sensitive_words",
    "add_ad_word",
    "remove_ad_word",
    "get_all_ad_words",
]

SENSITIVE_WORDS = [
    "代办假证", "办假证", "伪造证件", "假学历", "假文凭",
    "洗钱", "黑钱", "赌博网站", "网络赌博", "六合彩",
    "毒品", "冰毒", "大麻", "可卡因", "海洛因",
    "刷单兼职", "高额返利", "免费领取", "中奖通知",
    "杀人方法", "报复社会", "制造炸弹",
    "色情网站", "成人视频", "约炮",
    "翻墙软件", "VPN代理",
]

AD_WORDS = [
    "加微信", "加QQ", "免费领", "限时优惠", "点击链接",
    "扫码领取", "低价代办", "包过包拿证",
]


DEFAULT_AD_WORDS_THRESHOLD = 2
DEFAULT_CHECK_URL = True
DEFAULT_CHECK_PHONE = True


class ContentFilter:
    """内容过滤器"""

    def __init__(
        self,
        custom_words: list[str] | None = None,
        ad_threshold: int = DEFAULT_AD_WORDS_THRESHOLD,
        check_url: bool = DEFAULT_CHECK_URL,
        check_phone: bool = DEFAULT_CHECK_PHONE,
    ):
        self.sensitive_words: set[str] = set(SENSITIVE_WORDS)
        self.ad_words: set[str] = set(AD_WORDS)
        self.ad_threshold: int = int(ad_threshold) if int(
            ad_threshold) > 0 else DEFAULT_AD_WORDS_THRESHOLD
        self.check_url: bool = bool(check_url)
        self.check_phone: bool = bool(check_phone)
        if custom_words:
            self.sensitive_words.update(custom_words)

    def apply_config(
        self,
        sensitive_words: list[str] | None = None,
        ad_words: list[str] | None = None,
        ad_threshold: int | None = None,
        check_url: bool | None = None,
        check_phone: bool | None = None,
    ) -> None:
        if sensitive_words is not None:
            self.sensitive_words = {str(w).strip()
                                    for w in sensitive_words if str(w).strip()}
        if ad_words is not None:
            self.ad_words = {str(w).strip()
                             for w in ad_words if str(w).strip()}
        if ad_threshold is not None:
            v = int(ad_threshold)
            self.ad_threshold = v if v > 0 else DEFAULT_AD_WORDS_THRESHOLD
        if check_url is not None:
            self.check_url = bool(check_url)
        if check_phone is not None:
            self.check_phone = bool(check_phone)

    def check_content(self, content: str) -> tuple[bool, str, list[str]]:
        if not content:
            return True, "", []

        content_lower = content.lower()
        matched_sensitive: list[str] = []
        matched_ads: list[str] = []

        for word in self.sensitive_words:
            if word.lower() in content_lower:
                matched_sensitive.append(word)

        for word in self.ad_words:
            if word.lower() in content_lower:
                matched_ads.append(word)

        if matched_sensitive:
            return False, "内容包含敏感词汇", matched_sensitive

        if len(matched_ads) >= int(self.ad_threshold):
            return False, "内容疑似广告", matched_ads

        return True, "", []

    def filter_content(self, content: str, replacement: str = "***") -> str:
        if not content:
            return content

        result = content
        all_words = list(self.sensitive_words) + list(self.ad_words)

        for word in all_words:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            result = pattern.sub(replacement, result)

        return result

    def get_risk_level(self, content: str) -> str:
        passed, _, matched = self.check_content(content)

        if passed:
            return 'safe'

        if len(matched) >= 3:
            return 'danger'

        return 'warning'


_default_filter = ContentFilter()
content_filter = _default_filter


def apply_content_filter_config(
    sensitive_words: list[str] | None = None,
    ad_words: list[str] | None = None,
    ad_words_threshold: int | None = None,
    check_url: bool | None = None,
    check_phone: bool | None = None,
) -> None:
    content_filter.apply_config(
        sensitive_words=sensitive_words,
        ad_words=ad_words,
        ad_threshold=ad_words_threshold,
        check_url=check_url,
        check_phone=check_phone,
    )


def check_post_content(title: str, content: str) -> tuple[bool, str]:
    passed, reason, _ = content_filter.check_content(title)
    if not passed:
        if reason == "内容疑似广告":
            return True, ""
        return False, f"标题{reason}"

    passed, reason, _ = content_filter.check_content(content)
    if not passed:
        if reason == "内容疑似广告":
            return True, ""
        return False, f"内容{reason}"

    return True, ""


def check_comment_content(content: str) -> tuple[bool, str]:
    passed, reason, _ = content_filter.check_content(content)
    if not passed:
        if reason == "内容包含敏感词汇":
            return False, reason
        return True, ""

    return True, ""


def needs_review(content: str) -> tuple[bool, str]:
    passed, reason, _ = content_filter.check_content(content)
    if not passed:
        return True, reason

    risk_level = content_filter.get_risk_level(content)

    if risk_level == 'danger':
        return True, "内容风险较高，需要人工审核"

    if content_filter.check_url:
        url_pattern = r'https?://[^\s]+'
        if re.search(url_pattern, content):
            return True, "内容包含链接，需要人工审核"

    if content_filter.check_phone:
        phone_pattern = r'1[3-9]\d{9}'
        if re.search(phone_pattern, content):
            return True, "内容包含联系方式，需要人工审核"

    return False, ""


def add_sensitive_word(word: str):
    content_filter.sensitive_words.add(word)


def remove_sensitive_word(word: str):
    content_filter.sensitive_words.discard(word)


def get_all_sensitive_words() -> list[str]:
    return list(content_filter.sensitive_words)


def add_ad_word(word: str):
    content_filter.ad_words.add(word)


def remove_ad_word(word: str):
    content_filter.ad_words.discard(word)


def get_all_ad_words() -> list[str]:
    return list(content_filter.ad_words)
