/**
 * News Editor Component
 * 新闻编辑器组件，支持 Markdown 和富文本，自动保存草稿
 */

import { useCallback, useEffect, useRef, useState, memo } from 'react';
import { Button, Input, Select, Upload, message } from 'antd';
import { FileText, Sparkles } from 'lucide-react';

import { useArticle, useUpdateArticle, usePublishArticle, useCategories, useTags, useUploadImage } from '../hooks';
import type { ArticleEditor } from '../types';

const { TextArea } = Input;

interface NewsEditorProps {
  articleId?: string;
  onSave?: (data: Partial<ArticleEditor>) => void;
  onPreview?: () => void;
}

export const NewsEditor = memo(function NewsEditor({ articleId, onSave, onPreview }: NewsEditorProps) {
  const autoSaveTimerRef = useRef<number | null>(null);
  const [isAutoSaving, setIsAutoSaving] = useState(false);

  const { data: article, isLoading: articleLoading } = useArticle(articleId || '');
  const { data: categories } = useCategories();
  const { data: tagsData } = useTags();

  const updateArticleMutation = useUpdateArticle();
  const publishArticleMutation = usePublishArticle();
  const uploadImageMutation = useUploadImage();

  const [title, setTitle] = useState(() => article?.title ?? '');
  const [content, setContent] = useState(() => article?.content ?? '');
  const [excerpt, setExcerpt] = useState(() => article?.excerpt ?? '');
  const [categoryId, setCategoryId] = useState<string | undefined>(() => article?.categoryId);
  const [selectedTags, setSelectedTags] = useState<string[]>(() => article?.tags?.slice(0, 10) ?? []);
  const [seoTitle, setSeoTitle] = useState(() => article?.seoTitle ?? '');
  const [seoDescription, setSeoDescription] = useState(() => article?.seoDescription ?? '');
  const [coverImage, setCoverImage] = useState<string>(() => article?.coverImage ?? '');

  useEffect(() => {
    if (article) {
      setTitle(article.title);
      setContent(article.content);
      setExcerpt(article.excerpt || '');
      setCategoryId(article.categoryId);
      setSelectedTags(article.tags.slice(0, 10));
      setSeoTitle(article.seoTitle || '');
      setSeoDescription(article.seoDescription || '');
      setCoverImage(article.coverImage || '');
    }
  }, [article]);

  const handleAutoSave = useCallback(() => {
    setIsAutoSaving(true);
    if (onSave) {
      onSave({
        title,
        content,
        excerpt: excerpt || undefined,
        categoryId,
        tags: selectedTags,
        seoTitle,
        seoDescription,
      });
    }
    setTimeout(() => setIsAutoSaving(false), 1000);
  }, [title, content, excerpt, categoryId, selectedTags, seoTitle, seoDescription, onSave]);

  useEffect(() => {
    if (title || content) {
      if (autoSaveTimerRef.current) {
        window.clearTimeout(autoSaveTimerRef.current);
      }
      autoSaveTimerRef.current = window.setTimeout(() => {
        handleAutoSave();
      }, 5000);
    }
    return () => {
      if (autoSaveTimerRef.current) {
        window.clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [content, handleAutoSave, title]);

  const handleSave = useCallback(() => {
    if (!title.trim()) {
      void message.warning('请输入标题');
      return;
    }
    if (!content.trim()) {
      void message.warning('请输入内容');
      return;
    }
    if (articleId) {
      void updateArticleMutation.mutate(
        {
          id: articleId,
          data: { title, content, excerpt, categoryId, tags: selectedTags, seoTitle, seoDescription },
        },
        {
          onSuccess: () => {
            void message.success('保存成功');
          },
        }
      );
    } else if (onSave) {
      onSave({ title, content, excerpt, categoryId, tags: selectedTags, seoTitle, seoDescription });
    }
  }, [title, content, excerpt, categoryId, selectedTags, seoTitle, seoDescription, articleId, updateArticleMutation, onSave]);

  const handlePublish = useCallback(() => {
    if (!articleId) {
      void message.warning('请先保存文章');
      return;
    }
    void publishArticleMutation.mutate(articleId, {
      onSuccess: () => {
        void message.success('发布成功');
      },
    });
  }, [articleId, publishArticleMutation]);

  const handleImageUpload = useCallback((file: File) => {
    void uploadImageMutation.mutate(file, {
      onSuccess: (result) => {
        setCoverImage(result.url);
        void message.success('图片上传成功');
      },
      onError: () => {
        void message.error('图片上传失败');
      },
    });
  }, [uploadImageMutation]);

  if (articleLoading) {
    return <div className="p-8 text-center">加载中...</div>;
  }

  return (
    <div className="news-editor">
      <div className="editor-header mb-4 flex items-center justify-between">
        <h2 className="text-xl font-bold">{articleId ? '编辑文章' : '新建文章'}</h2>
        <div className="flex gap-2">
          <Button onClick={onPreview}>
            预览
          </Button>
          <Button icon={<FileText size={16} />} onClick={handleSave} loading={updateArticleMutation.isPending}>
            保存
          </Button>
          <Button type="primary" icon={<Sparkles size={16} />} onClick={handlePublish} loading={publishArticleMutation.isPending}>
            发布
          </Button>
        </div>
      </div>

      {isAutoSaving && <div className="text-sm text-gray-500 mb-2">自动保存中...</div>}

      <div className="editor-form space-y-4">
        <Input
          placeholder="文章标题"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          size="large"
          className="text-lg"
        />

        <div className="flex gap-4">
          <Select
            placeholder="选择分类"
            value={categoryId}
            onChange={setCategoryId}
            style={{ width: 200 }}
            allowClear
          >
            {categories?.map((cat) => (
              <Select.Option key={cat.id} value={cat.id}>
                {cat.name}
              </Select.Option>
            ))}
          </Select>

          <Select
            mode="tags"
            placeholder="添加标签"
            value={selectedTags}
            onChange={setSelectedTags}
            style={{ width: 300 }}
            maxTagCount={5}
          >
            {tagsData?.items.map((tag) => (
              <Select.Option key={tag.id} value={tag.name}>
                {tag.name}
              </Select.Option>
            ))}
          </Select>
        </div>

        <TextArea
          placeholder="文章摘要（可选）"
          value={excerpt}
          onChange={(e) => setExcerpt(e.target.value)}
          rows={2}
        />

        <div className="cover-image-section">
          <Upload beforeUpload={() => false} onChange={({ file }) => {
            if (file.originFileObj) {
              handleImageUpload(file.originFileObj);
            }
          }}>
            <Button icon={<FileText size={16} />}>上传封面图片</Button>
          </Upload>
          {coverImage && (
            <img src={coverImage} alt="封面" className="mt-2 max-w-md rounded" />
          )}
        </div>

        <TextArea
          placeholder="文章内容（支持 Markdown）"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={15}
          className="font-mono"
        />

        <div className="seo-section border-t pt-4 mt-4">
          <h3 className="text-lg font-medium mb-2">SEO 设置</h3>
          <Input
            placeholder="SEO 标题"
            value={seoTitle}
            onChange={(e) => setSeoTitle(e.target.value)}
            className="mb-2"
          />
          <TextArea
            placeholder="SEO 描述"
            value={seoDescription}
            onChange={(e) => setSeoDescription(e.target.value)}
            rows={2}
          />
        </div>
      </div>
    </div>
  );
});
