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
            
            if 'enum' in rules and value not in rules['enum']:
                errors.append(f"字段 {field} 值无效: {value}, 有效值: {rules['enum']}")
        
        if rules.get('required') and field in item and not item[field]:
            errors.append(f"必需字段 {field} 值为空")
    
    for error in errors:
        log(error, 'WARN')
    
    return len(errors) == 0

def clean_user_behavior(input_file, output_file, log_file):
    log = get_logger(log_file)
    log(f"开始清洗 user_behavior.json")
    log(f"输入文件: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
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
            log(f"记录 {i+1}/{total}: 发现重复记录，跳过", 'WARN')
            continue
        seen.add(record_str)
        
        log(f"处理记录 {i+1}/{total}: uid={item.get('uid') or item.get('user_id', 'N/A')}")
        
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
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({'results': cleaned}, f, ensure_ascii=False, indent=2)
    
    log(f"清洗完成！")
    log(f"总记录: {total}, 去重后: {len(cleaned)}, 重复: {duplicate_count}")
    log(f"有效: {valid_count}, 无效: {invalid_count}")
    log(f"输出文件: {output_file}")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    clean_user_behavior(
        os.path.join(script_dir, 'user_behavior.json'),
        os.path.join(script_dir, 'user_behavior_cleaned.json'),
        os.path.join(script_dir, 'clean.log')
    )