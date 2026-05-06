"""热度评分算法 - Hacker News 变体"""
import math
from datetime import datetime, timezone


def calculate_hot_score(
    likes: int,
    comments: int,
    views: int,
    favorites: int = 0,
    is_lawyer_post: bool = False,
    created_at: datetime = None
) -> float:
    engagement = (
        likes * 1.0 +
        comments * 3.0 +
        favorites * 2.0 +
        math.log10(max(views, 1)) * 0.5
    )

    if is_lawyer_post:
        engagement *= 1.5

    if created_at:
        now = datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        hours_since_post = (now - created_at).total_seconds() / 3600
        time_decay = 1.0 / (1.0 + (hours_since_post / 12.0) ** 1.5)
    else:
        time_decay = 1.0

    return round(engagement * time_decay, 4)


def recalculate_post_hot_score(post) -> float:
    return calculate_hot_score(
        likes=post.like_count,
        comments=post.comment_count,
        views=post.view_count,
        favorites=post.favorite_count,
        is_lawyer_post=post.is_lawyer,
        created_at=post.created_at
    )
