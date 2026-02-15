/**
 * 论坛点赞和收藏功能模块
 *
 * 提供论坛帖子的点赞、收藏和表情反应功能
 *
 * @example
 * ```tsx
 * import {
 *   ReactionBar,
 *   FavoriteButton,
 *   useForumReactions,
 *   useFavorites
 * } from '@/features/forum-reactions';
 *
 * function PostCard({ post }) {
 *   const { handleLike, handleFavorite } = useForumReactions();
 *
 *   return (
 *     <div>
 *       <h3>{post.title}</h3>
 *       <ReactionBar
 *         postId={post.id}
 *         likeCount={post.like_count}
 *         isLiked={post.is_liked}
 *         reactions={post.reactions}
 *         onLikeToggle={() => handleLike(post.id)}
 *         onReactionSelect={(emoji) => handleReaction(post.id, emoji)}
 *       />
 *       <FavoriteButton
 *         postId={post.id}
 *         isFavorited={post.is_favorited}
 *         favoriteCount={post.favorite_count}
 *         onToggle={() => handleFavorite(post.id)}
 *       />
 *     </div>
 *   );
 * }
 * ```
 */

// ============ 类型导出 ============

export type {
  // 反应相关
  ReactionEmoji,
  ReactionCount,
  ReactionRequest,
  ReactionResponse,
  // 点赞相关
  LikeResponse,
  // 收藏相关
  FavoriteResponse,
  FavoriteListParams,
  // 帖子相关
  AuthorInfo,
  Post,
  PostListResponse,
  // 组件Props
  ReactionBarProps,
  FavoriteButtonProps,
  PostReactionsProps,
  ReactionPickerProps,
  UserReactionState,
} from './types';

// ============ API导出 ============

export { forumReactionsApi, getPostDetail } from './api';

// ============ Hooks导出 ============

export {
  useToggleLike,
  useToggleFavorite,
  useToggleReaction,
  useFavorites,
  useForumReactions,
  forumReactionsKeys,
} from './hooks/useForumReactions';

// ============ 组件导出 ============

export { ReactionBar } from './components/ReactionBar';
export { FavoriteButton } from './components/FavoriteButton';
export { PostReactions } from './components/PostReactions';
export { ReactionPicker } from './components/ReactionPicker';

// ============ 默认导出 ============

export { forumReactionsApi as default } from './api';