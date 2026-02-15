#!/usr/bin/env python3
"""
安全门禁脚本
在CI/CD中检查安全问题，如果发现高风险问题则失败
"""
import subprocess
import sys
import json
from pathlib import Path


def check_bandit_high_severity():
    """检查bandit高风险问题"""
    print("=" * 60)
    print("检查 Bandit 高风险问题...")
    print("=" * 60)
    
    backend_dir = Path(__file__).parent.parent / "app"
    
    try:
        # 运行bandit并生成JSON报告
        result = subprocess.run(
            ["bandit", "-r", str(backend_dir), "-f", "json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print("✅ 未发现安全问题")
            return True
        
        # 解析JSON报告
        try:
            report = json.loads(result.stdout)
            high_severity = [r for r in report.get("results", []) if r.get("issue_severity") == "HIGH"]
            medium_severity = [r for r in report.get("results", []) if r.get("issue_severity") == "MEDIUM"]
            
            print(f"\n发现 {len(high_severity)} 个高风险问题")
            for issue in high_severity:
                print(f"  - {issue.get('test_id')}: {issue.get('issue_text')}")
                print(f"    文件: {issue.get('filename')}:{issue.get('line_number')}")
            
            print(f"\n发现 {len(medium_severity)} 个中风险问题")
            
            # 如果有高风险问题，返回失败
            if high_severity:
                print("\n❌ 发现高风险安全问题，构建失败")
                return False
            else:
                print("\n⚠️  仅有中风险问题，构建继续")
                return True
                
        except json.JSONDecodeError:
            print("⚠️  无法解析bandit报告，检查屏幕输出")
            print(result.stdout)
            # 无法解析时，保守处理：如果bandit返回非0，检查屏幕输出
            if "HIGH" in result.stdout:
                print("❌ 屏幕输出中发现高风险问题")
                return False
            return True
            
    except FileNotFoundError:
        print("❌ 未找到bandit命令，请先安装: pip install bandit")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def check_safety_vulnerabilities():
    """检查safety依赖漏洞"""
    print("\n" + "=" * 60)
    print("检查 Safety 依赖漏洞...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["safety", "check", "--json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print("✅ 未发现依赖漏洞")
            return True
        
        # 解析JSON报告
        try:
            vulnerabilities = json.loads(result.stdout)
            
            if vulnerabilities:
                print(f"\n发现 {len(vulnerabilities)} 个依赖漏洞")
                for vuln in vulnerabilities:
                    print(f"  - {vuln.get('advisory_id', 'N/A')}: {vuln.get('advisory', 'N/A')}")
                    print(f"    包: {vuln.get('package_name')}@{vuln.get('analyzed_version')}")
                    print(f"    修复版本: {vuln.get('affected_versions')}")
                
                print("\n❌ 发现依赖漏洞，构建失败")
                return False
            else:
                print("✅ 未发现依赖漏洞")
                return True
                
        except json.JSONDecodeError:
            print("⚠️  无法解析safety报告，检查屏幕输出")
            print(result.stdout)
            # 无法解析时，保守处理：如果safety返回非0，检查屏幕输出
            if "vulnerability" in result.stdout.lower():
                print("❌ 屏幕输出中发现依赖漏洞")
                return False
            return True
            
    except FileNotFoundError:
        print("❌ 未找到safety命令，请先安装: pip install safety")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def main():
    """主函数"""
    print("🔒 安全门禁检查...")
    
    bandit_passed = check_bandit_high_severity()
    safety_passed = check_safety_vulnerabilities()
    
    print("\n" + "=" * 60)
    print("安全门禁总结")
    print("=" * 60)
    print(f"Bandit检查: {'✅ 通过' if bandit_passed else '❌ 失败'}")
    print(f"Safety检查: {'✅ 通过' if safety_passed else '❌ 失败'}")
    
    # 如果任一检查失败，返回非0
    if not bandit_passed or not safety_passed:
        print("\n❌ 安全门禁检查失败")
        sys.exit(1)
    else:
        print("\n✅ 安全门禁检查通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
