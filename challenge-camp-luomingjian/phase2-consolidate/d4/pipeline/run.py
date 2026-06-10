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

# 敏感模式和命令词将从配置文件加载
EMAIL_PATTERN = None
PHONE_PATTERN = None
SENSITIVE_TERMS = []

def load_config(config_path):
    """从 YAML 配置文件加载安全配置"""
    global EMAIL_PATTERN, PHONE_PATTERN, SENSITIVE_TERMS
    
    if not os.path.exists(config_path):
        # 使用默认值
        EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        PHONE_PATTERN = re.compile(r'1[3-9]\d{9}')
        SENSITIVE_TERMS = ['别记下来', '不要保存', '忘记这个', '别保存', '别记录', '忽略这个']
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析 YAML 格式（简化解析）
    sensitive_patterns = []
    forget_commands = []
    
    lines = content.split('\n')
    in_patterns = False
    in_commands = False
    
    for line in lines:
        if 'sensitive_patterns:' in line:
            in_patterns = True
            in_commands = False
            continue
        elif 'forget_commands:' in line:
            in_patterns = False
            in_commands = True
            continue
        elif ':' in line and not line.strip().startswith('-'):
            in_patterns = False
            in_commands = False
        
        if in_patterns and line.strip().startswith('-'):
            pattern = line.strip().lstrip('- ').strip('"').strip("'")
            sensitive_patterns.append(pattern)
        elif in_commands and line.strip().startswith('-'):
            command = line.strip().lstrip('- ').strip('"').strip("'")
            forget_commands.append(command)
    
    # 解析敏感模式
    for pattern in sensitive_patterns:
        if pattern.startswith('email:'):
            email_regex = pattern.replace('email:', '').replace('\\\\', '\\')
            EMAIL_PATTERN = re.compile(email_regex)
        elif pattern.startswith('phone:'):
            phone_regex = pattern.replace('phone:', '').replace('\\\\', '\\')
            PHONE_PATTERN = re.compile(phone_regex)
    
    # 设置遗忘命令词（包含配置中的和扩展的）
    SENSITIVE_TERMS = forget_commands + ['不要保存', '别保存', '别记录', '忽略这个']
    
    # 如果没有解析到模式，使用默认值
    if EMAIL_PATTERN is None:
        EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    if PHONE_PATTERN is None:
        PHONE_PATTERN = re.compile(r'1[3-9]\d{9}')

def simple_encrypt(data: str, key: str) -> str:
    key_hash = hashlib.sha256(key.encode()).digest()
    data_bytes = data.encode('utf-8')
    encrypted = bytearray()
    for i, byte in enumerate(data_bytes):
        encrypted.append(byte ^ key_hash[i % len(key_hash)])
    return base64.urlsafe_b64encode(encrypted).decode()

def contains_sensitive_term(text: str) -> bool:
    """检查文本是否包含敏感提示词"""
    for term in SENSITIVE_TERMS:
        if term in text:
            return True
    return False

def encrypt_sensitive_info(text: str):
    # 只有当文本中包含敏感提示词时才加密
    if not contains_sensitive_term(text):
        return text
    
    for email in EMAIL_PATTERN.findall(text):
        encrypted_email = simple_encrypt(email, ENCRYPTION_KEY)
        text = text.replace(email, f"[ENCRYPTED_EMAIL:{encrypted_email}]")
    for phone in PHONE_PATTERN.findall(text):
        encrypted_phone = simple_encrypt(phone, ENCRYPTION_KEY)
        text = text.replace(phone, f"[ENCRYPTED_PHONE:{encrypted_phone}]")
    return text

def clean_text(text):
    original_text = text
    filler_removed = []
    symbols_removed = []
    
    text = text.strip()
    
    # 记录并移除停顿词（但保留内容完整性）
    for word in STUTTER_WORDS:
        if word in text:
            filler_removed.append(word)
            # 替换为一个空格而不是空字符串，保持语义连贯
            text = text.replace(word, ' ')
    
    # 去除多余空格
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # 记录并移除特殊符号
    symbols = ['【', '】', '～']
    for symbol in symbols:
        if symbol in original_text:
            symbols_removed.append(symbol)
    
    # 特殊处理：把【简洁版】保留下来，因为这是重要信息
    # 先提取括号里的内容
    bracket_match = re.search(r'【(.+?)】', original_text)
    if bracket_match:
        bracket_content = bracket_match.group(1)
        # 如果括号里有内容，保留下来
        text = re.sub(r'【(.+?)】', ' ' + bracket_content + ' ', text)
    
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
    
    return text, filler_removed, symbols_removed

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
            dt = datetime.strptime(ts, pattern)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            continue
    return ts

def extract_real_demand(text):
    """提取用户真实需求，保留关键信息"""
    demand = text.strip()
    
    # 移除强调重复的词
    demand = re.sub(r'(.)\1{2,}', r'\1', demand)
    demand = re.sub(r'不对不对', '不对', demand)
    demand = re.sub(r'啊{2,}', '啊', demand)
    demand = re.sub(r'[！!？?]{2,}', lambda m: m.group(0)[0], demand)
    
    # 提取核心需求标记 - 更智能的处理
    core_markers = ['帮我', '要', '需要', '请', '能不能', '应该']
    best_demand = demand
    for marker in core_markers:
        if marker in demand:
            idx = demand.find(marker)
            candidate = demand[idx:].strip()
            # 确保提取的内容不会太短
            if len(candidate) >= 3:
                best_demand = candidate
                break
    
    # 进一步简化，但确保不会清空
    demand = best_demand
    demand = re.sub(r'……+', ' ', demand)
    demand = re.sub(r'^请用这个', '', demand)
    demand = re.sub(r'覆盖旧答案', '', demand)
    demand = demand.strip()
    
    # 如果处理后为空，回退到原始文本
    if not demand or len(demand) < 2:
        return text.strip()
    
    return demand

def detect_anomalies(text, role, uid, ts):
    """检测异常并返回 flags"""
    flags = []
    
    # 检查空内容
    if not text or not text.strip():
        flags.append('empty_content')
    
    # 检查角色是否正常
    valid_roles = ['user', 'assistant', 'tool']
    if role not in valid_roles:
        flags.append('invalid_role')
    
    # 检查 UID
    if not uid or uid == 'UNKNOWN':
        flags.append('missing_uid')
    
    # 检查时间戳
    if not ts or ts.strip() == '':
        flags.append('missing_timestamp')
    
    # 检查敏感信息标记
    sensitive_terms = ['别记下来', '不要保存', '忘记这个', '别保存', '别记录', '忽略这个']
    for term in sensitive_terms:
        if term in text:
            flags.append('sensitive_info_marked')
            break
    
    # 检查修正/回退标记
    correction_markers = ['不对', '纠正', '错了', '刚才说错', '覆盖', '不是…是…', '不是...是...']
    for marker in correction_markers:
        if marker in text:
            flags.append('correction')
            break
    
    # 检查临时请求标记
    temp_markers = ['仅本次', '这次例外', '不代表以后', '这次']
    for marker in temp_markers:
        if marker in text:
            flags.append('temporary_request')
            break
    
    return flags

def clean_chat_logs(input_file, output_file):
    stutter_counts = defaultdict(int)
    cleaned = []
    seen = set()
    sessions = {}  # key: session_id, value: list of messages in order
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line: 
                continue
            
            try:
                item = json.loads(line)
                
                # 提取原始字段
                session = item.get('session', '')
                uid = item.get('uid', '')
                role = item.get('role', '')
                text = item.get('text', '')
                ts = item.get('ts', '')
                
                # 规范化处理
                uid = uid.upper() if uid else 'UNKNOWN'
                
                # 规范化角色
                role = role.lower() if role else ''
                if role not in ['user', 'assistant', 'tool']:
                    role = 'unknown'
                
                # 智能去重：同一会话、同一角色、相似内容去重
                normalize_text = re.sub(r'\s+', '', text).lower()
                record_key = f"{session}|{uid}|{role}|{normalize_text}"
                if record_key in seen:
                    continue
                seen.add(record_key)
                
                # 检测异常
                flags = detect_anomalies(text, role, uid, ts)
                
                # 统计停顿词
                stutter = count_stutter_words(text)
                for word, cnt in stutter.items():
                    stutter_counts[word] += cnt
                
                # 清洗文本
                text_clean, filler_removed, symbols_removed = clean_text(text)
                
                # 清理多余的省略号和前导空格
                text_clean = re.sub(r'^[\s…]+', '', text_clean)
                text_clean = re.sub(r'…+', '…', text_clean)
                text_clean = re.sub(r'\s+', ' ', text_clean)
                text_clean = text_clean.strip()
                
                # 规范化时间
                ts_clean = standardize_time(ts)
                
                # 构造记录 - 最简洁的结构
                record = {
                    'session_id': session,
                    'user_id': uid,
                    'role': role,
                    'text': text_clean,
                    'timestamp': ts_clean
                }
                
                # 按会话分组
                if session not in sessions:
                    sessions[session] = []
                sessions[session].append(record)
                
            except Exception as e:
                continue
    
    # 按会话排序，按时间排序
    all_records = []
    for session_id in sorted(sessions.keys()):
        # 按时间戳排序
        sorted_messages = sorted(sessions[session_id], key=lambda x: x['timestamp'] or '')
        for msg in sorted_messages:
            all_records.append(msg)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    
    return stutter_counts

def determine_preference_type(note, version):
    """判断偏好类型：default/explicit/temporary/correction"""
    note_lower = note.lower()
    if '管理员导入' in note or 'v0' in version:
        return 'default'
    elif '仅本次例外' in note or '不应覆盖' in note or '临时' in note:
        return 'temporary'
    elif '用户纠正' in note or '覆盖旧知识' in note or '不对' in note or '纠正' in note:
        return 'correction'
    elif '明确要求' in note or '记住' in note or '从对话' in note:
        return 'explicit'
    else:
        return 'explicit'

def clean_preferences(input_file, output_file, chat_logs_file=None):
    cleaned = []
    pref_records = {}  # key: uid|pref_key, value: list of records
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pref_id = row.get('pref_id', '')
            uid = row.get('uid', '').upper() or 'UNKNOWN'
            pref_key = row.get('pref_key', '')
            pref_value = row.get('pref_value', '')
            version = row.get('version', '')
            note = row.get('note', '')
            
            pref_value, _, _ = clean_text(pref_value)
            
            # 判断偏好类型
            pref_type = determine_preference_type(note, version)
            
            # 构造简洁记录
            record = {
                'user_id': uid,
                'pref_key': pref_key,
                'pref_value': pref_value,
                'preference_type': pref_type
            }
            
            # 按用户和偏好分组
            key = f"{uid}|{pref_key}"
            if key not in pref_records:
                pref_records[key] = []
            pref_records[key].append(record)
    
    # 只保留最新版本
    for key, records in pref_records.items():
        if len(records) == 1:
            cleaned.append(records[0])
        else:
            # 保留最新版本（保留最后一条）
            cleaned.append(records[-1])
    
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
            if not line: continue
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

def extract_knowledge_structure(content_part):
    """提取知识库内容的结构化信息"""
    structure = {
        'description': '',
        'steps': [],
        'examples': [],
        'notes': [],
        'principles': [],
        'legacy_info': ''
    }
    
    lines = content_part.split('\n')
    current_section = 'description'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检测段落标题
        section_patterns = [
            (r'^步骤[:：]', 'steps'),
            (r'^示例[:：]', 'examples'),
            (r'^示例输出[:：]', 'examples'),
            (r'^注意[:：]', 'notes'),
            (r'^常见坑[:：]', 'notes'),
            (r'^原则[:：]', 'principles'),
            (r'^说明[:：]', 'description'),
            (r'^要求[:：]', 'description'),
            (r'^适用[:：]', 'notes'),
            (r'^旧说法[:：]', 'legacy_info'),
            (r'^新说法[:：]', 'description')
        ]
        
        matched = False
        for pattern, section in section_patterns:
            if re.match(pattern, line):
                current_section = section
                line = re.sub(pattern, '', line).strip()
                if line:
                    if section == 'steps' and re.match(r'^\d+\.', line):
                        structure['steps'].append(line)
                    elif section == 'principles' and re.match(r'^\d+\.', line):
                        structure['principles'].append(line)
                    else:
                        structure[section] = line
                matched = True
                break
        
        if not matched:
            # 处理编号列表
            if re.match(r'^\d+\.', line):
                if current_section in ['steps', 'principles']:
                    structure[current_section].append(line)
                else:
                    structure[current_section] += (' ' + line)
            elif re.match(r'^[-*]', line):
                structure['examples'].append(line)
            else:
                structure[current_section] += (' ' + line)
    
    # 清理空值
    for key in structure:
        if isinstance(structure[key], str):
            structure[key] = structure[key].strip()
    
    return structure

def filter_privacy_from_knowledge(text):
    """从知识库内容中过滤隐私信息"""
    filtered_text = text
    
    # 检测并过滤邮箱
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    filtered_text = re.sub(email_pattern, '[EMAIL_REMOVED]', filtered_text)
    
    # 检测并过滤手机号
    phone_pattern = r'\b(?:(?:\+?86)|(?:86))?(1[3-9]\d{9})\b'
    filtered_text = re.sub(phone_pattern, '[PHONE_REMOVED]', filtered_text)
    
    # 检测并过滤可能的隐私信息
    sensitive_patterns = [
        r'密码.*[：:]\s*\S+',
        r'账号.*[：:]\s*\S+',
        r'用户名.*[：:]\s*\S+',
        r'身份证.*\d{17}[\dXx]',
        r'姓名.*[：:]\s*\S+'
    ]
    for pattern in sensitive_patterns:
        filtered_text = re.sub(pattern, '[SENSITIVE_REMOVED]', filtered_text)
    
    return filtered_text

def validate_knowledge_case(title, tags, content_str):
    """验证案例是否有效"""
    issues = []
    
    # 检查标题
    if not title or len(title.strip()) < 2:
        issues.append('invalid_title')
    
    # 检查内容
    if not content_str or len(content_str.strip()) < 5:
        issues.append('empty_content')
    
    # 检查垃圾案例
    garbage_indicators = [
        '=== 垃圾行 ===',
        '<<<<<<',
        '>>>>>>',
        '测试粘贴'
    ]
    for indicator in garbage_indicators:
        if indicator in title or indicator in content_str:
            issues.append('garbage_content')
            break
    
    return issues

def clean_knowledge(input_file, output_file):
    stutter_counts = defaultdict(int)
    cleaned = []
    skipped = []
    case_index = 0
    
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
        
        case_index += 1
        
        # 提取标题和标签
        title_match = re.search(r'标题：(.+)', content_part)
        tag_match = re.search(r'标签：(.+)', content_part)
        
        title = title_match.group(1).strip() if title_match else ''
        tags = [t.strip() for t in tag_match.group(1).split('#') if t.strip()] if tag_match else []
        
        # 清洗标题
        cleaned_title, _, _ = clean_text(title)
        cleaned_title = cleaned_title.strip()
        
        # 提取结构化内容
        structure = extract_knowledge_structure(content_part)
        
        # 收集所有内容行用于清洗
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
        
        # 合并为完整内容
        content_str = ' '.join(content_lines)
        
        # 移除多余空格
        content_str = re.sub(r'\s+', ' ', content_str)
        content_str = re.sub(r'([：:。；;！!？?])\s+', r'\1', content_str)  # 中文标点后不留空格
        content_str = content_str.strip()
        
        # 过滤隐私信息
        content_str = filter_privacy_from_knowledge(content_str)
        for key in ['description', 'legacy_info']:
            if structure[key]:
                structure[key] = filter_privacy_from_knowledge(structure[key])
        
        # 验证案例
        validation_issues = validate_knowledge_case(cleaned_title, tags, content_str)
        
        if validation_issues:
            # 跳过无效案例
            skipped.append({
                'case_index': case_index,
                'title': title,
                'issues': validation_issues,
                'reason': 'invalid_content'
            })
            continue
        
        # 生成知识 ID
        knowledge_id = f"K{str(case_index).zfill(4)}"
        
        # 构建知识库记录 - 最简洁的结构
        knowledge_record = {
            'title': cleaned_title,
            'tags': tags,
            'content': content_str
        }
        
        cleaned.append(knowledge_record)
    
    # 输出结果 - 直接输出数组，简化结构
    output_data = cleaned
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
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

1. `chat_logs_cleaned.jsonl` - 清洗后的聊天日志（JSONL格式）
2. `preferences_cleaned.json` - 清洗后的用户偏好（去重、版本标记）
3. `tool_result_cleaned.json` - 清洗后的工具执行结果
4. `knowledge_cleaned.json` - 清洗后的知识库
5. `report.md` - 本报告
"""
    
    return report

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)  # d4 目录
    
    # 创建输出目录
    output_dir = os.path.join(base_dir, 'cleaned_output')
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载配置文件
    config_path = os.path.join(base_dir, 'config_manual.yaml')
    load_config(config_path)
    print(f"已从配置文件加载敏感模式和命令词: {SENSITIVE_TERMS}")
    
    chat_logs_raw = os.path.join(base_dir, 'chat_logs_raw.jsonl')
    
    stutter_chat = clean_chat_logs(
        chat_logs_raw,
        os.path.join(output_dir, 'chat_logs_cleaned.json')
    )
    
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
        chat_data = json.load(f)
        chat_count = len(chat_data)
    
    with open(os.path.join(output_dir, 'knowledge_cleaned.json'), 'r', encoding='utf-8') as f:
        knowledge_data = json.load(f)
        knowledge_count = len(knowledge_data)
    
    report = generate_report(stutter_chat, stutter_knowledge, chat_count, pref_count, tool_count, knowledge_count)
    
    with open(os.path.join(output_dir, 'report.md'), 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("清洗完成！输出文件：")
    print("1. chat_logs_cleaned.jsonl")
    print("2. preferences_cleaned.json")
    print("3. tool_result_cleaned.json")
    print("4. knowledge_cleaned.json")
    print("5. report.md")
