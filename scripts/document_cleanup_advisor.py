#!/usr/bin/env python3
"""
文档清理建议生成器 - 生成详细的文档整理建议
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class DocumentCleanupAdvisor:
    """文档清理建议生成器"""
    
    def __init__(self, analysis_file: str = ".cospec/document_cleanup/analysis_report.json"):
        self.analysis_file = Path(analysis_file)
        self.analysis = {}
        self.cleanup_plan = {
            'generated_at': datetime.now().isoformat(),
            'summary': {},
            'actions': []
        }
        self.load_analysis()
    
    def load_analysis(self):
        """加载分析报告"""
        with open(self.analysis_file, 'r', encoding='utf-8') as f:
            self.analysis = json.load(f)
        print(f"已加载分析报告: {self.analysis['summary']}")
    
    def generate_duplicate_advice(self):
        """生成重复文档的处理建议"""
        print("\n生成重复文档处理建议...")
        
        for group in self.analysis['duplicate_groups']:
            if group['count'] > 1:
                # 选择保留的文件（优先保留docs/目录下的，其他归档或删除）
                files = group['files']
                
                # 按修改时间排序，保留最新的
                files_sorted = sorted(files, key=lambda x: x['modified_time'], reverse=True)
                
                # 确定保留路径
                primary_file = files_sorted[0]
                
                # 检查是否是空文件
                if primary_file['size'] == 0:
                    action = {
                        'type': 'DELETE_EMPTY',
                        'reason': '空文件，无实际内容',
                        'files': [f['path'] for f in files],
                        'priority': 'HIGH'
                    }
                else:
                    # 检查是否在docs/目录下（优先保留）
                    docs_files = [f for f in files if f['path'].startswith('docs/')]
                    wiki_files = [f for f in files if f['path'].startswith('.cospec/wiki/')]
                    test_files = [f for f in files if 'test-results' in f['path'] or 'playwright-report' in f['path']]
                    
                    if docs_files and (wiki_files or test_files):
                        # 保留docs/下的，删除其他
                        keep = docs_files[0]['path']
                        delete = [f['path'] for f in files if f['path'] != keep]
                        action = {
                            'type': 'DELETE_DUPLICATE',
                            'keep': keep,
                            'reason': f'保留docs/目录下的文档，删除{wiki_files and ".cospec/wiki/" or "test-results/"}下的重复',
                            'delete': delete,
                            'priority': 'MEDIUM'
                        }
                    elif wiki_files and len(wiki_files) > 1:
                        # wiki目录下有重复
                        keep = wiki_files[0]['path']
                        delete = [f['path'] for f in wiki_files if f['path'] != keep]
                        action = {
                            'type': 'DELETE_DUPLICATE',
                            'keep': keep,
                            'reason': f'保留wiki目录下的最新版本',
                            'delete': delete,
                            'priority': 'LOW'
                        }
                    elif test_files:
                        # 测试报告重复，全部归档
                        action = {
                            'type': 'ARCHIVE',
                            'reason': '测试报告文件，归档到archive目录',
                            'files': [f['path'] for f in files],
                            'archive_to': 'archive/test_reports/',
                            'priority': 'LOW'
                        }
                    else:
                        # 其他情况，保留修改时间最新的
                        keep = files_sorted[0]['path']
                        delete = [f['path'] for f in files if f['path'] != keep]
                        action = {
                            'type': 'DELETE_DUPLICATE',
                            'keep': keep,
                            'reason': f'保留最新修改的版本',
                            'delete': delete,
                            'priority': 'MEDIUM'
                        }
                
                self.cleanup_plan['actions'].append(action)
    
    def generate_similarity_advice(self):
        """生成相似文档的处理建议"""
        print("\n生成相似文档处理建议...")
        
        # 按相似度分组
        high_similarity = []
        medium_similarity = []
        
        for pair in self.analysis['similar_documents']:
            if pair['similarity'] == 1.0:
                # 完全相同（应该已在重复文档检测中处理）
                continue
            elif pair['similarity'] >= 0.9:
                high_similarity.append(pair)
            elif pair['similarity'] >= 0.8:
                medium_similarity.append(pair)
        
        # 高相似度文档建议合并
        for pair in high_similarity[:10]:  # 最多处理前10对
            path1, path2 = pair['paths']
            
            # 检查是否是docs/和.cospec/wiki/的重复
            docs_file = None
            wiki_file = None
            
            for path in [path1, path2]:
                if path.startswith('docs/'):
                    docs_file = path
                elif path.startswith('.cospec/wiki/'):
                    wiki_file = path
            
            if docs_file and wiki_file:
                action = {
                    'type': 'DELETE_SIMILAR',
                    'keep': docs_file,
                    'delete': wiki_file,
                    'reason': f'docs/目录下的文档已存在，删除wiki下的相似文档（相似度: {pair["similarity"]}）',
                    'priority': 'LOW'
                }
                self.cleanup_plan['actions'].append(action)
            elif len(pair['paths']) == 2:
                action = {
                    'type': 'REVIEW_MANUAL',
                    'files': pair['paths'],
                    'reason': f'文档高度相似（相似度: {pair["similarity"]}），需要人工审核是否合并',
                    'priority': 'LOW'
                }
                self.cleanup_plan['actions'].append(action)
    
    def generate_cleanup_summary(self):
        """生成清理摘要"""
        actions = self.cleanup_plan['actions']
        
        summary = {
            'total_actions': len(actions),
            'by_type': {},
            'by_priority': {
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'estimated_savings': {
                'files_to_delete': 0,
                'files_to_archive': 0,
                'files_to_review': 0
            }
        }
        
        for action in actions:
            action_type = action['type']
            priority = action['priority']
            
            summary['by_type'][action_type] = summary['by_type'].get(action_type, 0) + 1
            summary['by_priority'][priority] += 1
            
            if action_type in ['DELETE_DUPLICATE', 'DELETE_EMPTY', 'DELETE_SIMILAR']:
                summary['estimated_savings']['files_to_delete'] += len(
                    action.get('delete', action.get('files', []))
                )
            elif action_type == 'ARCHIVE':
                summary['estimated_savings']['files_to_archive'] += len(action.get('files', []))
            elif action_type == 'REVIEW_MANUAL':
                summary['estimated_savings']['files_to_review'] += len(action.get('files', []))
        
        self.cleanup_plan['summary'] = summary
        return summary
    
    def generate_plan(self, output_file: str = ".cospec/document_cleanup/cleanup_plan.json"):
        """生成完整的清理计划"""
        print("开始生成清理计划...")
        
        # 生成各类建议
        self.generate_duplicate_advice()
        self.generate_similarity_advice()
        
        # 生成摘要
        self.generate_cleanup_summary()
        
        # 保存计划
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.cleanup_plan, f, ensure_ascii=False, indent=2)
        
        print(f"\n清理计划已保存到: {output_path}")
        
        # 打印摘要
        self.print_summary()
        
        return self.cleanup_plan
    
    def print_summary(self):
        """打印清理摘要"""
        summary = self.cleanup_plan['summary']
        
        print("\n" + "="*60)
        print("文档清理计划摘要")
        print("="*60)
        print(f"总操作数: {summary['total_actions']}")
        
        print("\n按操作类型统计:")
        for action_type, count in summary['by_type'].items():
            print(f"  {action_type}: {count}")
        
        print("\n按优先级统计:")
        for priority, count in summary['by_priority'].items():
            print(f"  {priority}: {count}")
        
        print("\n预计效果:")
        print(f"  需要删除的文件: {summary['estimated_savings']['files_to_delete']} 个")
        print(f"  需要归档的文件: {summary['estimated_savings']['files_to_archive']} 个")
        print(f"  需要人工审核: {summary['estimated_savings']['files_to_review']} 个")
        print(f"  总计可清理: {summary['estimated_savings']['files_to_delete'] + summary['estimated_savings']['files_to_archive']} 个文件")


def main():
    """主函数"""
    advisor = DocumentCleanupAdvisor()
    advisor.generate_plan()


if __name__ == "__main__":
    main()