/**
 * Forum（论坛）模块 Query Keys
 * 用于 React Query 的缓存管理
 */

export const forumKeys = {
  // 所有论坛相关查询的根key
  all: ['forum'] as const,

  // 帖子相关
  posts: () => [...forumKeys.all, 'posts'] as const,
  postList: (filters: {
    category?: string | null;
    keyword?: string;
    is_essence?: boolean | null;
  }) => [...forumKeys.posts(), 'list', filters] as const,
  postDetail: (postId: number) => [...forumKeys.posts(), 'detail', postId] as const,
  hotPosts: (category?: string) => [...forumKeys.posts(), 'hot', category] as const,
  myPosts: (filters: { category?: string; keyword?: string }) =>
    [...forumKeys.posts(), 'my', filters] as const,
  myDeletedPosts: (filters: { category?: string; keyword?: string }) =>
    [...forumKeys.posts(), 'my-deleted', filters] as const,

  // 评论相关
  comments: () => [...forumKeys.all, 'comments'] as const,
  commentList: (postId: number, filters?: { include_unapproved?: boolean }) =>
    [...forumKeys.comments(), 'list', postId, filters] as const,
  myComments: (status?: 'all' | 'pending' | 'approved' | 'rejected') =>
    [...forumKeys.comments(), 'my', status] as const,

  // 收藏相关
  favorites: () => [...forumKeys.all, 'favorites'] as const,
  favoriteList: (filters: { category?: string | null; keyword?: string }) =>
    [...forumKeys.favorites(), 'list', filters] as const,

  // 表情反应相关
  reactions: () => [...forumKeys.all, 'reactions'] as const,
  postReactions: (postId: number) => [...forumKeys.reactions(), 'post', postId] as const,

  // 律师邀请相关
  invitations: () => [...forumKeys.all, 'invitations'] as const,
  invitationList: (status?: 'all' | 'pending' | 'accepted' | 'declined' | 'expired') =>
    [...forumKeys.invitations(), 'list', status] as const,

  // 律师相关
  lawyers: () => [...forumKeys.all, 'lawyers'] as const,
  lawyerList: (filters: { keyword?: string; specialty?: string }) =>
    [...forumKeys.lawyers(), 'list', filters] as const,
} as const;

// 导出默认对象便于使用
export default forumKeys;