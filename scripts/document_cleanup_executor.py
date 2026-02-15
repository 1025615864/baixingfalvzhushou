#!/usr/bin/env python3
"""
文档清理执行器 - 执行文档清理计划
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class DocumentCleanupExecutor:
    """文档清理执行器"""
    
    def __init__(self, plan_file: str = ".cospec/document_cleanup/cleanup_plan.json"):
        self.plan_file = Path(plan_file)
        self.plan = {}
        self.execution_log = {
            'execution_time': datetime.now().isoformat(),
            'total_actions': 0,
            'completed_actions': 0,
            'failed_actions': 0,
            'actions': []
        }
        self.load_plan()
    
    def load_plan(self):
        """加载清理计划"""
        with open(self.plan_file, 'r', encoding='utf-8') as f:
            self.plan = json.load(f)
        print(f"已加载清理计划，共 {len(self.plan['actions'])} 个操作")
    
    def execute_archive(self, action: Dict) -> bool:
        """执行归档操作"""
        print(f"  归档: {len(action['files'])} 个文件")
        
        # 创建归档目录
        archive_dir = Path(action['archive_to'])
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        success = True
        for file_path in action['files']:
            try:
                src = Path(file_path)
                if src.exists():
                    # 保留原始目录结构
                    relative_path = src.parent
                    if relative_path.name != '':
                        dest_dir = archive_dir / relative_path.name
                        dest_dir.mkdir(parents=True, exist_ok=True)
                    else:
                        dest_dir = archive_dir
                    
                    dest = dest_dir / src.name
                    shutil.move(str(src), str(dest))
                    print(f"    ✓ 归档: {file_path} -> {action['archive_to']}")
                else:
                    print(f"    ✗ 文件不存在: {file_path}")
                    success = False
            except Exception as e:
                print(f"    ✗ 归档失败 {file_path}: {e}")
                success = False
        
        return success
    
    def execute_delete(self, action: Dict) -> bool:
        """执行删除操作"""
        files_to_delete = action.get('delete', [])
        print(f"  删除: {len(files_to_delete)} 个文件")
        
        success = True
        for file_path in files_to_delete:
            try:
                src = Path(file_path)
                if src.exists():
                    src.unlink()
                    print(f"    ✓ 删除: {file_path}")
                else:
                    print(f"    ✗ 文件不存在: {file_path}")
                    success = False
            except Exception as e:
                print(f"    ✗ 删除失败 {file_path}: {e}")
                success = False
        
        return success
    
    def execute_delete_empty(self, action: Dict) -> bool:
        """执行删除空文件操作"""
        files = action.get('files', [])
        
        # 检查文件是否真的是空文件
        non_empty_files = []
        for file_path in files:
            path = Path(file_path)
            if path.exists() and path.stat().st_size > 0:
                print(f"  ⚠ 文件不为空，跳过: {file_path}")
                non_empty_files.append(file_path)
        
        if non_empty_files:
            # 如果有非空文件，记录但不删除
            log_entry = {
                'type': action['type'],
                'status': 'SKIPPED',
                'reason': '文件不为空',
                'skipped_files': non_empty_files
            }
            self.execution_log['actions'].append(log_entry)
            return True
        
        # 文件确实是空的，执行删除
        print(f"  删除空文件: {len(files)} 个")
        return self.execute_delete({'delete': files})
    
    def execute_review_manual(self, action: Dict) -> bool:
        """执行人工审核操作"""
        files = action.get('files', [])
        print(f"  需要人工审核: {len(files)} 个文件")
        for file_path in files:
            print(f"    - {file_path}")
        
        # 自动跳过人工审核项
        log_entry = {
            'type': action['type'],
            'status': 'SKIPPED',
            'reason': '需要人工审核',
            'files': files
        }
        self.execution_log['actions'].append(log_entry)
        return True
    
    def execute_action(self, action: Dict) -> bool:
        """执行单个操作"""
        action_type = action['type']
        priority = action.get('priority', 'MEDIUM')
        
        print(f"\n执行操作: {action_type} [优先级: {priority}]")
        print(f"  原因: {action.get('reason', '')}")
        
        success = False
        
        if action_type == 'ARCHIVE':
            success = self.execute_archive(action)
        elif action_type == 'DELETE_DUPLICATE':
            success = self.execute_delete(action)
        elif action_type == 'DELETE_EMPTY':
            success = self.execute_delete_empty(action)
        elif action_type == 'DELETE_SIMILAR':
            success = self.execute_delete(action)
        elif action_type == 'REVIEW_MANUAL':
            success = self.execute_review_manual(action)
        else:
            print(f"  ✗未知操作类型: {action_type}")
            success = False
        
        # 记录执行结果
        log_entry = {
            'type': action_type,
            'status': 'SUCCESS' if success else 'FAILED',
            'priority': priority,
            'reason': action.get('reason', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        if 'keep' in action:
            log_entry['keep'] = action['keep']
        if 'delete' in action:
            log_entry['deleted'] = action['delete']
        if 'files' in action and action_type not in ['DELETE_EMPTY']:
            log_entry['files'] = action['files']
        
        self.execution_log['actions'].append(log_entry)
        
        return success
    
    def execute_all(self) -> bool:
        """执行所有操作"""
        print("\n" + "="*60)
        print("开始执行文档清理计划")
        print("="*60)
        
        self.execution_log['total_actions'] = len(self.plan['actions'])
        
        # 按优先级排序：HIGH -> MEDIUM -> LOW
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        sorted_actions = sorted(
            self.plan['actions'],
            key=lambda x: priority_order.get(x.get('priority', 'LOW'), 2)
        )
        
        for action in sorted_actions:
            try:
                success = self.execute_action(action)
                if success:
                    self.execution_log['completed_actions'] += 1
                else:
                    self.execution_log['failed_actions'] += 1
            except Exception as e:
                print(f"\n执行操作时发生错误: {e}")
                self.execution_log['failed_actions'] += 1
        
        self.print_summary()
        return self.execution_log['failed_actions'] == 0
    
    def print_summary(self):
        """打印执行摘要"""
        log = self.execution_log
        
        print("\n" + "="*60)
        print("文档清理执行摘要")
        print("="*60)
        print(f"总操作数: {log['total_actions']}")
        print(f"成功执行: {log['completed_actions']}")
        print(f"执行失败: {log['failed_actions']}")
        print(f"跳过操作: {len([a for a in log['actions'] if a.get('status') == 'SKIPPED'])}")
        
        # 按类型统计
        type_stats = {}
        for action in log['actions']:
            if action['status'] == 'SKIPPED':
                action_type = action['type']
                type_stats[action_type] = type_stats.get(action_type, 0) + 1
        
        if type_stats:
            print("\n跳过的操作:")
            for action_type, count in type_stats.items():
                print(f"  {action_type}: {count}")
    
    def save_log(self, log_file: str = ".cospec/document_cleanup/execution_log.json"):
        """保存执行日志"""
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.execution_log, f, ensure_ascii=False, indent=2)
        
        print(f"\n执行日志已保存到: {log_file}")


def main():
    """主函数"""
    executor = DocumentCleanupExecutor()
    
    # 执行所有操作
    success = executor.execute_all()
    
    # 保存执行日志
    executor.save_log()
    
    if success:
        print("\n文档清理执行完成！")
    else:
        print("\n文档清理执行完成，但有部分操作失败")


if __name__ == "__main__":
    main()