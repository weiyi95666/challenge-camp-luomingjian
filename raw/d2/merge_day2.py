import json
import re
import os
from datetime import datetime

def get_logger(log_file):
    def log(message, level='INFO'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    return log

TOOL_RESULT_SCHEMA = {
    'trace_id': {'required': True, 'type': 'string'},
    'tool': {'required': True, 'type': 'string'},
    'status': {'required': True, 'type': 'string', 'enum': ['success', 'fail']},
    'output': {'required': True, 'type': 'string'},
    'latency_ms': {'required': True, 'type': 'number'}
}

USER_BEHAVIOR_SCHEMA = {
    'user_id': {'required': True, 'type': 'string'},
    'timestamp': {'required': False, 'type': 'string'},
    'action': {'required': True, 'type': 'string', 'enum': ['chat', 'click', 'voice']},
    'content': {'required': True, 'type': 'string'}
}

def standardize_time(time_str):
    time_str = time_str.strip()
    if not time_str:
        return None
    
    formats = [
        '%Y/%m/%d %H:%M',
        '%Y-%m-%dT%H:%M:%S',
        '%Y年%m月%d日 %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
    return time_str

def validate_item(item, schema, log):
    errors = []
    for field, rules in schema.items():
        if rules.get('required') and field not in item:
            errors.append(f"缺少必需字段: {field}")
            continue
        
        if field in item:
            value = item[field]
            expected_type = rules.get('type')
            if expected_type == 'string' and value is not None and not isinstance(value, str):
                errors.append(f"字段 {field} 类型错误: 期望 string, 实际 {type(value).__name__}")
            elif expected_type == 'number' and not isinstance(value, (int, float, str)):
                errors.append(f"字段 {field} 类型错误: 期望 number, 实际 {type(value).__name__}")
            
            if 'enum' in rules and value not in rules['enum']:
                errors.append(f"字段 {field} 值无效: {value}, 有效值: {rules['enum']}")
        
        if rules.get('required') and field in item and not item[field]:
            errors.append(f"必需字段 {field} 值为空")
    
    for error in errors:
        log(error, 'WARN')
    
    return len(errors) == 0

def clean_tool_result_data(data, log):
    total = len(data['results'])
    valid_count = 0
    invalid_count = 0
    cleaned = []
    
    for i, item in enumerate(data['results']):
        log(f"处理 tool_result 记录 {i+1}/{total}: trace_id={item.get('trace_id', 'N/A')}")
        
        if validate_item(item, TOOL_RESULT_SCHEMA, log):
            valid_count += 1
        else:
            invalid_count += 1
        
        try:
            item['latency_ms'] = int(item['latency_ms'])
        except (ValueError, TypeError) as e:
            log(f"latency_ms 转换失败: {item.get('latency_ms')} - {e}", 'ERROR')
        
        output = item['output']
        output = re.sub(r'<!--.*?-->', '', output)
        output = output.replace('呃呃呃', '').replace('嗯…', '')
        output = output.replace('设制中心', '设置中心')
        output = output.replace('**', '')
        output = output.strip()
        item['output'] = output
        cleaned.append(item)
    
    log(f"tool_result 清洗完成！总记录: {total}, 有效: {valid_count}, 无效: {invalid_count}")
    return cleaned

def clean_user_behavior_data(data, log):
    seen = set()
    cleaned = []
    duplicate_count = 0
    valid_count = 0
    invalid_count = 0
    total = len(data)
    
    for i, item in enumerate(data):
        record_str = json.dumps(item, ensure_ascii=False)
        if record_str in seen:
            duplicate_count += 1
            log(f"user_behavior 记录 {i+1}/{total}: 发现重复记录，跳过", 'WARN')
            continue
        seen.add(record_str)
        
        log(f"处理 user_behavior 记录 {i+1}/{total}: uid={item.get('uid') or item.get('user_id', 'N/A')}")
        
        normalized = {}
        normalized['user_id'] = item.get('uid') or item.get('user_id', '')
        normalized['timestamp'] = standardize_time(item.get('time') or item.get('timestamp', ''))
        normalized['action'] = item.get('action') or item.get('type', '')
        
        content = item.get('content') or item.get('text', '')
        content = content.strip()
        content = re.sub(r'[\s　]+', '', content)
        content = content.replace('***', '').replace('@@@', '')
        normalized['content'] = content
        
        if validate_item(normalized, USER_BEHAVIOR_SCHEMA, log):
            valid_count += 1
        else:
            invalid_count += 1
        
        cleaned.append(normalized)
    
    log(f"user_behavior 清洗完成！总记录: {total}, 去重后: {len(cleaned)}, 重复: {duplicate_count}, 有效: {valid_count}, 无效: {invalid_count}")
    return cleaned

def merge_day2_data(input_dir, output_file, log_file):
    log = get_logger(log_file)
    log(f"开始处理 day2 数据")
    
    merged = []
    seen = set()
    
    files = [
        ('tool_result.json', clean_tool_result_data),
        ('user_behavior.json', clean_user_behavior_data)
    ]
    
    for filename, clean_func in files:
        filepath = os.path.join(input_dir, filename)
        if not os.path.exists(filepath):
            log(f"文件不存在，跳过: {filepath}", 'WARN')
            continue
        
        log(f"读取文件: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cleaned_items = clean_func(data, log)
        for item in cleaned_items:
            item_str = json.dumps(item, ensure_ascii=False)
            if item_str not in seen:
                seen.add(item_str)
                merged.append(json.loads(item_str))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in merged:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    log(f"合并完成！共 {len(merged)} 条记录，已保存到 {output_file}")
    
    if len(merged) < 8:
        log(f"警告: 去重后只有 {len(merged)} 行，少于 8 行", 'WARN')
    
    return len(merged)

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'merged.jsonl')
    log_path = os.path.join(script_dir, 'clean.log')
    
    merge_day2_data(script_dir, output_path, log_path)

