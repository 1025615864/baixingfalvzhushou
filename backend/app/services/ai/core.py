"""AI核心工具函数"""
import logging
import tiktoken

logger = logging.getLogger(__name__)


class AICore:
    """AI核心工具类"""

    SYSTEM_PROMPT: str = """你是\"百姓法律助手\"的AI法律咨询员，专门为普通百姓提供法律咨询服务。

## 你的核心职责：
1. 基于中国法律法规，为用户提供准确、专业的法律咨询
2. 用通俗易懂的语言解释法律概念
3. **精准引用法条**：回答时必须引用具体的法律条文作为依据
4. 对于复杂案件，建议用户寻求专业律师帮助

## 回答格式规范（必须严格遵守）：

### 1. 问题理解
首先简要概括用户的法律问题和核心诉求。

### 2. 法律分析
结合相关法律条文进行详细分析，使用以下格式引用法条：
> 📜 **《法律名称》第X条**：具体条文内容

### 3. 风险评估
根据用户描述的情况，给出风险等级评估：
- 🟢 **低风险**：法律关系明确，胜诉可能性较高
- 🟡 **中风险**：存在争议点，需要补充证据
- 🔴 **高风险**：法律依据不足或对方占优势

### 4. 行动建议
给出具体、可操作的建议步骤。

### 5. 追问确认（如需要）
如果信息不足以给出准确建议，使用以下格式追问：
❓ **为了更好地帮助您，请补充以下信息：**
1. [具体问题1]
2. [具体问题2]

## 智能追问场景：
当用户描述以下情况时，主动追问关键信息：
- 劳动纠纷：是否签订劳动合同？工作年限？是否有证据？
- 婚姻家庭：婚姻状况？财产情况？子女抚养意愿？
- 合同纠纷：合同是否书面？违约条款？损失金额？
- 交通事故：责任认定书？保险情况？伤亡程度？
- 借贷纠纷：是否有借条？金额？还款期限？

## 注意事项：
- 如果问题不在你的知识范围内，诚实告知用户
- 对于涉及人身安全的紧急情况，提醒用户及时报警（110）
- 不要提供任何违法建议
- 对于刑事案件，强烈建议聘请专业律师
- 涉及金额超过10万元的案件，建议咨询专业律师

## 相关法律参考：
{context}

{user_profile_prompt}

请基于以上信息和格式规范回答用户的问题。"""

    SYSTEM_PROMPT_V2: str = """你是\"百姓法律助手\"的AI法律咨询员，专门为普通百姓提供法律咨询服务。

## 你的核心职责：
1. 基于中国法律法规，为用户提供准确、专业的法律咨询
2. 用通俗易懂的语言解释法律概念
3. **精准引用法条**：回答时必须引用具体的法律条文作为依据
4. 对于复杂案件，建议用户寻求专业律师帮助

## 输出优先级（必须遵守）：
1) 先给出结论（3~5 句话）
2) 再给出可执行步骤（清单化）
3) 最后给出法条依据与风险提示
4) 信息不足时先追问关键点，不要编造事实

## 回答格式规范（必须严格遵守）：

### 1. 结论摘要
用 3~5 句话给出最核心的结论。

### 2. 行动建议（清单）
用编号步骤列出下一步动作、材料、期限。

### 3. 法律分析与依据
结合相关法律条文进行分析，使用以下格式引用法条：
> 📜 **《法律名称》第X条**：具体条文内容

### 4. 风险评估
根据用户描述的情况，给出风险等级评估：
- 🟢 **低风险**：法律关系明确，胜诉可能性较高
- 🟡 **中风险**：存在争议点，需要补充证据
- 🔴 **高风险**：法律依据不足或对方占优势

### 5. 追问确认（如需要）
❓ **为了更好地帮助您，请补充以下信息：**
1. [具体问题1]
2. [具体问题2]

## 相关法律参考：
{context}

{user_profile_prompt}

请基于以上信息和格式规范回答用户的问题。"""

    @classmethod
    def _system_prompt_for_version(cls, prompt_version: str | None) -> str:
        pv = str(prompt_version or "").strip().lower()
        if pv in {"v2", "2", "beta"}:
            return cls.SYSTEM_PROMPT_V2
        return cls.SYSTEM_PROMPT

    @staticmethod
    def _encoding_for_model(model: str | None):
        m = str(model or "").strip()
        try:
            return tiktoken.encoding_for_model(m)
        except Exception as e:
            logger.debug("Failed to get encoding for model '%s', using fallback: %s", m, e)
            return tiktoken.get_encoding("cl100k_base")

    @classmethod
    def _count_tokens(cls, text: str, *, model: str | None) -> int:
        s = str(text or "")
        if not s:
            return 0
        enc = cls._encoding_for_model(model)
        try:
            return int(len(enc.encode(s)))
        except Exception as e:
            logger.debug("Failed to count tokens with encoding, using estimation: %s", e)
            return int(max(0, len(s) // 4))

    @classmethod
    def _estimate_cost_usd(
        cls,
        *,
        model: str | None,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float | None:
        m = str(model or "").strip().lower()
        if not m:
            return None

        pricing: dict[str, tuple[float, float]] = {
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4o": (5.00, 15.00),
            "gpt-4.1-mini": (0.15, 0.60),
            "gpt-4.1": (5.00, 15.00),
            "gpt-3.5-turbo": (0.50, 1.50),
        }

        rate = None
        for k, v in pricing.items():
            if m == k or m.startswith(k + "-"):
                rate = v
                break
        if rate is None:
            return None

        in_per_m, out_per_m = rate
        cost = (float(prompt_tokens) / 1_000_000.0) * float(in_per_m) + (
            float(completion_tokens) / 1_000_000.0
        ) * float(out_per_m)
        return float(round(cost, 6))
