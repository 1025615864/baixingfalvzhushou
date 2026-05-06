"""社区积分事件类型定义

社区服务发布的事件类型，供积分服务消费
"""

class CommunityPointEventTypes:
    POST_CREATED = "community.post.created"
    COMMENT_CREATED = "community.comment.created"
    POST_LIKED = "community.post.liked"
    COMMENT_LIKED = "community.comment.liked"
    BEST_ANSWER_SELECTED = "community.best_answer.selected"

    @classmethod
    def all(cls):
        return [
            cls.POST_CREATED,
            cls.COMMENT_CREATED,
            cls.POST_LIKED,
            cls.COMMENT_LIKED,
            cls.BEST_ANSWER_SELECTED,
        ]


COMMUNITY_POINTS_CONFIG = {
    CommunityPointEventTypes.POST_CREATED: {
        "points": 5,
        "description": "发帖奖励",
        "is_lawyer_multiplier": 1.5,
    },
    CommunityPointEventTypes.COMMENT_CREATED: {
        "points": 2,
        "description": "评论奖励",
        "is_lawyer_multiplier": 1.5,
    },
    CommunityPointEventTypes.POST_LIKED: {
        "points": 1,
        "description": "帖子被点赞奖励",
        "is_lawyer_multiplier": 1.5,
    },
    CommunityPointEventTypes.COMMENT_LIKED: {
        "points": 1,
        "description": "评论被点赞奖励",
        "is_lawyer_multiplier": 1.5,
    },
    CommunityPointEventTypes.BEST_ANSWER_SELECTED: {
        "points": 10,
        "description": "最佳回答奖励",
        "is_lawyer_multiplier": 2.0,
    },
}
