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

def validate_item(item, schema, log):
    errors = []
    for field, rules in schema.items():
        if rules.get('required') and field not in item:
            errors.append(f"缺少必需字段: {field}")
            continue
        
        if field in item:
            value = item[field]
            expected_type = rules.get('type')
            if expected_type == 'string' and not isinstance(value, str):
                errors.append(f"字段 {field} 类型错误: 期望 string, 实际 {type(value).__name__}")
            elif expected_type == 'number' and not isinstance(value, (int, float, str)):
                errors.append(f"字段 {field} 类型错误: 期望 number, 实际 {type(value).__name__}")
            
            if 'enum' in rules and value not in rules['enum']:
                errors.append(f"字段 {field} 值无效: {value}, 有效值: {rules['enum']}")
    
    for error in errors:
        log(error, 'WARN')
    
    return len(errors) == 0

def clean_tool_result(input_file, output_file, log_file):
    log = get_logger(log_file)
    log(f"开始清洗 tool_result.json")
    log(f"输入文件: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total = len(data['results'])
    valid_count = 0
    invalid_count = 0
    
    for i, item in enumerate(data['results']):
        log(f"处理记录 {i+1}/{total}: trace_id={item.get('trace_id', 'N/A')}")
        
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
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    log(f"清洗完成！")
    log(f"总记录: {total}, 有效: {valid_count}, 无效: {invalid_count}")
    log(f"输出文件: {output_file}")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    clean_tool_result(
        os.path.join(script_dir, 'tool_result.json'),
        os.path.join(script_dir, 'tool_result_cleaned.json'),
        os.path.join(script_dir, 'clean.log')
    )