#!/usr/bin/env python3
"""
文档清理报告生成器 - 对比清理前后的文档清单
"""

import json
from pathlib import Path
from datetime import datetime


def generate_cleanup_report():
    """生成清理报告"""
    
    # 读取清理前的清单
    before_file = Path(".cospec/document_cleanup/document_manifest.json")
    with open(before_file, 'r', encoding='utf-8') as f:
        before_data = json.load(f)
    
    # 读取清理后的清单
    after_file = Path(".cospec/document_cleanup/document_manifest_after_cleanup.json")
    if not after_file.exists():
        print("清理后清单文件不存在，请先运行扫描")
        return
    
    with open(after_file, 'r', encoding='utf-8') as f:
        after_data = json.load(f)
    
    before_docs = {doc['path']: doc for doc in before_data['documents']}
    after_docs = {doc['path']: doc for doc in after_data['documents']}
    
    # 找出被删除的文档
    deleted_docs = []
    for path, doc in before_docs.items():
        if path not in after_docs:
            deleted_docs.append(doc)
    
    # 找出新增的文档
    new_docs = []
    for path, doc in after_docs.items():
        if path not in before_docs:
            new_docs.append(doc)
    
    # 检查归档目录
    archive_dir = Path("archive")
    archived_files = []
    if archive_dir.exists():
        for md_file in archive_dir.rglob("*.md"):
            archived_files.append({
                'path': str(md_file.relative_to(".")),
                'size': md_file.stat().st_size
            })
    
    # 生成报告
    report = {
        'report_time': datetime.now().isoformat(),
        'before': {
            'total_documents': len(before_data['documents']),
            'total_size': sum(doc['size'] for doc in before_data['documents'])
        },
        'after': {
            'total_documents': len(after_data['documents']),
            'total_size': sum(doc['size'] for doc in after_data['documents'])
        },
        'changes': {
            'deleted_count': len(deleted_docs),
            'deleted_size': sum(doc['size'] for doc in deleted_docs),
            'new_count': len(new_docs),
            'new_size': sum(doc['size'] for doc in new_docs),
            'archived_count': len(archived_files),
            'archived_size': sum(doc['size'] for doc in archived_files)
        },
        'deleted_documents': deleted_docs,
        'new_documents': new_docs,
        'archived_documents': archived_files[:20]  # 只显示前20个
    }
    
    # 保存报告
    output_file = Path(".cospec/document_cleanup/cleanup_report.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 打印摘要
    print("\n" + "="*60)
    print("文档清理效果报告")
    print("="*60)
    print(f"\n清理前: {report['before']['total_documents']} 个文档")
    print(f"清理后: {report['after']['total_documents']} 个文档")
    print(f"减少: {report['changes']['deleted_count']} 个文档")
    
    print(f"\n清理前总大小: {report['before']['total_size']:,} bytes")
    print(f"清理后总大小: {report['after']['total_size']:,} bytes")
    
    if report['changes']['deleted_count'] > 0:
        print(f"\n已删除的文档 ({len(deleted_docs)} 个):")
        for doc in deleted_docs:
            print(f"  - {doc['path']} ({doc['size']} bytes)")
    
    if report['changes']['archived_count'] > 0:
        print(f"\n已归档的文档 ({len(archived_files)} 个):")
        for doc in archived_files[:10]:
            print(f"  - {doc['path']} ({doc['size']} bytes)")
        if len(archived_files) > 10:
            print(f"  ... 还有 {len(archived_files) - 10} 个文件")
    
    if report['changes']['new_count'] > 0:
        print(f"\n新增的文档 ({len(new_docs)} 个):")
        for doc in new_docs:
            print(f"  - {doc['path']}")
    
    print(f"\n报告已保存到: {output_file}")
    print(f"\n清理效果:")
    print(f"  删除文档: {report['changes']['deleted_count']} 个")
    print(f"  归档文档: {report['changes']['archived_count']} 个")
    print(f"  新增文档: {report['changes']['new_count']} 个")
    print(f"  总计减少: {report['changes']['deleted_count']} 个文档")


if __name__ == "__main__":
    generate_cleanup_report()