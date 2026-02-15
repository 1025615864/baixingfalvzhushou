import json
import sys

def analyze_openapi(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        paths = data.get('paths', {})
        api_summary = []
        
        for path, methods in paths.items():
            for method, details in methods.items():
                tags = details.get('tags', [])
                summary = details.get('summary', '')
                api_summary.append({
                    'path': path,
                    'method': method.upper(),
                    'tags': tags,
                    'summary': summary
                })
        
        # Sort by tag then path
        api_summary.sort(key=lambda x: (x['tags'][0] if x['tags'] else 'Uncategorized', x['path']))
        
        print(f"Total API Endpoints: {len(api_summary)}")
        
        current_tag = None
        for api in api_summary:
            tag = api['tags'][0] if api['tags'] else 'Uncategorized'
            if tag != current_tag:
                print(f"\n## Module: {tag}")
                current_tag = tag
            print(f"- {api['method']} {api['path']} : {api['summary']}")
            
    except Exception as e:
        print(f"Error analyzing openapi.json: {e}")

if __name__ == "__main__":
    analyze_openapi('openapi.json')
