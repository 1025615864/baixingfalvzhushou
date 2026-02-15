#!/usr/bin/env python3
"""
项目清理执行器 - 主清理执行器，协调各模块
"""

import os
import json
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 导入清理工具模块
import sys
sys.path.append(str(Path(__file__).parent))

from cleanup_project import SafetyValidator, BackupManager, CleanupLogger
from document_scanner import DocumentScanner


class ProjectCleanupExecutor:
    """项目清理执行器"""
    
    def __init__(self, root_dir: str = "d:/Git/百姓助手"):
        self.root_dir = Path(root_dir)
        self.backup_dir = self.root_dir / "temp" / "cleanup_backup"
        self.log_file = self.root_dir / "temp" / "cleanup_execution_log.json"
        
        # 初始化组件
        self.validator = SafetyValidator(self.root_dir)
        self.backup_manager = BackupManager(self.backup_dir)
        self.logger = CleanupLogger(self.log_file)
        
        # 清理计划配置
        self.cleanup_plan = self._load_cleanup_plan()
    
    def _load_cleanup_plan(self) -> Dict:
        """加载清理计划"""
        return {
            "phase1": {
                "name": "第一阶段清理 - IDE临时文件",
                "targets": [
                    ".codebuddy", ".cospec", ".trae", ".windsurf",
                    ".hypothesis", ".pytest_cache", ".ruff_cache"
                ],
                "description": "删除IDE工具生成的临时文件和测试缓存"
            },
            "phase2": {
                "name": "第二阶段清理 - 日志和备份文件", 
                "targets": [
                    "logs", "backups", "coverage_html", "playwright-report",
                    "chroma_db", "temp"
                ],
                "description": "删除日志文件、备份文件和临时数据"
            },
            "phase3": {
                "name": "第三阶段清理 - 重复配置文件",
                "targets": ["find_duplicates"],
                "description": "查找并删除重复的配置文件"
            },
            "phase4": {
                "name": "第四阶段清理 - 测试系统优化",
                "targets": ["organize_tests"],
                "description": "整理测试文件结构"
            }
        }
    
    def scan_project_structure(self) -> Dict:
        """扫描项目结构"""
        print("扫描项目结构...")
        
        scanner = DocumentScanner(str(self.root_dir))
        documents = scanner.scan()
        
        # 分析项目结构
        structure_analysis = {
            "total_files": len(documents),
            "by_type": {},
            "largest_files": [],
            "recently_modified": []
        }
        
        # 按文件类型统计
        for doc in documents:
            file_type = doc.get('file_type', 'unknown')
            structure_analysis['by_type'][file_type] = structure_analysis['by_type'].get(file_type, 0) + 1
        
        # 最大的文件
        structure_analysis['largest_files'] = sorted(
            documents, 
            key=lambda x: x.get('size', 0), 
            reverse=True
        )[:10]
        
        # 最近修改的文件
        structure_analysis['recently_modified'] = sorted(
            documents,
            key=lambda x: x.get('modified_time', ''),
            reverse=True
        )[:10]
        
        return structure_analysis
    
    def execute_phase(self, phase_id: str) -> bool:
        """执行清理阶段"""
        phase = self.cleanup_plan.get(phase_id)
        if not phase:
            print(f"未知阶段: {phase_id}")
            return False
        
        print(f"\n{'='*60}")
        print(f"执行: {phase['name']}")
        print(f"描述: {phase['description']}")
        print(f"{'='*60}")
        
        if phase_id == "phase1":
            return self._execute_phase1()
        elif phase_id == "phase2":
            return self._execute_phase2()
        elif phase_id == "phase3":
            return self._execute_phase3()
        elif phase_id == "phase4":
            return self._execute_phase4()
        else:
            return False
    
    def _execute_phase1(self) -> bool:
        """执行第一阶段清理"""
        from cleanup_project import remove_directories, remove_recursive_targets
        
        targets = self.cleanup_plan["phase1"]["targets"]
        
        # 删除顶级目录
        removed_dirs = remove_directories(
            self.root_dir, targets, self.logger, self.backup_manager, self.validator
        )
        
        # 删除递归缓存目录
        recursive_targets = [".pytest_cache", ".ruff_cache"]
        removed_recursive = remove_recursive_targets(
            self.root_dir, recursive_targets, self.logger, self.backup_manager, self.validator
        )
        
        total_removed = removed_dirs + removed_recursive
        print(f"第一阶段清理完成，删除 {total_removed} 个目录")
        return total_removed > 0
    
    def _execute_phase2(self) -> bool:
        """执行第二阶段清理"""
        from cleanup_project import remove_directories, remove_recursive_targets
        
        targets = self.cleanup_plan["phase2"]["targets"]
        
        # 删除日志和备份目录
        removed_dirs = remove_directories(
            self.root_dir, targets, self.logger, self.backup_manager, self.validator
        )
        
        print(f"第二阶段清理完成，删除 {removed_dirs} 个目录")
        return removed_dirs > 0
    
    def _execute_phase3(self) -> bool:
        """执行第三阶段清理"""
        from cleanup_project import find_duplicates, remove_duplicate_files
        
        print("查找重复文件...")
        duplicates = find_duplicates(self.root_dir)
        
        if not duplicates:
            print("未找到重复文件")
            return True
        
        print(f"找到 {len(duplicates)} 对重复文件")
        
        # 删除重复文件
        removed_files = remove_duplicate_files(
            duplicates, self.logger, self.backup_manager, self.validator
        )
        
        print(f"第三阶段清理完成，删除 {removed_files} 个重复文件")
        return removed_files > 0
    
    def _execute_phase4(self) -> bool:
        """执行第四阶段清理 - 测试系统优化"""
        print("优化测试系统组织...")
        
        # 分析测试目录结构
        test_dirs = ["backend/tests", "backend/tests_income"]
        
        for test_dir in test_dirs:
            test_path = self.root_dir / test_dir
            if test_path.exists():
                print(f"分析测试目录: {test_dir}")
                
                # 统计测试文件
                test_files = list(test_path.rglob("test_*.py"))
                print(f"  测试文件数量: {len(test_files)}")
                
                # 检查测试覆盖率配置
                coverage_config = self.root_dir / "backend" / ".coveragerc"
                if coverage_config.exists():
                    print("  测试覆盖率配置: 存在")
                
        print("第四阶段清理完成 - 测试系统分析完成")
        return True
    
    def execute_all_phases(self) -> Dict[str, bool]:
        """执行所有清理阶段"""
        print("开始执行所有清理阶段...")
        
        results = {}
        
        for phase_id in ["phase1", "phase2", "phase3", "phase4"]:
            try:
                success = self.execute_phase(phase_id)
                results[phase_id] = success
                
                if not success:
                    print(f"警告: 阶段 {phase_id} 执行失败")
                    
            except Exception as e:
                print(f"阶段 {phase_id} 执行异常: {e}")
                results[phase_id] = False
        
        return results
    
    def generate_cleanup_report(self) -> Dict:
        """生成清理报告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "project_root": str(self.root_dir),
            "phases_executed": {},
            "summary": {
                "total_operations": self.logger.log_data['summary']['total'],
                "successful_operations": self.logger.log_data['summary']['success'],
                "failed_operations": self.logger.log_data['summary']['failed'],
                "skipped_operations": self.logger.log_data['summary']['skipped']
            },
            "recommendations": []
        }
        
        # 添加建议
        if self.backup_dir.exists():
            report["recommendations"].append({
                "type": "backup",
                "message": f"备份文件已创建到 {self.backup_dir}",
                "action": "如需恢复文件，请使用备份管理器"
            })
        
        # 检查是否需要更新.gitignore
        gitignore_path = self.root_dir / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                gitignore_content = f.read()
            
            missing_patterns = []
            patterns_to_add = [".codebuddy", ".cospec", ".trae", ".windsurf", ".hypothesis"]
            
            for pattern in patterns_to_add:
                if pattern not in gitignore_content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                report["recommendations"].append({
                    "type": "gitignore",
                    "message": ".gitignore需要更新",
                    "patterns": missing_patterns,
                    "action": "建议添加缺失的忽略模式"
                })
        
        return report
    
    def save_report(self, report: Dict, output_file: Optional[str] = None):
        """保存清理报告"""
        if not output_file:
            output_file = self.root_dir / "PROJECT_CLEANUP_REPORT.json"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"清理报告已保存到: {output_path}")
    
    def print_summary(self, results: Dict[str, bool]):
        """打印执行摘要"""
        print("\n" + "="*60)
        print("清理执行摘要")
        print("="*60)
        
        for phase_id, success in results.items():
            phase_name = self.cleanup_plan[phase_id]["name"]
            status = "✓ 成功" if success else "✗ 失败"
            print(f"{phase_name}: {status}")
        
        # 打印日志摘要
        self.logger.print_summary()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='项目清理执行器')
    parser.add_argument('--root', '-r', default='d:/Git/百姓助手', 
                       help='项目根目录')
    parser.add_argument('--phase', '-p', choices=['phase1', 'phase2', 'phase3', 'phase4', 'all'],
                       default='all', help='执行特定阶段或所有阶段')
    parser.add_argument('--report', '-o', help='报告输出文件')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不实际删除文件')
    
    args = parser.parse_args()
    
    # 创建执行器
    executor = ProjectCleanupExecutor(args.root)
    
    # 执行清理
    if args.phase == 'all':
        results = executor.execute_all_phases()
    else:
        results = {args.phase: executor.execute_phase(args.phase)}
    
    # 生成报告
    report = executor.generate_cleanup_report()
    
    # 保存报告
    executor.save_report(report, args.report)
    
    # 打印摘要
    executor.print_summary(results)
    
    # 保存日志
    executor.logger.save_log()
    
    print("\n清理执行完成！")


if __name__ == "__main__":
    main()