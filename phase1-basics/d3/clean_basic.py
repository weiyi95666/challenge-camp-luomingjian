import csv
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

def clear_log(log_file):
    if os.path.exists(log_file):
        os.remove(log_file)
        print(f"已清理旧日志: {log_file}")

def is_time_value(value):
    time_formats = [
        '%Y/%m/%d %H:%M',
        '%Y/%m/%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y年%m月%d日 %H:%M',
        '%Y年%m月%d日 %H:%M:%S',
        '%Y-%m-%d',
        '%Y/%m/%d'
    ]
    value = value.strip()
    if not value:
        return False
    for fmt in time_formats:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False

def standardize_time(time_str):
    time_str = time_str.strip()
    if not time_str:
        return ''
    
    formats = [
        '%Y/%m/%d %H:%M',
        '%Y/%m/%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y年%m月%d日 %H:%M',
        '%Y年%m月%d日 %H:%M:%S',
        '%Y-%m-%d',
        '%Y/%m/%d'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
    return time_str

def clean_text(text):
    if not text:
        return ''
    text = text.strip()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'#([^#]+)#', r'\1', text)
    text = re.sub(r'[\s　]+', '', text)
    return text

def clean_csv(input_file, output_file=None, log_file=None):
    log = get_logger(log_file) if log_file else lambda msg, level='INFO': print(msg)
    log(f"开始清洗 CSV 文件")
    log(f"输入文件: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    log(f"检测到列名: {fieldnames}")
    
    time_columns = []
    for col in fieldnames:
        sample_values = [row.get(col, '') for row in rows[:5] if row.get(col)]
        if len(sample_values) >= 2:
            time_count = sum(1 for v in sample_values if is_time_value(v))
            if time_count >= len(sample_values) * 0.5:
                time_columns.append(col)
    
    log(f"自动检测到的时间列: {time_columns}")
    
    cleaned = []
    seen = set()
    duplicate_count = 0
    empty_row_count = 0
    total = len(rows)
    
    for i, row in enumerate(rows):
        record_str = '|'.join(row.values())
        
        message_empty = not row.get('message', '').strip()
        if message_empty:
            empty_row_count += 1
            log(f"记录 {i+1}/{total}: message 为空，已删除该记录", 'WARN')
            continue
        
        empty_cols = [col for col in fieldnames if col != 'message' and (not row.get(col) or not row.get(col).strip())]
        if empty_cols:
            log(f"记录 {i+1}/{total}: 存在空值列 {empty_cols}（非 message），保留但记录 WARN", 'WARN')
        
        if record_str in seen:
            duplicate_count += 1
            log(f"记录 {i+1}/{total}: 发现重复记录，跳过", 'WARN')
            continue
        seen.add(record_str)
        
        new_row = {}
        for col in fieldnames:
            value = row.get(col, '')
            if col in time_columns:
                new_value = standardize_time(value)
                if new_value != value:
                    log(f"记录 {i+1}/{total}: 列 {col} 时间标准化: {value} -> {new_value}")
            else:
                new_value = clean_text(value) if isinstance(value, str) else value
                if value != new_value and value:
                    log(f"记录 {i+1}/{total}: 列 {col} 文本清洗完成")
            new_row[col] = new_value
        
        cleaned.append(new_row)
    
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = base + '_cleaned' + ext
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerows(cleaned)
    
    log(f"清洗完成！")
    log(f"总记录: {total}, 去重后: {len(cleaned)}, 重复: {duplicate_count}, 删除的message空记录: {empty_row_count}")
    log(f"输出文件: {output_file}")
    
    return len(cleaned)

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_files = [f for f in os.listdir(script_dir) if f.endswith('.csv') and 'cleaned' not in f]
    log_file = os.path.join(script_dir, 'clean.log')
    
    clear_log(log_file)
    
    if len(csv_files) == 1:
        input_file = os.path.join(script_dir, csv_files[0])
        clean_csv(input_file, log_file=log_file)
    elif len(csv_files) > 1:
        print(f"发现多个CSV文件，请手动指定要清洗的文件")
        for i, f in enumerate(csv_files, 1):
            print(f"  {i}. {f}")
    else:
        print(f"未找到CSV文件")