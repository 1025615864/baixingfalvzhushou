#!/usr/bin/env python3
"""
文档扫描器 - 扫描项目中的所有文档并提取元数据
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse


class DocumentScanner:
    """文档扫描器类"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.documents: List[Dict] = []
    
    def calculate_file_hash(self, filepath: Path) -> str:
        """计算文件内容的SHA256哈希值"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"无法计算 {filepath} 的哈希值: {e}")
            return ""
    
    def extract_metadata(self, filepath: Path) -> Optional[Dict]:
        """提取文档元数据"""
        try:
            stat = filepath.stat()
            
            metadata = {
                "path": str(filepath.relative_to(self.root_dir)),
                "full_path": str(filepath),
                "filename": filepath.name,
                "size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "file_type": filepath.suffix,
                "content_hash": self.calculate_file_hash(filepath),
                "scanned_at": datetime.now().isoformat()
            }
            
            # 尝试读取文档内容提取更多信息
            if filepath.suffix in ['.md', '.txt', '.py', '.js', '.ts', '.json', '.yaml', '.yml']:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        metadata['line_count'] = len(content.splitlines())
                        metadata['char_count'] = len(content)
                        
                        # 尝试提取标题（Markdown文档的第一行）
                        if filepath.suffix == '.md' and content:
                            first_lines = content.split('\n')[:5]
                            for line in first_lines:
                                line = line.strip()
                                if line.startswith('#'):
                                    # 移除#标记
                                    metadata['title'] = line.lstrip('#').strip()
                                    break
                except Exception as e:
                    print(f"无法读取 {filepath} 的内容: {e}")
            
            return metadata
            
        except Exception as e:
            print(f"无法提取 {filepath} 的元数据: {e}")
            return None
    
    def scan_directory(self, directory: Path, exclude_dirs: List[str] = None) -> List[Dict]:
        """递归扫描目录"""
        if exclude_dirs is None:
            exclude_dirs = [
                '.git', '__pycache__', 'node_modules', '.venv', 
                'venv', 'env', 'htmlcov', '.pytest_cache',
                '.hypothesis', 'dist', 'build', '*.egg-info',
                'migration_reports'
            ]
        
        documents = []
        
        for item in directory.rglob('*.md'):
            # 检查是否在排除目录中
            if any(excluded in str(item) for excluded in exclude_dirs):
                continue
            
            metadata = self.extract_metadata(item)
            if metadata:
                documents.append(metadata)
        
        return documents
    
    def scan(self, include_patterns: List[str] = None, exclude_dirs: List[str] = None) -> List[Dict]:
        """扫描项目文档"""
        if include_patterns is None:
            include_patterns = ['.md']
        
        print(f"开始扫描目录: {self.root_dir.absolute()}")
        documents = self.scan_directory(self.root_dir, exclude_dirs)
        self.documents = documents
        print(f"扫描完成，共找到 {len(documents)} 个文档")
        
        return documents
    
    def save_manifest(self, output_file: str = ".cospec/document_cleanup/document_manifest.json"):
        """保存文档清单到JSON文件"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        manifest = {
            "scan_time": datetime.now().isoformat(),
            "total_documents": len(self.documents),
            "documents": self.documents
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        print(f"文档清单已保存到: {output_path}")
        return output_path
    
    def print_summary(self):
        """打印扫描摘要"""
        print("\n" + "="*60)
        print("文档扫描摘要")
        print("="*60)
        print(f"扫描路径: {self.root_dir.absolute()}")
        print(f"文档总数: {len(self.documents)}")
        
        # 按文件类型统计
        type_stats = {}
        for doc in self.documents:
            file_type = doc.get('file_type', 'unknown')
            type_stats[file_type] = type_stats.get(file_type, 0) + 1
        
        print("\n文件类型分布:")
        for file_type, count in sorted(type_stats.items()):
            print(f"  {file_type}: {count}")
        
        # 显示最大的10个文件
        sorted_by_size = sorted(self.documents, key=lambda x: x.get('size', 0), reverse=True)
        print("\n最大的10个文件:")
        for i, doc in enumerate(sorted_by_size[:10], 1):
            print(f"  {i}. {doc['path']} ({doc['size']} bytes)")
        
        # 显示最近修改的10个文件
        sorted_by_time = sorted(self.documents, key=lambda x: x.get('modified_time', ''), reverse=True)
        print("\n最近修改的10个文件:")
        for i, doc in enumerate(sorted_by_time[:10], 1):
            modified_time = doc.get('modified_time', '').split('T')[0]
            print(f"  {i}. {doc['path']} ({modified_time})")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='文档扫描器 - 扫描项目文档并提取元数据')
    parser.add_argument('--root', '-r', default='.', help='扫描根目录 (默认: 当前目录)')
    parser.add_argument('--output', '-o', 
                       default='.cospec/document_cleanup/document_manifest.json',
                       help='输出文件路径 (默认: .cospec/document_cleanup/document_manifest.json)')
    parser.add_argument('--no-save', action='store_true', help='不保存清单文件')
    
    args = parser.parse_args()
    
    # 创建扫描器
    scanner = DocumentScanner(args.root)
    
    # 执行扫描
    documents = scanner.scan()
    
    # 打印摘要
    scanner.print_summary()
    
    # 保存清单
    if not args.no_save:
        scanner.save_manifest(args.output)


if __name__ == "__main__":
    main()