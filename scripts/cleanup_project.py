
#!/usr/bin/env python3
"""
项目清理工具 - 增强版本，包含安全验证和备份机制
"""

import os
import hashlib
import shutil
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

# 配置常量
ROOT_DIR = Path(r"d:\Git\百姓助手")
BACKUP_DIR = ROOT_DIR / "temp" / "cleanup_backup"
LOG_FILE = ROOT_DIR / "temp" / "cleanup_log.json"

# 目标目录配置（基于扫描结果）
TARGET_DIRS_TO_REMOVE = [
    ".codebuddy",
    ".cospec", 
    ".trae",
    ".windsurf",
    ".hypothesis",
    "archive",
    "logs",
    "backups",
]

TARGET_DIRS_RECURSIVE = [
    "__pycache__",
    ".pytest_cache", 
    ".ruff_cache",
    "htmlcov",
    "coverage_html",
    "chroma_db",
    "playwright-report",
]

# 需要保留的文件模式
PROTECTED_PATTERNS = [
    "*.py", "*.pyx", "*.pyi", "*.c", "*.h", 
    "*.md", "*.txt", "*.json", "*.yaml", "*.yml",
    "*.ts", "*.tsx", "*.js", "*.jsx", "*.vue",
    "*.css", "*.scss", "*.html", "*.xml",
    "*.sql", "*.dockerfile", "Dockerfile",
    "*.gitignore", "*.gitmodules",
    "requirements*.txt", "pyproject.toml", "package.json",
    "*.sh", "*.bat", "*.ps1", "*.cmd"
]

class SafetyValidator:
    """安全验证器"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        
    def is_protected_file(self, filepath: Path) -> bool:
        """检查文件是否受保护"""
        for pattern in PROTECTED_PATTERNS:
            if filepath.match(pattern):
                return True
        return False
    
    def is_git_related(self, filepath: Path) -> bool:
        """检查是否与Git相关"""
        git_patterns = [".git", ".gitignore", ".gitmodules"]
        return any(pattern in str(filepath) for pattern in git_patterns)
    
    def is_project_file(self, filepath: Path) -> bool:
        """检查是否是项目核心文件"""
        core_dirs = ["backend", "frontend", "docs", "scripts", "helm", "nginx"]
        return any(filepath.is_relative_to(self.root_dir / core_dir) for core_dir in core_dirs)
    
    def validate_deletion(self, filepath: Path) -> Tuple[bool, str]:
        """验证删除操作的安全性"""
        if not filepath.exists():
            return False, "文件不存在"
            
        if self.is_git_related(filepath):
            return False, "Git相关文件，禁止删除"
            
        if self.is_protected_file(filepath) and self.is_project_file(filepath):
            return False, "项目核心文件，禁止删除"
            
        return True, "安全"

class BackupManager:
    """备份管理器"""
    
    def __init__(self, backup_dir: Path):
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self, filepath: Path) -> bool:
        """创建文件备份"""
        try:
            if filepath.is_file():
                # 创建备份目录结构
                relative_path = filepath.relative_to(ROOT_DIR)
                backup_path = self.backup_dir / relative_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制文件
                shutil.copy2(filepath, backup_path)
                return True
                
            elif filepath.is_dir():
                # 创建目录备份
                relative_path = filepath.relative_to(ROOT_DIR)
                backup_path = self.backup_dir / relative_path
                shutil.copytree(filepath, backup_path, dirs_exist_ok=True)
                return True
                
        except Exception as e:
            print(f"备份失败 {filepath}: {e}")
            return False
            
        return False
    
    def restore_backup(self, filepath: Path) -> bool:
        """恢复备份"""
        try:
            relative_path = filepath.relative_to(ROOT_DIR)
            backup_path = self.backup_dir / relative_path
            
            if backup_path.exists():
                if filepath.exists():
                    if filepath.is_file():
                        filepath.unlink()
                    else:
                        shutil.rmtree(filepath)
                        
                if backup_path.is_file():
                    shutil.copy2(backup_path, filepath)
                else:
                    shutil.copytree(backup_path, filepath)
                    
                return True
                
        except Exception as e:
            print(f"恢复失败 {filepath}: {e}")
            
        return False

class CleanupLogger:
    """清理日志记录器"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_data = {
            'start_time': datetime.now().isoformat(),
            'operations': [],
            'summary': {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
        }
        
    def log_operation(self, operation: str, filepath: str, status: str, reason: str = ""):
        """记录操作日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'filepath': filepath,
            'status': status,
            'reason': reason
        }
        
        self.log_data['operations'].append(log_entry)
        self.log_data['summary']['total'] += 1
        
        if status == 'success':
            self.log_data['summary']['success'] += 1
        elif status == 'failed':
            self.log_data['summary']['failed'] += 1
        elif status == 'skipped':
            self.log_data['summary']['skipped'] += 1
            
    def save_log(self):
        """保存日志文件"""
        self.log_data['end_time'] = datetime.now().isoformat()
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.log_data, f, ensure_ascii=False, indent=2)
            
    def print_summary(self):
        """打印日志摘要"""
        summary = self.log_data['summary']
        print(f"\n清理操作摘要:")
        print(f"  总操作数: {summary['total']}")
        print(f"  成功: {summary['success']}")
        print(f"  失败: {summary['failed']}")
        print(f"  跳过: {summary['skipped']}")

def calculate_hash(filepath: Path, chunk_size: int = 8192) -> str:
    """计算文件的SHA256哈希值"""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()
    except OSError:
        return ""

def find_duplicates(root_dir: Path) -> List[Tuple[Path, Path]]:
    """查找重复文件"""
    hashes = {}
    duplicates = []
    validator = SafetyValidator(root_dir)
    
    print(f"扫描重复文件: {root_dir}...")
    
    for dirpath, _, filenames in os.walk(root_dir):
        # 跳过Git和依赖目录
        if ".git" in dirpath or "node_modules" in dirpath or ".venv" in dirpath:
            continue
            
        for filename in filenames:
            filepath = Path(dirpath) / filename
            
            # 跳过小文件
            if filepath.stat().st_size < 10:
                continue
                
            # 安全验证
            is_safe, reason = validator.validate_deletion(filepath)
            if not is_safe:
                continue
                
            file_hash = calculate_hash(filepath)
            if not file_hash:
                continue
                
            if file_hash in hashes:
                original = hashes[file_hash]
                duplicates.append((filepath, original))
            else:
                hashes[file_hash] = filepath
                
    return duplicates

def remove_directories(root_dir: Path, targets: List[str], logger: CleanupLogger, 
                      backup_manager: BackupManager, validator: SafetyValidator) -> int:
    """删除指定目录"""
    removed_count = 0
    
    for target in targets:
        target_path = root_dir / target
        
        if not target_path.exists():
            logger.log_operation("remove_directory", str(target_path), "skipped", "目录不存在")
            continue
            
        # 安全验证
        is_safe, reason = validator.validate_deletion(target_path)
        if not is_safe:
            logger.log_operation("remove_directory", str(target_path), "skipped", reason)
            continue
            
        # 创建备份
        if backup_manager.create_backup(target_path):
            try:
                shutil.rmtree(target_path)
                logger.log_operation("remove_directory", str(target_path), "success")
                removed_count += 1
                print(f"[OK] 删除目录: {target_path}")
            except Exception as e:
                logger.log_operation("remove_directory", str(target_path), "failed", str(e))
                print(f"[ERROR] 删除失败: {target_path} - {e}")
        else:
            logger.log_operation("remove_directory", str(target_path), "failed", "备份失败")
            
    return removed_count

def remove_recursive_targets(root_dir: Path, targets: List[str], logger: CleanupLogger,
                            backup_manager: BackupManager, validator: SafetyValidator) -> int:
    """递归删除目标目录"""
    removed_count = 0
    
    print(f"扫描递归目标: {targets}")
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for dirname in list(dirnames):
            if dirname in targets:
                full_path = Path(dirpath) / dirname
                
                # 安全验证
                is_safe, reason = validator.validate_deletion(full_path)
                if not is_safe:
                    logger.log_operation("remove_recursive", str(full_path), "skipped", reason)
                    continue
                    
                # 创建备份
                if backup_manager.create_backup(full_path):
                    try:
                        shutil.rmtree(full_path)
                        logger.log_operation("remove_recursive", str(full_path), "success")
                        removed_count += 1
                        dirnames.remove(dirname)  # 不递归到已删除的目录
                        print(f"[OK] 删除递归目录: {full_path}")
                    except Exception as e:
                        logger.log_operation("remove_recursive", str(full_path), "failed", str(e))
                        print(f"[ERROR] 删除失败: {full_path} - {e}")
                else:
                    logger.log_operation("remove_recursive", str(full_path), "failed", "备份失败")
                    
    return removed_count

def remove_duplicate_files(duplicates: List[Tuple[Path, Path]], logger: CleanupLogger,
                          backup_manager: BackupManager, validator: SafetyValidator) -> int:
    """删除重复文件"""
    removed_count = 0
    
    for dup_path, orig_path in duplicates:
        # 检查文件是否仍存在
        if not dup_path.exists() or not orig_path.exists():
            continue
            
        # 安全验证
        is_safe, reason = validator.validate_deletion(dup_path)
        if not is_safe:
            logger.log_operation("remove_duplicate", str(dup_path), "skipped", reason)
            continue
            
        # 创建备份
        if backup_manager.create_backup(dup_path):
            try:
                dup_path.unlink()
                logger.log_operation("remove_duplicate", str(dup_path), "success")
                removed_count += 1
                print(f"[OK] 删除重复文件: {dup_path}")
            except Exception as e:
                logger.log_operation("remove_duplicate", str(dup_path), "failed", str(e))
                print(f"[ERROR] 删除失败: {dup_path} - {e}")
        else:
            logger.log_operation("remove_duplicate", str(dup_path), "failed", "备份失败")
            
    return removed_count

def main():
    """主函数"""
    print("=" * 60)
    print("项目清理工具 - 增强版本")
    print("=" * 60)
    
    # 初始化组件
    validator = SafetyValidator(ROOT_DIR)
    backup_manager = BackupManager(BACKUP_DIR)
    logger = CleanupLogger(LOG_FILE)
    
    print(f"项目根目录: {ROOT_DIR}")
    print(f"备份目录: {BACKUP_DIR}")
    print(f"日志文件: {LOG_FILE}")
    
    print("\n开始清理...")
    
    total_removed = 0
    
    # 1. 删除指定目录
    print("\n1. 删除指定目录...")
    removed = remove_directories(ROOT_DIR, TARGET_DIRS_TO_REMOVE, logger, backup_manager, validator)
    total_removed += removed
    
    # 2. 删除递归目标
    print("\n2. 删除递归目标...")
    removed = remove_recursive_targets(ROOT_DIR, TARGET_DIRS_RECURSIVE, logger, backup_manager, validator)
    total_removed += removed
    
    # 3. 处理重复文件
    print("\n3. 查找重复文件...")
    duplicates = find_duplicates(ROOT_DIR)
    print(f"找到 {len(duplicates)} 对重复文件")
    
    if duplicates:
        removed = remove_duplicate_files(duplicates, logger, backup_manager, validator)
        total_removed += removed
    
    # 保存日志
    logger.save_log()
    
    # 打印摘要
    logger.print_summary()
    print(f"\n总计清理: {total_removed} 个文件/目录")
    
    if BACKUP_DIR.exists():
        print(f"\n备份已创建到: {BACKUP_DIR}")
        print("如需恢复，请使用备份管理器")
    
    print("\n清理完成！")

if __name__ == "__main__":
    main()
