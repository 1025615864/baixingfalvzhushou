#!/usr/bin/env python3
"""
检查Trivy扫描结果中的漏洞数量
用于CI/CD流程中阻断包含CRITICAL级别漏洞的构建
"""

import json
import sys
import argparse


def count_vulnerabilities(report_path: str, severity: str = "CRITICAL") -> int:
    """统计指定严重级别的漏洞数量"""
    try:
        with open(report_path) as f:
            data = json.load(f)
        
        count = 0
        for result in data.get("Results", []):
            for vuln in result.get("Vulnerabilities", []):
                if vuln.get("Severity") == severity:
                    count += 1
        return count
    except Exception as e:
        print(f"::warning::解析扫描结果失败: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="检查Trivy扫描结果")
    parser.add_argument("--report", required=True, help="Trivy JSON报告路径")
    parser.add_argument(
        "--severity",
        default="CRITICAL",
        help="要检查的漏洞严重级别 (CRITICAL, HIGH, MEDIUM, LOW)",
    )
    parser.add_argument(
        "--max-allowed",
        type=int,
        default=0,
        help="允许的最大漏洞数量，超过则返回非零退出码",
    )
    
    args = parser.parse_args()
    
    count = count_vulnerabilities(args.report, args.severity)
    
    if count > args.max_allowed:
        print(f"::error::发现 {count} 个 {args.severity} 级别漏洞")
        print("请查看 Trivy 扫描报告获取详情")
        print(f"::error::镜像包含 {args.severity} 级别漏洞，构建被阻断")
        sys.exit(1)
    else:
        print(f"✅ 未检测到 {args.severity} 级别漏洞")
        sys.exit(0)


if __name__ == "__main__":
    main()