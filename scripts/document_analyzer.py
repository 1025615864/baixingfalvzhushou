#!/usr/bin/env python3
"""
文档分析器 - 分析文档的时效性、重复性和相似性
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import re
import argparse


class DocumentAnalyzer:
    """文档分析器类"""
    
    def __init__(self, manifest_file: str = ".cospec/document_cleanup/document_manifest.json"):
        self.manifest_file = Path(manifest_file)
        self.documents = []
        self.outdated_documents = []
        self.duplicate_groups = []
        self.similar_documents = []
        self.load_manifest()
    
    def load_manifest(self):
        """加载文档清单"""
        with open(self.manifest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.documents = data['documents']
        print(f"已加载 {len(self.documents)} 个文档的元数据")
    
    def identify_outdated(self, days_threshold: int = 30) -> List[Dict]:
        """识别过时文档"""
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        outdated = []
        
        for doc in self.documents:
            modified_time = datetime.fromisoformat(doc['modified_time'])
            
            # 检查修改时间
            if modified_time < cutoff_date:
                outdated.append({
                    'path': doc['path'],
                    'reason': f'最后修改时间超过 {days_threshold} 天',
                    'last_modified': doc['modified_time'],
                    'days_old': (datetime.now() - modified_time).days,
                    'file_type': doc.get('file_type', ''),
                    'title': doc.get('title', '')
                })
        
        outdated.sort(key=lambda x: x['days_old'], reverse=True)
        self.outdated_documents = outdated
        
        print(f"识别出 {len(outdated)} 个过时文档")
        return outdated
    
    def detect_duplicates(self) -> List[List[Dict]]:
        """检测重复文档"""
        hash_groups = defaultdict(list)
        
        # 按内容哈希分组
        for doc in self.documents:
            content_hash = doc.get('content_hash', '')
            if content_hash:
                hash_groups[content_hash].append(doc)
        
        # 找出重复的组
        duplicate_groups = []
        for content_hash, group in hash_groups.items():
            if len(group) > 1:
                duplicate_groups.append({
                    'hash': content_hash,
                    'count': len(group),
                    'files': [{
                        'path': doc['path'],
                        'size': doc['size'],
                        'modified_time': doc['modified_time']
                    } for doc in group],
                    'file_type': group[0].get('file_type', '')
                })
        
        duplicate_groups.sort(key=lambda x: x['count'], reverse=True)
        self.duplicate_groups = duplicate_groups
        
        print(f"检测出 {len(duplicate_groups)} 组重复文档")
        return duplicate_groups
    
    def extract_similarity_keywords(self, text: str) -> Set[str]:
        """提取相似度关键词"""
        if not text:
            return set()
        
        # 移除Markdown标记
        text = re.sub(r'#+\s*', '', text)  # 移除标题标记
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # 移除代码块
        text = re.sub(r'`[^`]+`', '', text)  # 移除行内代码
        text = re.sub(r'\*\*?\*?([^*]+)\*?\*?', r'\1', text)  # 移除粗体/斜体标记
        
        # 提取中文和英文单词
        # 匹配中文字符或英文单词
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
        
        # 过滤常见停用词
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'ought',
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
            '没有', '看', '好', '自己', '这'
        }
        
        return set(words) - stop_words
    
    def calculate_jaccard_similarity(self, set1: Set, set2: Set) -> float:
        """计算Jaccard相似度"""
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    def analyze_similarity(self, threshold: float = 0.8) -> List[Dict]:
        """分析文档相似度"""
        similar_pairs = []
        
        print("开始分析文档相似度...")
        
        # 读取文档内容
        doc_contents = {}
        for doc in self.documents:
            try:
                filepath = Path(doc['full_path'])
                if filepath.exists() and filepath.suffix == '.md':
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 只读取前5000个字符进行相似度分析（性能考虑）
                        keywords = self.extract_similarity_keywords(content[:5000])
                        doc_contents[doc['path']] = keywords
            except Exception as e:
                print(f"无法读取 {doc['path']}: {e}")
        
        # 计算相似度矩阵
        paths = list(doc_contents.keys())
        total_pairs = len(paths) * (len(paths) - 1) // 2
        checked = 0
        
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                path1 = paths[i]
                path2 = paths[j]
                
                keywords1 = doc_contents[path1]
                keywords2 = doc_contents[path2]
                
                if keywords1 and keywords2:
                    similarity = self.calculate_jaccard_similarity(keywords1, keywords2)
                    
                    if similarity >= threshold:
                        similar_pairs.append({
                            'paths': [path1, path2],
                            'similarity': round(similarity, 3),
                            'reason': '关键词集合高度相似'
                        })
                
                checked += 1
                if checked % 100 == 0:
                    print(f"已检查 {checked}/{total_pairs} 对文档...")
        
        similar_pairs.sort(key=lambda x: x['similarity'], reverse=True)
        self.similar_documents = similar_pairs
        
        print(f"识别出 {len(similar_pairs)} 对相似文档")
        return similar_pairs
    
    def generate_report(self, output_file: str = ".cospec/document_cleanup/analysis_report.json"):
        """生成分析报告"""
        report = {
            'analysis_time': datetime.now().isoformat(),
            'summary': {
                'total_documents': len(self.documents),
                'outdated_count': len(self.outdated_documents),
                'duplicate_groups': len(self.duplicate_groups),
                'duplicate_files': sum(g['count'] for g in self.duplicate_groups),
                'similar_pairs': len(self.similar_documents)
            },
            'outdated_documents': self.outdated_documents,
            'duplicate_groups': self.duplicate_groups,
            'similar_documents': self.similar_documents
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"分析报告已保存到: {output_path}")
        return report
    
    def print_summary(self):
        """打印分析摘要"""
        print("\n" + "="*60)
        print("文档分析摘要")
        print("="*60)
        print(f"总文档数: {len(self.documents)}")
        print(f"过时文档数: {len(self.outdated_documents)}")
        print(f"重复文档组数: {len(self.duplicate_groups)}")
        print(f"重复文档总数: {sum(g['count'] for g in self.duplicate_groups)}")
        print(f"相似文档对数: {len(self.similar_documents)}")
        
        # 显示前5个过时文档
        if self.outdated_documents:
            print("\n最旧的5个文档:")
            for i, doc in enumerate(self.outdated_documents[:5], 1):
                print(f"  {i}. {doc['path']} ({doc['days_old']}天前)")
        
        # 显示前5组重复文档
        if self.duplicate_groups:
            print("\n重复文档最多的5组:")
            for i, group in enumerate(self.duplicate_groups[:5], 1):
                print(f"  {i}. 哈希: {group['hash'][:12]}...")
                print(f"     重复数: {group['count']} 个文件")
                for file in group['files'][:2]:  # 只显示前2个
                    print(f"       - {file['path']}")
        
        # 显示前5对相似文档
        if self.similar_documents:
            print("\n相似度最高的5对文档:")
            for i, pair in enumerate(self.similar_documents[:5], 1):
                print(f"  {i}. 相似度: {pair['similarity']}")
                print(f"     - {pair['paths'][0]}")
                print(f"     - {pair['paths'][1]}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='文档分析器 - 分析文档的时效性、重复性和相似性')
    parser.add_argument('--manifest', '-m', 
                       default='.cospec/document_cleanup/document_manifest.json',
                       help='文档清单文件路径')
    parser.add_argument('--outdated-days', '-o', type=int, default=30,
                       help='过时文档的时间阈值（天） (默认: 30)')
    parser.add_argument('--similarity-threshold', '-s', type=float, default=0.8,
                       help='相似度阈值 (默认: 0.8)')
    parser.add_argument('--output', '-r', 
                       default='.cospec/document_cleanup/analysis_report.json',
                       help='分析报告输出文件路径')
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = DocumentAnalyzer(args.manifest)
    
    # 执行分析
    print("\n步骤 1: 识别过时文档...")
    analyzer.identify_outdated(args.outdated_days)
    
    print("\n步骤 2: 检测重复文档...")
    analyzer.detect_duplicates()
    
    print("\n步骤 3: 分析文档相似度...")
    analyzer.analyze_similarity(args.similarity_threshold)
    
    # 打印摘要
    analyzer.print_summary()
    
    # 生成报告
    analyzer.generate_report(args.output)


if __name__ == "__main__":
    main()