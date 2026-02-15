/**
 * AI Content Assistant Component
 * AI 辅助内容生成、摘要、关键词提取
 */

import { memo } from 'react';
import { Card, Spin, Tabs } from 'antd';

import { useAISummary, useAIAnalysis, useAITags } from '../hooks';

interface AIContentAssistantProps {
  articleId?: string;
}

export const AIContentAssistant = memo(function AIContentAssistant({
  articleId,
}: AIContentAssistantProps) {
  const { data: summary, isLoading: summaryLoading } = useAISummary(articleId || '');
  const { data: analysis, isLoading: analysisLoading } = useAIAnalysis(articleId || '');
  const { data: tags, isLoading: tagsLoading } = useAITags(articleId || '');

  return (
    <Card title="AI 辅助" className="ai-content-assistant">
      <Tabs
        activeKey="summary"
        onChange={() => {}}
        items={[
          {
            key: 'summary',
            label: '摘要',
            children: summaryLoading ? (
              <Spin tip="生成摘要中..." />
            ) : summary?.summary ? (
              <div className="result-content">
                <p>{summary.summary}</p>
                <div className="meta-info text-sm text-gray-500 mt-2">
                  <span>质量评分: {summary.qualityScore || 'N/A'}</span>
                  {summary.generatedAt && (
                    <span className="ml-4">生成时间: {new Date(summary.generatedAt).toLocaleString()}</span>
                  )}
                </div>
              </div>
            ) : (
              <div className="empty-state text-center text-gray-500 py-4">暂无摘要数据</div>
            ),
          },
          {
            key: 'keywords',
            label: '关键词',
            children: tagsLoading ? (
              <Spin tip="提取关键词中..." />
            ) : tags?.keywords && tags.keywords.length > 0 ? (
              <div className="keywords-list">
                <div className="flex flex-wrap gap-2 mb-4">
                  {tags.keywords.map((keyword: string, index: number) => (
                    <span key={`${keyword}-${index}`} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <div className="empty-state text-center text-gray-500 py-4">暂无关键词数据</div>
            ),
          },
          {
            key: 'analysis',
            label: '分析',
            children: analysisLoading ? (
              <Spin tip="分析内容中..." />
            ) : analysis ? (
              <div className="analysis-content">
                <div className="risk-level mb-4">
                  <span className="font-medium">风险等级: </span>
                  <span className={`badge badge-${
                    analysis.riskLevel === 'high' ? 'red' :
                    analysis.riskLevel === 'medium' ? 'orange' : 'green'
                  }`}>
                    {analysis.riskLevel || '未知'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="empty-state text-center text-gray-500 py-4">暂无分析数据</div>
            ),
          },
        ]}
      />
    </Card>
  );
});
