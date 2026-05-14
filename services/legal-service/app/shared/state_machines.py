"""状态机基类"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import TypeVar, Generic, Optional, Set, Dict, List

T = TypeVar('T')


class TransitionError(Exception):
    """状态转换错误"""

    def __init__(self, current_state: str, target_state: str, message: Optional[str] = None):
        self.current_state = current_state
        self.target_state = target_state
        self.message = message or f"不允许从 [{current_state}] 转换到 [{target_state}]"
        super().__init__(self.message)


class StateMachine(ABC, Generic[T]):
    """状态机基类"""

    @property
    @abstractmethod
    def transitions(self) -> Dict[T, Set[T]]:
        """定义合法的状态转换映射"""
        pass

    @property
    @abstractmethod
    def terminal_states(self) -> Set[T]:
        """定义终态（不可转换的状态）"""
        pass

    def can_transition(self, current: T, target: T) -> bool:
        """检查是否可以从 current 转换到 target"""
        if current == target:
            return True
        allowed = self.transitions.get(current, set())
        return target in allowed

    def validate_transition(self, current: T, target: T) -> None:
        """验证状态转换，如果不合法则抛出 TransitionError"""
        current_val = current.value if hasattr(current, 'value') else str(current)
        target_val = target.value if hasattr(target, 'value') else str(target)

        if target in self.terminal_states:
            raise TransitionError(
                current_state=current_val,
                target_state=target_val,
                message=f"[{target_val}] 是终态，不可转换"
            )

        if not self.can_transition(current, target):
            raise TransitionError(
                current_state=current_val,
                target_state=target_val,
            )

    def get_allowed_transitions(self, current: T) -> Set[T]:
        """获取当前状态允许的所有转换"""
        return self.transitions.get(current, set())


class TimestampedStateMachine(StateMachine[T]):
    """带时间戳的状态机"""

    def __init__(self):
        super().__init__()
        self._transition_history: List[dict] = []

    def transition(
        self,
        current: T,
        target: T,
        operator_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """执行状态转换并记录历史"""
        self.validate_transition(current, target)

        self._transition_history.append({
            "from": current.value if hasattr(current, 'value') else current,
            "to": target.value if hasattr(target, 'value') else target,
            "operator_id": operator_id,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc),
        })

    def get_transition_history(self) -> List[dict]:
        """获取转换历史"""
        return self._transition_history.copy()