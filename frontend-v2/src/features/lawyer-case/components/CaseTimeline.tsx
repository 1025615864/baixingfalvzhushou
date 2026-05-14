import { Clock, Plus } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import type { ProgressNode } from '../types';

interface CaseTimelineProps {
  nodes: ProgressNode[];
  onAddNode?: () => void;
}

export function CaseTimeline({ nodes, onAddNode }: CaseTimelineProps): JSX.Element {
  if (nodes.length === 0 && !onAddNode) {
    return (
      <div className="text-center py-8 text-gray-400">
        <Clock className="w-8 h-8 mx-auto mb-2" />
        <p className="text-sm">暂无进度记录</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-medium text-gray-700">案件进度</h4>
        {onAddNode && (
          <Button variant="outline" size="sm" onClick={onAddNode} leftIcon={<Plus className="w-3.5 h-3.5" />}>
            添加进度
          </Button>
        )}
      </div>

      <div className="relative pl-6 border-l-2 border-gray-200 space-y-6">
        {nodes.map((node, idx) => (
          <div key={idx} className="relative">
            <div className="absolute -left-[25px] w-3 h-3 rounded-full bg-primary-500 border-2 border-white ring-2 ring-primary-100" />
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-medium text-gray-900">{node.title}</p>
                <span className="text-xs text-gray-400">
                  {new Date(node.date).toLocaleDateString('zh-CN')}
                </span>
              </div>
              {node.description && (
                <p className="text-sm text-gray-600">{node.description}</p>
              )}
            </div>
          </div>
        ))}
        {nodes.length === 0 && onAddNode && (
          <div className="relative">
            <div className="absolute -left-[25px] w-3 h-3 rounded-full bg-gray-300 border-2 border-white" />
            <div className="text-center py-4 text-gray-400 text-sm">
              点击"添加进度"记录案件进展
            </div>
          </div>
        )}
      </div>
    </div>
  );
}