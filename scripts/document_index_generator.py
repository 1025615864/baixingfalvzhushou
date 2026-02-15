#!/usr/bin/env python3
"""
文档索引生成器 - 生成文档索引并更新核心文档信息
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class DocumentIndexGenerator:
    """文档索引生成器"""
    
    def __init__(self, manifest_file: str = ".cospec/document_cleanup/document_manifest_after_cleanup.json"):
        self.manifest_file = Path(manifest_file)
        self.documents = []
        self.load_manifest()
    
    def load_manifest(self):
        """加载文档清单"""
        if not self.manifest_file.exists():
            print(f"清单文件不存在: {self.manifest_file}")
            return
        
        with open(self.manifest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.documents = data['documents']
        
        print(f"已加载 {len(self.documents)} 个文档的清单")
    
    def generate_doc_index(self, output_file: str = "docs/INDEX.md") -> Dict:
        """生成文档索引"""
        
        # 按目录和类型分类
        categories = {
            '系统架构': [],
            '业务系统': [],
            '开发文档': [],
            '部署运营': [],
            '项目报告': [],
            '其他文档': []
        }
        
        docs_dir = Path('docs')
        root_docs = []
        
        for doc in self.documents:
            path = Path(doc['path'])
            
            # 按路径分类
            if path.parent == docs_dir:
                # docs/目录下的文档
                title = doc.get('title', path.stem)
                
                if 'ARCHITECTURE' in doc['filename']:
                    categories['系统架构'].append(doc)
                elif 'SYSTEM' in doc['filename'] and doc['filename'] not in ['USER_SYSTEM.md']:
                    categories['业务系统'].append(doc)
                elif 'USER_SYSTEM' in doc['filename']:
                    categories['业务系统'].append(doc)
                elif 'API' in doc['filename'] or 'DESIGN' in doc['filename'] or 'DATABASE' in doc['filename']:
                    categories['系统架构'].append(doc)
                elif 'PERFORMANCE' in doc['filename'] or 'SECURITY' in doc['filename']:
                    categories['开发文档'].append(doc)
                elif 'DOCKER' in doc['filename'] or 'MONITORING' in doc['filename']:
                    categories['部署运营'].append(doc)
                else:
                    categories['系统架构'].append(doc)
            elif path.parent.name == 'backend':
                categories['开发文档'].append(doc)
            elif path.parent.name == 'frontend':
                categories['开发文档'].append(doc)
            elif 'REPORT' in doc['filename'] or 'SUMMARY' in doc['filename'] or 'VERIFICATION' in doc['filename']:
                categories['项目报告'].append(doc)
            elif path.parent.name == '.cospec':
                # cospec下的文档
                pass
            else:
                root_docs.append(doc)
        
        # 为根目录文档创建分类
        if root_docs:
            categories['其他文档'].extend(root_docs)
        
        # 生成索引内容
        index_content = f"""# 文档索引

> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 文档总数: {len(self.documents)}
> 最后更新: {datetime.now().isoformat()}

本文档提供了项目中所有重要文档的导航索引。

## 快速导航

- [项目报告](#项目报告)
- [系统架构](#系统架构)
- [业务系统](#业务系统)
- [开发文档](#开发文档)
- [部署运营](#部署运营)
- [其他文档](#其他文档)

---

"""
        
        # 为每个分类生成内容
        for category_name, docs in categories.items():
            if not docs:
                continue
            
            sort_key = lambda x: x.get('title', x['path'])
            docs_sorted = sorted(docs, key=sort_key)
            
            index_content += f"## {category_name}\n\n"
            
            for doc in docs_sorted:
                title = doc.get('title', doc['filename'])
                path = doc['path']
                size_kb = doc['size'] / 1024
                modified_date = doc['modified_time'].split('T')[0]
                
                index_content += f"- **{title}** ([{path}]({path}))\n"
                index_content += f"  - 大小: {size_kb:.1f} KB | 最后修改: {modified_date}\n"
            
            index_content += "\n"
        
        index_content += f"""
---

## 文档统计

| 分类 | 文档数 |
|------|--------|
"""
        for category_name, docs in categories.items():
            if docs:
                index_content += f"| {category_name} | {len(docs)} |\n"
        
        # 保存索引
        index_path = Path(output_file)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"文档索引已生成: {index_path}")
        return categories
    
    def update_core_docs(self, categories: Dict):
        """更新核心文档信息"""
        
        print("\n更新核心文档元数据...")
        
        # 定义核心文档映射
        core_docs_mapping = {
            'README.md': {
                'purpose': '项目主README文档',
                'status': 'current',
                'version': 'latest'
            },
            'docs/BACKEND_ARCHITECTURE.md': {
                'purpose': '后端架构设计文档',
                'status': 'current',
                'version': 'v2.0'
            },
            'docs/API_DOCUMENTATION_INDEX.md': {
                'purpose': 'API文档导航',
                'status': 'current',
                'version': 'latest'
            },
            'DEVELOPMENT_ROADMAP.md': {
                'purpose': '开发路线图',
                'status': 'current',
                'version': 'v1.0'
            }
        }
        
        # 保存核心文档元数据
        metadata_content = {
            'generated_at': datetime.now().isoformat(),
            'core_documents': []
        }
        
        for doc_path, metadata in core_docs_mapping.items():
            # 查找对应文档
            found_doc = None
            for doc in self.documents:
                if doc['path'] == doc_path:
                    found_doc = doc
                    break
            
            if found_doc:
                doc_info = {
                    'path': doc_path,
                    'title': found_doc.get('title', ''),
                    'purpose': metadata['purpose'],
                    'status': metadata['status'],
                    'version': metadata['version'],
                    'size': found_doc['size'],
                    'last_modified': found_doc['modified_time'],
                    'content_hash': found_doc.get('content_hash', '')
                }
                metadata_content['core_documents'].append(doc_info)
                print(f"  更新: {doc_path}")
        
        # 保存元数据
        metadata_file = Path('.cospec/document_cleanup/core_documents_metadata.json')
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_content, f, ensure_ascii=False, indent=2)
        
        print(f"\n核心文档元数据已保存: {metadata_file}")
    
    def generate_structure_report(self, output_file: str = ".cospec/document_cleanup/structure_report.json"):
        """生成文档结构报告"""
        
        print("\n生成文档结构报告...")
        
        # 分析文档分布
        dir_distribution = {}
        type_distribution = {}
        
        for doc in self.documents:
            path = Path(doc['path'])
            parent_dir = str(path.parent)
            file_type = doc['file_type']
            
            dir_distribution[parent_dir] = dir_distribution.get(parent_dir, 0) + 1
            type_distribution[file_type] = type_distribution.get(file_type, 0) + 1
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_documents': len(self.documents),
            'directory_distribution': dir_distribution,
            'type_distribution': type_distribution,
            'recommendations': []
        }
        
        # 生成建议
        if len(dir_distribution) > 10:
            report['recommendations'].append({
                'type': 'ORGANIZATION',
                'priority': 'MEDIUM',
                'message': '文档目录过于分散，建议考虑合并相似目录'
            })
        
        if type_distribution.get('.md', 0) > 300:
            report['recommendations'].append({
                'type': 'MAINTENANCE',
                'priority': 'LOW',
                'message': 'Markdown文档数量较多，建议定期清理过时文档'
            })
        
        # 保存报告
        report_path = Path(output_file)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"文档结构报告已保存: {report_path}")
        return report


def main():
    """主函数"""
    generator = DocumentIndexGenerator()
    
    if not generator.documents:
        print("无法加载文档清单")
        return
    
    # 生成文档索引
    print("生成文档索引...")
    categories = generator.generate_doc_index()
    
    # 更新核心文档信息
    generator.update_core_docs(categories)
    
    # 生成结构报告
    generator.generate_structure_report()
    
    print("\n" + "="*60)
    print("文档索引和结构分析完成！")
    print("="*60)


if __name__ == "__main__":
    main()