#!/usr/bin/env python3
"""
Coverage HTML Report Generator
生成美观的单文件 coverage HTML 报告
"""

import json
import os
from datetime import datetime
from pathlib import Path


def load_coverage_data(coverage_file: str) -> dict:
    """加载 coverage JSON 数据"""
    with open(coverage_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_coverage_color(percent: float) -> str:
    """根据覆盖率返回颜色"""
    if percent >= 80:
        return '#10b981'
    elif percent >= 60:
        return '#f59e0b'
    else:
        return '#ef4444'


def get_coverage_gradient(percent: float) -> str:
    """返回渐变色"""
    if percent >= 80:
        return 'linear-gradient(90deg, #10b981 0%, #34d399 100%)'
    elif percent >= 60:
        return 'linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%)'
    else:
        return 'linear-gradient(90deg, #ef4444 0%, #f87171 100%)'


def format_file_data(data: dict) -> list:
    """格式化文件数据"""
    files = []
    for filepath, file_info in data.get('files', {}).items():
        summary = file_info.get('summary', {})
        classes = file_info.get('classes', {})
        
        class_summaries = []
        for class_name, class_info in classes.items():
            class_summary = class_info.get('summary', {})
            class_summaries.append({
                'name': class_name,
                'covered_lines': class_summary.get('covered_lines', 0),
                'num_statements': class_summary.get('num_statements', 0),
                'percent': class_summary.get('percent_covered', 0),
                'executed_lines': class_info.get('executed_lines', []),
                'missing_lines': class_info.get('missing_lines', []),
            })
        
        files.append({
            'path': filepath,
            'name': Path(filepath).name,
            'covered_lines': summary.get('covered_lines', 0),
            'num_statements': summary.get('num_statements', 0),
            'percent': summary.get('percent_covered', 0),
            'missing_lines': summary.get('missing_lines', []),
            'excluded_lines': summary.get('excluded_lines', []),
            'classes': class_summaries,
        })
    
    files.sort(key=lambda x: x['percent'])
    return files


def generate_html_report(data: dict, output_file: str):
    """生成 HTML 报告"""
    totals = data.get('totals', {})
    overall_percent = totals.get('percent_covered', 0)
    covered_lines = totals.get('covered_lines', 0)
    total_statements = totals.get('num_statements', 0)
    missing_lines = totals.get('missing_lines', 0)
    excluded_lines = totals.get('excluded_lines', 0)
    
    files = format_file_data(data)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coverage Report - 覆盖率报告</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }}
        code, pre, .mono {{ font-family: 'JetBrains Mono', 'Fira Code', monospace; }}
        
        .gradient-bg {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        .card-hover {{
            transition: all 0.3s ease;
        }}
        
        .card-hover:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }}
        
        .progress-bar {{
            background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%);
            border-radius: 9999px;
        }}
        
        .coverage-ring {{
            background: conic-gradient(
                {get_coverage_color(overall_percent)} {overall_percent * 3.6}deg,
                #e5e7eb 0deg
            );
        }}
        
        .uncovered-line {{
            background-color: rgba(239, 68, 68, 0.15);
            border-left: 3px solid #ef4444;
        }}
        
        .excluded-line {{
            background-color: rgba(245, 158, 11, 0.15);
            border-left: 3px solid #f59e0b;
        }}
        
        .code-block {{
            font-size: 13px;
            line-height: 1.6;
        }}
        
        .line-number {{
            color: #9ca3af;
            user-select: none;
            min-width: 3ch;
        }}
        
        .fade-in {{
            animation: fadeIn 0.3s ease-out;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .pulse {{
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: .5; }}
        }}
        
        details > summary {{
            cursor: pointer;
        }}
        
        details[open] summary {{
            margin-bottom: 1rem;
        }}
        
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #c1c1c1;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #a1a1a1;
        }}
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <header class="gradient-bg text-white py-8 px-6 shadow-lg">
        <div class="max-w-7xl mx-auto">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-3xl font-bold mb-2">Coverage Report</h1>
                    <p class="text-white/80 text-sm">代码覆盖率分析报告</p>
                </div>
                <div class="text-right">
                    <p class="text-sm text-white/70">生成时间</p>
                    <p class="font-medium">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </div>
    </header>

    <div class="max-w-7xl mx-auto px-6 -mt-8">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-white rounded-2xl shadow-lg p-6 card-hover md:col-span-1">
                <div class="flex flex-col items-center">
                    <div class="relative w-32 h-32 mb-4">
                        <svg class="w-32 h-32 transform -rotate-90">
                            <circle cx="64" cy="64" r="56" stroke="#e5e7eb" stroke-width="12" fill="none"/>
                            <circle cx="64" cy="64" r="56" stroke="{get_coverage_color(overall_percent)}" stroke-width="12" fill="none"
                                stroke-dasharray="{overall_percent * 3.51} 351" stroke-linecap="round"/>
                        </svg>
                        <div class="absolute inset-0 flex items-center justify-center">
                            <span class="text-3xl font-bold text-gray-800">{overall_percent:.1f}%</span>
                        </div>
                    </div>
                    <h3 class="text-gray-600 font-medium">总体覆盖率</h3>
                </div>
            </div>

            <div class="bg-white rounded-2xl shadow-lg p-6 card-hover">
                <div class="flex items-center">
                    <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mr-4">
                        <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">已覆盖行数</p>
                        <p class="text-2xl font-bold text-gray-800">{covered_lines:,}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-2xl shadow-lg p-6 card-hover">
                <div class="flex items-center">
                    <div class="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mr-4">
                        <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">未覆盖行数</p>
                        <p class="text-2xl font-bold text-gray-800">{missing_lines:,}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-2xl shadow-lg p-6 card-hover">
                <div class="flex items-center">
                    <div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mr-4">
                        <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">总语句数</p>
                        <p class="text-2xl font-bold text-gray-800">{total_statements:,}</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <div class="flex flex-col md:flex-row gap-4">
                <div class="flex-1 relative">
                    <svg class="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                    <input type="text" id="searchInput" placeholder="搜索文件路径..."
                        class="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all">
                </div>
                <select id="filterSelect" class="px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none bg-white">
                    <option value="all">全部文件</option>
                    <option value="low">低覆盖率 (&lt;60%)</option>
                    <option value="medium">中覆盖率 (60-80%)</option>
                    <option value="high">高覆盖率 (&gt;80%)</option>
                </select>
            </div>
        </div>

        <div class="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <h2 class="text-lg font-semibold text-gray-800 mb-4">覆盖率分布</h2>
            <div class="h-6 progress-bar rounded-full overflow-hidden">
                <div class="h-full flex">
                    <div class="h-full bg-red-500" style="width: {max(0, 60 - min(60, overall_percent))}%"></div>
                    <div class="h-full bg-yellow-500" style="width: {max(0, min(20, max(0, overall_percent - 60)))}%"></div>
                    <div class="h-full bg-green-500" style="width: {max(0, overall_percent - 80)}%"></div>
                </div>
            </div>
            <div class="flex justify-between mt-2 text-sm text-gray-500">
                <span>0%</span>
                <span>60%</span>
                <span>80%</span>
                <span>100%</span>
            </div>
        </div>

        <div class="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <h2 class="text-lg font-semibold text-gray-800 mb-4">文件覆盖率详情</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="fileGrid">
'''
    
    for f in files:
        percent = f['percent']
        color = get_coverage_color(percent)
        gradient = get_coverage_gradient(percent)
        
        html += f'''
                <div class="border border-gray-200 rounded-xl p-4 card-hover file-card fade-in" data-percent="{percent}" data-path="{f['path']}">
                    <div class="flex items-start justify-between mb-3">
                        <div class="flex-1 min-w-0">
                            <p class="font-medium text-gray-800 truncate" title="{f['path']}">{f['name']}</p>
                            <p class="text-xs text-gray-400 truncate">{f['path']}</p>
                        </div>
                        <span class="text-lg font-bold ml-2" style="color: {color}">{percent:.1f}%</span>
                    </div>
                    
                    <div class="mb-3">
                        <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div class="h-full rounded-full transition-all duration-500" style="width: {percent}%; background: {gradient}"></div>
                        </div>
                    </div>
                    
                    <div class="flex justify-between text-xs text-gray-500">
                        <span>覆盖: {f['covered_lines']}</span>
                        <span>总计: {f['num_statements']}</span>
                    </div>
'''
        
        if f['classes'] or f['missing_lines']:
            html += f'''
                    <details class="mt-3">
                        <summary class="text-sm text-purple-600 hover:text-purple-700 font-medium flex items-center">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                            </svg>
                            查看详情
                        </summary>
                        <div class="mt-2 text-xs">
'''
            if f['classes']:
                html += '<p class="font-medium text-gray-700 mb-1">类/函数:</p>'
                for cls in f['classes'][:5]:
                    html += f'''
                            <div class="flex items-center justify-between py-1 px-2 bg-gray-50 rounded">
                                <span class="truncate">{cls['name']}</span>
                                <span class="font-medium" style="color: {get_coverage_color(cls['percent'])}">{cls['percent']:.1f}%</span>
                            </div>
'''
                if len(f['classes']) > 5:
                    html += f'<p class="text-gray-400 italic">... 共 {len(f["classes"])} 个类</p>'
            
            html += '''
                        </div>
                    </details>
'''
        
        html += '''
                </div>
'''
    
    html += '''
            </div>
        </div>

        <div class="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <h2 class="text-lg font-semibold text-gray-800 mb-4">图例说明</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="flex items-center">
                    <div class="w-4 h-4 rounded bg-green-500 mr-2"></div>
                    <span class="text-sm text-gray-600">高覆盖率 (≥80%)</span>
                </div>
                <div class="flex items-center">
                    <div class="w-4 h-4 rounded bg-yellow-500 mr-2"></div>
                    <span class="text-sm text-gray-600">中覆盖率 (60-80%)</span>
                </div>
                <div class="flex items-center">
                    <div class="w-4 h-4 rounded bg-red-500 mr-2"></div>
                    <span class="text-sm text-gray-600">低覆盖率 (&lt;60%)</span>
                </div>
                <div class="flex items-center">
                    <div class="w-4 h-4 rounded bg-red-200 mr-2"></div>
                    <span class="text-sm text-gray-600">未覆盖行</span>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-gray-800 text-white py-6 mt-8">
        <div class="max-w-7xl mx-auto px-6 text-center">
            <p class="text-sm text-gray-400">Generated by Coverage Report Generator</p>
        </div>
    </footer>

    <script>
        const searchInput = document.getElementById('searchInput');
        const filterSelect = document.getElementById('filterSelect');
        const fileCards = document.querySelectorAll('.file-card');

        function filterFiles() {
            const searchTerm = searchInput.value.toLowerCase();
            const filterValue = filterSelect.value;

            fileCards.forEach(card => {
                const path = card.dataset.path.toLowerCase();
                const percent = parseFloat(card.dataset.percent);

                const matchesSearch = path.includes(searchTerm);
                let matchesFilter = true;

                if (filterValue === 'low') {
                    matchesFilter = percent < 60;
                } else if (filterValue === 'medium') {
                    matchesFilter = percent >= 60 && percent < 80;
                } else if (filterValue === 'high') {
                    matchesFilter = percent >= 80;
                }

                if (matchesSearch && matchesFilter) {
                    card.style.display = 'block';
                    card.classList.add('fade-in');
                } else {
                    card.style.display = 'none';
                }
            });
        }

        searchInput.addEventListener('input', filterFiles);
        filterSelect.addEventListener('change', filterFiles);

        document.addEventListener('DOMContentLoaded', () => {
            const progressBars = document.querySelectorAll('.progress-bar > div > div');
            progressBars.forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0';
                setTimeout(() => {
                    bar.style.width = width;
                }, 100);
            });
        });

        document.querySelectorAll('.file-card').forEach(card => {
            card.addEventListener('click', () => {
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            });
        });
    </script>
</body>
</html>
'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Coverage report generated: {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate beautiful coverage HTML report')
    parser.add_argument('-i', '--input', default='coverage.json', help='Input coverage JSON file')
    parser.add_argument('-o', '--output', default='coverage_report.html', help='Output HTML file')
    parser.add_argument('-p', '--path', default='.', help='Base path for coverage files')
    
    args = parser.parse_args()
    
    input_file = os.path.join(args.path, args.input)
    output_file = os.path.join(args.path, args.output)
    
    if not os.path.exists(input_file):
        print(f"Error: Coverage file not found: {input_file}")
        return
    
    print(f"Loading coverage data from: {input_file}")
    data = load_coverage_data(input_file)
    
    print(f"Generating HTML report: {output_file}")
    generate_html_report(data, output_file)
    
    print("Done!")


if __name__ == '__main__':
    main()
