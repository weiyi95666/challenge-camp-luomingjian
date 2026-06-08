import json
import os

def merge_day2_data(input_dir, output_file):
    merged = []
    seen = set()
    
    files_to_merge = [
        'tool_result_cleaned.json',
        'user_behavior_cleaned.json'
    ]
    
    for filename in files_to_merge:
        filepath = os.path.join(input_dir, filename)
        if not os.path.exists(filepath):
            print(f"文件不存在，跳过: {filepath}")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = data.get('results', []) if isinstance(data, dict) else data
        for item in results:
            item_str = json.dumps(item, ensure_ascii=False)
            if item_str not in seen:
                seen.add(item_str)
                merged.append(json.loads(item_str))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in merged:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"合并完成！共 {len(merged)} 条记录，已保存到 {output_file}")
    return len(merged)

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'merged.jsonl')
    
    count = merge_day2_data(script_dir, output_path)
    
    if count < 8:
        print(f"警告: 去重后只有 {count} 行，少于 8 行")