#!/usr/bin/env python3
"""
安全扫描脚本
使用bandit和safety进行代码安全扫描
"""
import subprocess
import sys
from pathlib import Path


def run_bandit_scan():
    """运行bandit安全扫描"""
    print("=" * 60)
    print("运行 Bandit 安全扫描...")
    print("=" * 60)
    
    backend_dir = Path(__file__).parent.parent / "app"
    
    try:
        result = subprocess.run(
            ["bandit", "-r", str(backend_dir), "-f", "screen"],
            capture_output=True,
            text=True,
            check=False
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Bandit返回非0表示发现问题，但这不是错误
        if result.returncode == 0:
            print("✅ Bandit扫描完成，未发现安全问题")
        else:
            print(f"⚠️  Bandit扫描完成，发现安全问题（退出码: {result.returncode}）")
        
        return result.returncode
    except FileNotFoundError:
        print("❌ 未找到bandit命令，请先安装: pip install bandit")
        return 1
    except Exception as e:
        print(f"❌ Bandit扫描失败: {e}")
        return 1


def run_safety_scan():
    """运行safety依赖安全扫描"""
    print("\n" + "=" * 60)
    print("运行 Safety 依赖安全扫描...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["safety", "check"],
            capture_output=True,
            text=True,
            check=False
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Safety返回0表示安全，非0表示发现问题
        if result.returncode == 0:
            print("✅ Safety扫描完成，未发现依赖漏洞")
        else:
            print(f"⚠️  Safety扫描完成，发现依赖漏洞（退出码: {result.returncode}）")
        
        return result.returncode
    except FileNotFoundError:
        print("❌ 未找到safety命令，请先安装: pip install safety")
        return 1
    except Exception as e:
        print(f"❌ Safety扫描失败: {e}")
        return 1


def main():
    """主函数"""
    print("🔒 开始安全扫描...")
    
    bandit_exit_code = run_bandit_scan()
    safety_exit_code = run_safety_scan()
    
    print("\n" + "=" * 60)
    print("安全扫描总结")
    print("=" * 60)
    print(f"Bandit扫描退出码: {bandit_exit_code}")
    print(f"Safety扫描退出码: {safety_exit_code}")
    
    # 如果任一扫描失败，返回非0
    if bandit_exit_code != 0 or safety_exit_code != 0:
        print("\n⚠️  安全扫描发现潜在问题，请检查上述输出")
        sys.exit(1)
    else:
        print("\n✅ 所有安全扫描通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
