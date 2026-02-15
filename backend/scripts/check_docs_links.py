#!/usr/bin/env python3
"""
文档链接检查脚本

检查 docs 目录下的 markdown 文件中的链接有效性：
1. 内部链接（相对路径引用）
2. 锚点链接（#xxx）
3. 排除 http/https 外部链接、_archive 目录

用法：
    py scripts/check_docs_links.py
"""

import os
import re
from pathlib import Path


def find_markdown_files(base_dir: str) -> list[Path]:
    """查找所有 markdown 文件"""
    md_files = []
    for root, dirs, files in os.walk(base_dir):
        # 跳过 _archive 目录
        if "_archive" in root:
            continue
        for f in files:
            if f.endswith(".md"):
                md_files.append(Path(os.path.join(root, f)))
    return md_files


def extract_links(content: str) -> list[tuple]:
    """从 markdown 内容中提取链接"""
    links = []
    # 匹配 [text](link) 格式
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    for match in re.finditer(pattern, content):
        link_text = match.group(1)
        link_target = match.group(2)
        line_no = content[:match.start()].count("\n") + 1
        links.append((link_target, line_no, link_text))
    return links


def validate_link(link: str, base_file: Path, base_dir: Path) -> tuple[bool, str]:
    """验证单个链接"""
    # 跳过外部链接
    if link.startswith(("http://", "https://", "mailto:", "tel:")):
        return True, "external"

    # 跳过锚点链接
    if link.startswith("#"):
        return True, "anchor"

    # 跳过邮件地址
    if "@" in link and not link.startswith("http"):
        return True, "email"

    # 解析相对路径
    link_path = link.split("#")[0]  # 去掉锚点部分
    link_path = link_path.split("?")[0]  # 去掉查询参数

    # 相对路径处理
    if not link_path.startswith("/"):
        # 相对路径
        full_path = base_file.parent / link_path
    else:
        # 绝对路径（从 docs 目录）
        full_path = base_dir / link_path.lstrip("/")

    # 检查文件是否存在
    if full_path.exists():
        return True, "exists"
    else:
        # 尝试添加 .md 后缀
        if not full_path.suffix:
            md_path = full_path.with_suffix(".md")
            if md_path.exists():
                return True, "exists_with_md"
        return False, f"not_found: {full_path}"


def check_docs_links(base_dir: str = "docs") -> dict:
    """检查文档链接"""
    # 尝试多个可能的路径
    possible_paths = [
        Path(base_dir),
        Path(__file__).parent.parent / base_dir,
        Path(__file__).parent.parent.parent / base_dir,
        Path.cwd() / base_dir,
    ]

    base_path = None
    for path in possible_paths:
        if path.exists():
            base_path = path
            break

    if base_path is None:
        return {"error": f"Directory not found: {base_dir}"}

    results = {
        "total_files": 0,
        "total_links": 0,
        "valid_links": 0,
        "invalid_links": [],
        "external_links": 0,
        "anchor_links": 0,
    }

    md_files = find_markdown_files(str(base_path))

    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            links = extract_links(content)
            results["total_links"] += len(links)

            for link_target, line_no, link_text in links:
                is_valid, link_type = validate_link(link_target, md_file, base_path)

                if link_type == "external":
                    results["external_links"] += 1
                elif link_type == "anchor":
                    results["anchor_links"] += 1
                elif is_valid:
                    results["valid_links"] += 1
                else:
                    results["invalid_links"].append({
                        "file": str(md_file.relative_to(base_path)),
                        "line": line_no,
                        "link": link_target,
                        "text": link_text,
                        "reason": link_type,
                    })

            results["total_files"] += 1
        except Exception as e:
            print(f"Error reading {md_file}: {e}")

    return results


def main():
    """主函数"""
    import sys

    base_dir = sys.argv[1] if len(sys.argv) > 1 else "docs"

    print("=" * 60)
    print("文档链接检查工具")
    print("=" * 60)
    print(f"检查目录: {base_dir}")
    print()

    results = check_docs_links(base_dir)

    if "error" in results:
        print(f"错误: {results['error']}")
        return 1

    print(f"检查文件数: {results['total_files']}")
    print(f"总链接数: {results['total_links']}")
    print(f"有效链接: {results['valid_links']}")
    print(f"外部链接: {results['external_links']}")
    print(f"锚点链接: {results['anchor_links']}")
    print()

    if results["invalid_links"]:
        print("无效链接:")
        print("-" * 60)
        for item in results["invalid_links"]:
            print(f"  文件: {item['file']}:{item['line']}")
            print(f"     链接: {item['link']}")
            print(f"     文本: {item['text']}")
            print()
        print("-" * 60)
        count = len(results['invalid_links'])
        print(f"共 {count} 个无效链接")
        return 1
    else:
        print("所有链接均有效!")
        return 0


if __name__ == "__main__":
    exit(main())
