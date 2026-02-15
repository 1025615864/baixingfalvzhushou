/**
 * Posts Manage Page
 * 帖子管理页面（管理员用）
 */

import { useState } from 'react';
import type { LucideIcon } from 'lucide-react';
import { Search, Trash2, Pin, Star, Eye, FileText } from 'lucide-react';

import { Card, Input, Button, Badge, Pagination } from '@/components/ui';

import {
  usePosts,
  useDeletePost,
  usePinPost,
  useFeaturePost,
} from '../hooks/usePosts';
import type { PostListItem, PostStatus } from '../types';

interface FilterItem {
  value: PostStatus | '';
  label: string;
  icon: LucideIcon;
}

const FILTER_ITEMS: FilterItem[] = [
  { value: 'published', label: '已发布', icon: FileText },
  { value: 'draft', label: '草稿', icon: FileText },
  { value: 'archived', label: '已归档', icon: FileText },
  { value: '', label: '全部', icon: FileText },
];

/**
 * 获取状态标签
 */
function getStatusBadge(status: PostStatus): { label: string; variant: 'success' | 'warning' | 'default' | 'danger' } {
  switch (status) {
    case 'published':
      return { label: '已发布', variant: 'success' };
    case 'draft':
      return { label: '草稿', variant: 'warning' };
    case 'archived':
      return { label: '已归档', variant: 'default' };
    case 'deleted':
      return { label: '已删除', variant: 'danger' };
    default:
      return { label: '未知', variant: 'default' };
  }
}

/**
 * 帖子管理页面
 */
export function PostsManagePage(): JSX.Element {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<PostStatus | ''>('published');
  const [keyword, setKeyword] = useState('');
  const [activeAction, setActiveAction] = useState<{ id: string; kind: 'pin' | 'feature' | 'delete' } | null>(null);

  // 数据查询
  const { data: postsData, isLoading } = usePosts({
    page,
    limit: pageSize,
    filter: {
      status: statusFilter || undefined,
      searchQuery: keyword || undefined,
    },
    sortBy: 'latest',
  });

  // Mutations
  const deleteMutation = useDeletePost();
  const pinMutation = usePinPost();
  const featureMutation = useFeaturePost();

  const posts = postsData?.posts ?? [];
  const totalPages = postsData?.totalPages ?? 0;

  // 处理删除
  const handleDelete = (id: string): void => {
    if (!window.confirm('确定要删除这个帖子吗？')) return;
    setActiveAction({ id, kind: 'delete' });
    deleteMutation.mutate(
      { id, permanent: false },
      { onSettled: () => setActiveAction(null) }
    );
  };

  // 处理置顶
  const handlePin = (post: PostListItem): void => {
    setActiveAction({ id: post.id, kind: 'pin' });
    pinMutation.mutate(
      { postId: post.id, isPinned: !post.isPinned },
      { onSettled: () => setActiveAction(null) }
    );
  };

  // 处理加精
  const handleFeature = (post: PostListItem): void => {
    setActiveAction({ id: post.id, kind: 'feature' });
    featureMutation.mutate(
      { postId: post.id, isFeatured: !post.isFeatured },
      { onSettled: () => setActiveAction(null) }
    );
  };

  return (
    <div className="container mx-auto py-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">帖子管理</h1>
          <p className="text-slate-600 mt-1">管理和维护社区帖子</p>
        </div>
      </div>

      {/* 筛选栏 */}
      <Card className="mb-6">
        <div className="p-4 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-slate-500" />
            <span className="text-sm text-slate-700">状态筛选：</span>
          </div>
          <div className="flex gap-2">
            {FILTER_ITEMS.map((item) => (
              <Button
                key={item.value}
                variant={statusFilter === item.value ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => {
                  setStatusFilter(item.value);
                  setPage(1);
                }}
              >
                {item.label}
              </Button>
            ))}
          </div>
          <div className="flex-1 min-w-[200px] ml-auto flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索帖子标题..."
                value={keyword}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  setKeyword(e.target.value);
                  setPage(1);
                }}
                className="pl-10"
              />
            </div>
          </div>
        </div>
      </Card>

      {/* 帖子列表 */}
      <Card>
        {isLoading ? (
          <div className="p-6 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-24 bg-slate-100 rounded animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            <div className="divide-y divide-slate-200">
              {posts.map((post) => {
                const status = getStatusBadge(post.status);
                return (
                  <div key={post.id} className="p-4 hover:bg-slate-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-medium text-slate-900 truncate">{post.title}</h3>
                          <Badge variant={status.variant} size="sm">
                            {status.label}
                          </Badge>
                          {post.isPinned && (
                            <Badge variant="primary" size="sm">置顶</Badge>
                          )}
                          {post.isFeatured && (
                            <Badge variant="warning" size="sm">精华</Badge>
                          )}
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-500">
                          <div>
                            <span className="text-slate-400">作者：</span>
                            {post.author.name}
                          </div>
                          <div>
                            <span className="text-slate-400">分类：</span>
                            {post.category}
                          </div>
                          <div>
                            <span className="text-slate-400">浏览：</span>
                            {post.viewCount}
                          </div>
                          <div>
                            <span className="text-slate-400">点赞：</span>
                            {post.likeCount}
                          </div>
                        </div>
                        <div className="mt-2 text-sm text-slate-500">
                          <span className="text-slate-400">发布时间：</span>
                          {post.publishedAt
                            ? new Date(post.publishedAt).toLocaleString('zh-CN')
                            : new Date(post.createdAt).toLocaleString('zh-CN')}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(`/posts/${post.id}`, '_blank')}
                          title="查看"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handlePin(post)}
                          disabled={activeAction?.id === post.id && activeAction?.kind === 'pin'}
                          title={post.isPinned ? '取消置顶' : '置顶'}
                        >
                          {activeAction?.id === post.id && activeAction?.kind === 'pin' ? (
                            <span className="animate-spin">⏳</span>
                          ) : (
                            <Pin className={`h-4 w-4 ${post.isPinned ? 'text-blue-500' : 'text-slate-400'}`} />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleFeature(post)}
                          disabled={activeAction?.id === post.id && activeAction?.kind === 'feature'}
                          title={post.isFeatured ? '取消加精' : '加精'}
                        >
                          {activeAction?.id === post.id && activeAction?.kind === 'feature' ? (
                            <span className="animate-spin">⏳</span>
                          ) : (
                            <Star className={`h-4 w-4 ${post.isFeatured ? 'text-yellow-500' : 'text-slate-400'}`} />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(post.id)}
                          disabled={activeAction?.id === post.id && activeAction?.kind === 'delete'}
                          title="删除"
                        >
                          {activeAction?.id === post.id && activeAction?.kind === 'delete' ? (
                            <span className="animate-spin">⏳</span>
                          ) : (
                            <Trash2 className="h-4 w-4 text-red-500" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
              {!posts.length && (
                <div className="p-10 text-center text-slate-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                  <p>暂无帖子</p>
                  <p className="text-sm mt-1">当有帖子发布后会显示在这里</p>
                </div>
              )}
            </div>
            {totalPages > 1 && (
              <div className="p-4 border-t border-slate-200">
                <Pagination
                  currentPage={page}
                  totalPages={totalPages}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
