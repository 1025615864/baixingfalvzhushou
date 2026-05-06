"""敏感词过滤器"""
import re
from typing import List, Set, Tuple


SENSITIVE_WORDS: Set[str] = {
    "枪支", "毒品", "赌博", "诈骗", "传销", "色情", "暴力",
    "政治", "领导人", "敏感", "分裂", "恐怖", "贪污", "贿赂",
    "色情", "赌博", "毒品", "枪支", "管制刀具", "邪教",
}


class SensitiveWordFilter:
    def __init__(self, custom_words: Set[str] = None):
        self.words = SENSITIVE_WORDS.copy()
        if custom_words:
            self.words.update(custom_words)
        self.pattern = re.compile("|".join(re.escape(w) for w in self.words))

    def check(self, content: str) -> Tuple[bool, List[str]]:
        matches = self.pattern.findall(content)
        if matches:
            return True, list(set(matches))
        return False, []

    def filter(self, content: str, replace_char: str = "*") -> str:
        return self.pattern.sub(replace_char * 2, content)


sensitive_filter = SensitiveWordFilter()
