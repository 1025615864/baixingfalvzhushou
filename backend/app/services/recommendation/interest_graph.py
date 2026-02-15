"""兴趣图谱服务

构建用户-内容兴趣关系图谱，支持基于图论的推荐算法。
"""

import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


@dataclass
class InterestNode:
    """兴趣节点"""
    node_id: str
    node_type: str  # user, content, tag, category
    attributes: Dict[str, Any] = field(default_factory=dict)
    neighbors: Set[str] = field(default_factory=set)


@dataclass
class InterestEdge:
    """兴趣边"""
    source: str
    target: str
    edge_type: str  # viewed, liked, searched, generated
    weight: float = 1.0
    timestamp: Optional[str] = None


class InterestGraph:
    """兴趣图谱

    用于构建和分析用户-内容-标签的关系网络，
    支持基于图论的推荐算法（如协同过滤、标签传播等）。
    """

    def __init__(self):
        self._nodes: Dict[str, InterestNode] = {}
        self._edges: List[InterestEdge] = []
        # user_id -> content_id -> weight
        self._user_content_matrix: Dict[int, Dict[str, float]] = {}
        # content_id -> tag -> weight
        self._content_tag_matrix: Dict[str, Dict[str, float]] = {}
        self._tag_user_matrix: Dict[str, Set[int]] = {}  # tag -> user_ids

    def add_user_node(self, user_id: int,
                      attributes: Optional[Dict] = None) -> None:
        """添加用户节点"""
        node_id = f"user_{user_id}"
        if node_id not in self._nodes:
            self._nodes[node_id] = InterestNode(
                node_id=node_id,
                node_type="user",
                attributes=attributes or {},
            )
            self._user_content_matrix[user_id] = {}

    def add_content_node(
        self,
        content_id: str,
        content_type: str,
        tags: List[str],
        attributes: Optional[Dict] = None,
    ) -> None:
        """添加内容节点"""
        node_id = f"content_{content_id}"
        if node_id not in self._nodes:
            self._nodes[node_id] = InterestNode(
                node_id=node_id,
                node_type=content_type,
                attributes=attributes or {},
            )
            self._content_tag_matrix[content_id] = {}

        # 更新内容-标签矩阵
        for tag in tags:
            if tag not in self._content_tag_matrix[content_id]:
                self._content_tag_matrix[content_id][tag] = 0.0

    def add_interaction(
        self,
        user_id: int,
        content_id: str,
        content_type: str,
        tags: List[str],
        interaction_type: str = "viewed",
        weight: float = 1.0,
    ) -> None:
        """添加用户-内容交互

        Args:
            user_id: 用户ID
            content_id: 内容ID
            content_type: 内容类型（news, forum_post, document 等）
            tags: 内容标签
            interaction_type: 交互类型
            weight: 交互权重
        """
        # 添加节点
        self.add_user_node(user_id)
        self.add_content_node(content_id, content_type, tags)

        # 添加边
        edge = InterestEdge(
            source=f"user_{user_id}",
            target=f"content_{content_id}",
            edge_type=interaction_type,
            weight=weight,
        )
        self._edges.append(edge)

        # 更新用户-内容矩阵
        if user_id not in self._user_content_matrix:
            self._user_content_matrix[user_id] = {}

        current_weight = self._user_content_matrix[user_id].get(content_id, 0)
        self._user_content_matrix[user_id][content_id] = current_weight + weight

        # 更新标签-用户矩阵
        for tag in tags:
            if tag not in self._tag_user_matrix:
                self._tag_user_matrix[tag] = set()
            self._tag_user_matrix[tag].add(user_id)

        # 更新节点邻居
        user_node = self._nodes.get(f"user_{user_id}")
        content_node = self._nodes.get(f"content_{content_id}")
        if user_node:
            user_node.neighbors.add(f"content_{content_id}")
        if content_node:
            content_node.neighbors.add(f"user_{user_id}")

    def get_user_similar_users(
            self, user_id: int, top_k: int = 10) -> List[tuple[int, float]]:
        """获取相似用户（基于内容交互的协同过滤）

        Returns:
            List of (user_id, similarity_score) sorted by similarity
        """
        if user_id not in self._user_content_matrix:
            return []

        user_contents = self._user_content_matrix[user_id]
        user_tags = set()
        for content_id, weight in user_contents.items():
            for tag in self._content_tag_matrix.get(content_id, {}):
                if self._content_tag_matrix[content_id].get(tag, 0) > 0:
                    user_tags.add(tag)

        similarities = []
        for other_id, other_contents in self._user_content_matrix.items():
            if other_id == user_id:
                continue

            # 计算 Jaccard 相似度
            other_tags = set()
            for content_id, weight in other_contents.items():
                for tag in self._content_tag_matrix.get(content_id, {}):
                    if self._content_tag_matrix[content_id].get(tag, 0) > 0:
                        other_tags.add(tag)

            if not user_tags or not other_tags:
                continue

            intersection = user_tags & other_tags
            union = user_tags | other_tags

            if union:
                similarity = len(intersection) / len(union)
                similarities.append((other_id, similarity))

        # 排序并返回 top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def get_content_similar_contents(
        self,
        content_id: str,
        top_k: int = 10,
    ) -> List[tuple[str, float]]:
        """获取相似内容（基于标签的余弦相似度）"""
        if content_id not in self._content_tag_matrix:
            return []

        content_tags = self._content_tag_matrix[content_id]

        similarities = []
        for other_id, other_tags in self._content_tag_matrix.items():
            if other_id == content_id:
                continue

            # 计算余弦相似度
            similarity = self._cosine_similarity(content_tags, other_tags)
            similarities.append((other_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _cosine_similarity(
        self,
        tags1: Dict[str, float],
        tags2: Dict[str, float],
    ) -> float:
        """计算余弦相似度"""
        if not tags1 or not tags2:
            return 0.0

        # 获取所有标签
        all_tags = set(tags1.keys()) | set(tags2.keys())
        if not all_tags:
            return 0.0

        # 计算点积
        dot_product = sum(tags1.get(tag, 0) * tags2.get(tag, 0)
                          for tag in all_tags)

        # 计算模长
        norm1 = math.sqrt(sum(v * v for v in tags1.values()))
        norm2 = math.sqrt(sum(v * v for v in tags2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def get_users_by_tag(self, tag: str) -> Set[int]:
        """获取拥有特定标签的用户"""
        return self._tag_user_matrix.get(tag, set())

    def get_tag_popularity(self) -> Dict[str, int]:
        """获取标签热度（用户数）"""
        return {tag: len(users)
                for tag, users in self._tag_user_matrix.items()}

    def get_user_preferred_tags(
        self,
        user_id: int,
        top_k: int = 10,
    ) -> List[tuple[str, float]]:
        """获取用户偏好的标签"""
        if user_id not in self._user_content_matrix:
            return []

        # 统计用户交互内容的标签
        tag_weights: Dict[str, float] = defaultdict(float)
        for content_id, weight in self._user_content_matrix[user_id].items():
            for tag, tag_weight in self._content_tag_matrix.get(
                    content_id, {}).items():
                tag_weights[tag] += weight * tag_weight

        # 排序
        sorted_tags = sorted(
            tag_weights.items(),
            key=lambda x: x[1],
            reverse=True)
        return sorted_tags[:top_k]

    def predict_user_preference(
        self,
        user_id: int,
        content_id: str,
    ) -> float:
        """预测用户对内容的偏好分数"""
        if user_id not in self._user_content_matrix:
            return 0.0

        # 如果用户已经交互过，返回历史权重
        if content_id in self._user_content_matrix[user_id]:
            return self._user_content_matrix[user_id][content_id]

        # 基于相似用户的加权平均
        similar_users = self.get_user_similar_users(user_id, top_k=20)
        if not similar_users:
            return 0.0

        content_tags = self._content_tag_matrix.get(content_id, {})
        if not content_tags:
            return 0.0

        # 计算加权分数
        numerator = 0.0
        denominator = 0.0

        for other_id, similarity in similar_users:
            # 获取相似用户对相同标签内容的交互权重
            other_score = 0.0
            for tag in content_tags:
                # 检查相似用户是否也关注这个标签
                other_users_with_tag = self._tag_user_matrix.get(tag, set())
                if other_id in other_users_with_tag:
                    other_tags = self._content_tag_matrix.get(content_id, {})
                    other_score += similarity * other_tags.get(tag, 0)

            numerator += similarity * other_score
            denominator += similarity

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def get_stats(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        return {
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
            "user_count": len(self._user_content_matrix),
            "content_count": len(self._content_tag_matrix),
            "tag_count": len(self._tag_user_matrix),
            "popular_tags": dict(
                sorted(
                    self.get_tag_popularity().items(),
                    key=lambda x: x[1],
                    reverse=True)[
                    :10]
            ),
        }


# 全局兴趣图谱实例
_interest_graph: Optional[InterestGraph] = None


def get_interest_graph() -> InterestGraph:
    """获取兴趣图谱单例"""
    global _interest_graph
    if _interest_graph is None:
        _interest_graph = InterestGraph()
    return _interest_graph


def record_user_interaction(
    user_id: int,
    content_id: str,
    content_type: str,
    tags: List[str],
    interaction_type: str = "viewed",
    weight: float = 1.0,
) -> None:
    """记录用户交互的便捷函数"""
    graph = get_interest_graph()
    graph.add_interaction(
        user_id=user_id,
        content_id=content_id,
        content_type=content_type,
        tags=tags,
        interaction_type=interaction_type,
        weight=weight,
    )
