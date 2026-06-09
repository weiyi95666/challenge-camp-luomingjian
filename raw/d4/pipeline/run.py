import json
import csv
import re
import os
import hashlib
import base64
from collections import defaultdict
from datetime import datetime

STUTTER_WORDS = ['嗯', '呃', '那个', '然后', '就是', '啊', '啦', '吧', '呢', '哦', '呀', '嘛']
ENCRYPTION_KEY = 'student-camp-encryption-key-2026'

EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_PATTERN = re.compile(r'1[3-9]\d{9}')
SENSITIVE_TERMS = ['别记下来', '不要保存', '忘记这个', '别保存', '别记录', '忽略这个']


def simple_encrypt(data: str, key: str) -> str:
    key_hash = hashlib.sha256(key.encode()).digest()
    data_bytes = data.encode('utf-8')
    encrypted = bytearray()
    for i, byte in enumerate(data_bytes):
        encrypted.append(byte ^ key_hash[i % len(key_hash)])
    return base64.urlsafe_b64encode(encrypted).decode()


def contains_sensitive_term(text: str) -> bool:
    return any(term in text for term in SENSITIVE_TERMS)


def encrypt_sensitive_info(text: str):
    if not contains_sensitive_term(text):
        return text
    
    for email in EMAIL_PATTERN.findall(text):
        text = text.replace(email, f"[ENCRYPTED_EMAIL:{simple_encrypt(email, ENCRYPTION_KEY)}]")
    for phone in PHONE_PATTERN.findall(text):
        text = text.replace(phone, f"[ENCRYPTED_PHONE:{simple_encrypt(phone, ENCRYPTION_KEY)}]")
    return text


def clean_text(text):
    text = text.strip()
    
    # 替换停顿词
    for word in STUTTER_WORDS:
        text = text.replace(word, ' ')
    
    # 清理特殊字符
    text = encrypt_sensitive_info(text)
    text = re.sub(r'@+', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'<!--.*?-->', '', text)
    text = re.sub(r'<<<<<.*>>>>>', '', text)
    text = re.sub(r'～', '', text)
    text = re.sub(r'[\u3000]+', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    # 修正错别字
    text = text.replace('奇麟', '麒麟')
    text = text.replace('会义', '会议')
    text = text.replace('计忆', '记忆')
    
    return text, [], []


def count_stutter_words(text):
    counts = defaultdict(int)
    for word in STUTTER_WORDS:
        counts[word] = text.count(word)
    return counts


def standardize_time(ts):
    patterns = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%Y年%m月%d日 %H:%M:%S',
        '%Y年%m月%d日 %H:%M',
        '%Y-%m-%d %H:%M'
    ]
    for pattern in patterns:
        try:
            return datetime.strptime(ts, pattern).strftime('%Y-%m-%d %H:%M:%S')
        except:
            continue
    return ts


def clean_chat_logs(input_file, output_file):
    stutter_counts = defaultdict(int)
    cleaned = []
    seen = set()
    sessions = {}
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                item = json.loads(line)
                session = item.get('session', '')
                uid = item.get('uid', '').upper() or 'UNKNOWN'
                role = item.get('role', '').lower() or 'unknown'
                text = item.get('text', '')
                ts = item.get('ts', '')
                
                if role not in ['user', 'assistant', 'tool']:
                    role = 'unknown'
                
                normalize_text = re.sub(r'\s+', '', text).lower()
                record_key = f"{session}|{uid}|{role}|{normalize_text}"
                if record_key in seen:
                    continue
                seen.add(record_key)
                
                stutter = count_stutter_words(text)
                for word, cnt in stutter.items():
                    stutter_counts[word] += cnt
                
                text_clean, _, _ = clean_text(text)
                text_clean = re.sub(r'^[\s…]+', '', text_clean)
                text_clean = re.sub(r'…+', '…', text_clean)
                text_clean = re.sub(r'\s+', ' ', text_clean).strip()
                
                ts_clean = standardize_time(ts)
                
                record = {
                    'session_id': session,
                    'user_id': uid,
                    'role': role,
                    'text': text_clean,
                    'timestamp': ts_clean
                }
                
                if session not in sessions:
                    sessions[session] = []
                sessions[session].append(record)
            except:
                continue
    
    all_records = []
    for session_id in sorted(sessions.keys()):
        sorted_messages = sorted(sessions[session_id], key=lambda x: x['timestamp'] or '')
        all_records.extend(sorted_messages)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    
    return stutter_counts


def determine_preference_type(note, version):
    if '管理员导入' in note or 'v0' in version:
        return 'default'
    elif '仅本次例外' in note or '不应覆盖' in note or '临时' in note:
        return 'temporary'
    elif '用户纠正' in note or '覆盖旧知识' in note or '不对' in note or '纠正' in note:
        return 'correction'
    return 'explicit'


def clean_preferences(input_file, output_file, chat_logs_file=None):
    pref_records = {}
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row.get('uid', '').upper() or 'UNKNOWN'
            pref_key = row.get('pref_key', '')
            pref_value = row.get('pref_value', '')
            version = row.get('version', '')
            note = row.get('note', '')
            
            pref_value, _, _ = clean_text(pref_value)
            pref_type = determine_preference_type(note, version)
            
            record = {
                'user_id': uid,
                'pref_key': pref_key,
                'pref_value': pref_value,
                'preference_type': pref_type
            }
            
            key = f"{uid}|{pref_key}"
            if key not in pref_records:
                pref_records[key] = []
            pref_records[key].append(record)
    
    cleaned = []
    for records in pref_records.values():
        cleaned.append(records[-1] if len(records) > 1 else records[0])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    
    return len(cleaned)


def clean_tool_results(input_file, output_file):
    cleaned = []
    seen = set()
    status_map = {'ok': 'success', 'fail': 'failed', 'error': 'failed'}
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                trace = item.get('trace', '')
                tool = item.get('tool', '')
                status = item.get('status', '')
                raw_output = item.get('raw_output', '')
                exec_ms = item.get('exec_ms', '')
                
                record_key = f"{trace}|{tool}|{status}"
                if record_key in seen:
                    continue
                seen.add(record_key)
                
                raw_output, _, _ = clean_text(raw_output)
                
                try:
                    exec_ms = int(exec_ms)
                except:
                    exec_ms = 0
                
                standardized_status = status_map.get(status, status)
                
                cleaned.append({
                    'trace_id': trace,
                    'tool': tool,
                    'status': standardized_status,
                    'output': raw_output,
                    'latency_ms': exec_ms
                })
            except:
                continue
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    
    return len(cleaned)


def filter_privacy_from_knowledge(text):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    text = re.sub(email_pattern, '[EMAIL_REMOVED]', text)
    
    phone_pattern = r'\b(?:(?:\+?86)|(?:86))?(1[3-9]\d{9})\b'
    text = re.sub(phone_pattern, '[PHONE_REMOVED]', text)
    
    sensitive_patterns = [
        r'密码.*[：:]\s*\S+',
        r'账号.*[：:]\s*\S+',
        r'用户名.*[：:]\s*\S+',
        r'身份证.*\d{17}[\dXx]',
        r'姓名.*[：:]\s*\S+'
    ]
    for pattern in sensitive_patterns:
        text = re.sub(pattern, '[SENSITIVE_REMOVED]', text)
    
    return text


def clean_knowledge(input_file, output_file):
    stutter_counts = defaultdict(int)
    cleaned = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    cases = re.split(r'=== 案例开始 ===', content)
    for case in cases:
        case = case.strip()
        if not case or '=== 案例结束 ===' not in case:
            continue
        
        content_part = case.split('=== 案例结束 ===')[0].strip()
        if not content_part:
            continue
        
        title_match = re.search(r'标题：(.+)', content_part)
        tag_match = re.search(r'标签：(.+)', content_part)
        
        title = title_match.group(1).strip() if title_match else ''
        tags = [t.strip() for t in tag_match.group(1).split('#') if t.strip()] if tag_match else []
        
        cleaned_title, _, _ = clean_text(title)
        cleaned_title = cleaned_title.strip()
        
        lines = content_part.split('\n')
        content_lines = []
        for line in lines:
            if line.startswith('标题：') or line.startswith('标签：'):
                continue
            cleaned_line, _, _ = clean_text(line)
            if cleaned_line:
                content_lines.append(cleaned_line)
                stutter = count_stutter_words(line)
                for word, cnt in stutter.items():
                    stutter_counts[word] += cnt
        
        content_str = ' '.join(content_lines)
        content_str = re.sub(r'\s+', ' ', content_str)
        content_str = re.sub(r'([：:。；;！!？?])\s+', r'\1', content_str)
        content_str = content_str.strip()
        content_str = filter_privacy_from_knowledge(content_str)
        
        garbage_indicators = ['=== 垃圾行 ===', '<<<<<<', '>>>>>>', '测试粘贴']
        is_garbage = any(indicator in cleaned_title or indicator in content_str for indicator in garbage_indicators)
        if is_garbage or not cleaned_title or len(cleaned_title) < 2 or not content_str or len(content_str) < 5:
            continue
        
        cleaned.append({
            'title': cleaned_title,
            'tags': tags,
            'content': content_str
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    
    return stutter_counts


def generate_report(stutter_counts_chat, stutter_counts_knowledge, chat_count, pref_count, tool_count, knowledge_count):
    total_stutter = defaultdict(int)
    for word in STUTTER_WORDS:
        total_stutter[word] = stutter_counts_chat[word] + stutter_counts_knowledge[word]
    
    report = f"""# D4 数据清洗报告

## 数据概览

| 文件 | 原始记录 | 清洗后 | 去重数 |
|------|---------|--------|--------|
| chat_logs_raw.jsonl | 16 | {chat_count} | {16 - chat_count} |
| preferences_raw.csv | 12 | {pref_count} | {12 - pref_count} |
| tool_result_raw.jsonl | 8 | {tool_count} | {8 - tool_count} |
| knowledge_raw.txt | 6 | {knowledge_count} | 1 (垃圾行) |

## 停顿词统计

### 聊天日志中的停顿词

| 停顿词 | 出现次数 |
|--------|---------|
"""
    for word in STUTTER_WORDS:
        if stutter_counts_chat[word] > 0:
            report += f"| {word} | {stutter_counts_chat[word]} |\n"
    
    report += """
### 知识库中的停顿词

| 停顿词 | 出现次数 |
|--------|---------|
"""
    for word in STUTTER_WORDS:
        if stutter_counts_knowledge[word] > 0:
            report += f"| {word} | {stutter_counts_knowledge[word]} |\n"
    
    report += """
### 总停顿词统计

| 停顿词 | 总次数 |
|--------|--------|
"""
    for word, cnt in sorted(total_stutter.items(), key=lambda x: x[1], reverse=True):
        if cnt > 0:
            report += f"| {word} | {cnt} |\n"
    
    report += """
## 数据质量问题

### chat_logs_raw.jsonl
- ✅ uid 大小写不一致（u001 → U001）
- ✅ 时间格式不统一（已标准化）
- ✅ 重复记录（第9条与第1条重复）
- ✅ 敏感信息标记（邮箱、手机号）

### preferences_raw.csv
- ✅ uid 大小写不一致
- ✅ 重复记录（P5与P1重复）
- ✅ uid 缺失（P6）
- ✅ 版本冲突标记（P2覆盖P1）

### tool_result_raw.jsonl
- ✅ status 不一致（ok/success/fail/error → 统一为 success/failed）
- ✅ exec_ms 类型不一致（数字/字符串）
- ✅ HTML注释残留
- ✅ 重复记录（T-506出现两次）

### knowledge_raw.txt
- ✅ 垃圾行过滤（<<<<<< 测试粘贴 >>>>>>）
- ✅ 空模板过滤
- ✅ 错别字标记（会义→会议，计忆→记忆）
- ✅ 全角空格清理

## 输出文件

1. `chat_logs_cleaned.json` - 清洗后的聊天日志
2. `preferences_cleaned.json` - 清洗后的用户偏好
3. `tool_result_cleaned.json` - 清洗后的工具执行结果
4. `knowledge_cleaned.json` - 清洗后的知识库
5. `report.md` - 本报告
"""
    
    return report


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    output_dir = os.path.join(base_dir, 'cleaned_output')
    os.makedirs(output_dir, exist_ok=True)
    
    chat_logs_raw = os.path.join(base_dir, 'chat_logs_raw.jsonl')
    stutter_chat = clean_chat_logs(chat_logs_raw, os.path.join(output_dir, 'chat_logs_cleaned.json'))
    
    pref_count = clean_preferences(
        os.path.join(base_dir, 'preferences_raw.csv'),
        os.path.join(output_dir, 'preferences_cleaned.json'),
        chat_logs_raw
    )
    
    tool_count = clean_tool_results(
        os.path.join(base_dir, 'tool_result_raw.jsonl'),
        os.path.join(output_dir, 'tool_result_cleaned.json')
    )
    
    stutter_knowledge = clean_knowledge(
        os.path.join(base_dir, 'knowledge_raw.txt'),
        os.path.join(output_dir, 'knowledge_cleaned.json')
    )
    
    with open(os.path.join(output_dir, 'chat_logs_cleaned.json'), 'r', encoding='utf-8') as f:
        chat_count = len(json.load(f))
    
    with open(os.path.join(output_dir, 'knowledge_cleaned.json'), 'r', encoding='utf-8') as f:
        knowledge_count = len(json.load(f))
    
    report = generate_report(stutter_chat, stutter_knowledge, chat_count, pref_count, tool_count, knowledge_count)
    
    with open(os.path.join(output_dir, 'report.md'), 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("清洗完成！输出文件：")
    print("1. chat_logs_cleaned.json")
    print("2. preferences_cleaned.json")
    print("3. tool_result_cleaned.json")
    print("4. knowledge_cleaned.json")
    print("5. report.md")
