import json
import csv
import re
import os
import hashlib
import base64

# 正则表达式匹配
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_PATTERN = re.compile(r'1[3-9]\d{9}')

# 简单的加密函数（使用 AES 的简化版本，纯 Python 实现）
def simple_encrypt(data: str, key: str) -> str:
    """使用 XOR 和哈希进行简单加密"""
    key_hash = hashlib.sha256(key.encode()).digest()
    data_bytes = data.encode('utf-8')
    
    # XOR 加密
    encrypted = bytearray()
    for i, byte in enumerate(data_bytes):
        encrypted.append(byte ^ key_hash[i % len(key_hash)])
    
    return base64.urlsafe_b64encode(encrypted).decode()

# 替换文本中的敏感信息
def encrypt_sensitive_info(text: str, key: str) -> str:
    # 加密邮箱
    for email in EMAIL_PATTERN.findall(text):
        encrypted_email = simple_encrypt(email, key)
        text = text.replace(email, f"[ENCRYPTED_EMAIL:{encrypted_email}]")
    
    # 加密手机号
    for phone in PHONE_PATTERN.findall(text):
        encrypted_phone = simple_encrypt(phone, key)
        text = text.replace(phone, f"[ENCRYPTED_PHONE:{encrypted_phone}]")
    
    return text

# 处理 chat_logs_cleaned.jsonl
def encrypt_chat_logs(input_file, output_file, key):
    encrypted_lines = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                item['text'] = encrypt_sensitive_info(item['text'], key)
                encrypted_lines.append(json.dumps(item, ensure_ascii=False))
            except Exception as e:
                encrypted_lines.append(line)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(encrypted_lines) + '\n')
    
    print(f"加密完成: {input_file} -> {output_file}")

# 处理 tool_result_cleaned.json
def encrypt_tool_results(input_file, output_file, key):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for item in data:
        item['output'] = encrypt_sensitive_info(item['output'], key)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"加密完成: {input_file} -> {output_file}")

# 处理 knowledge_cleaned.json
def encrypt_knowledge(input_file, output_file, key):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for item in data:
        item['title'] = encrypt_sensitive_info(item['title'], key)
        item['content'] = encrypt_sensitive_info(item['content'], key)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"加密完成: {input_file} -> {output_file}")

# 处理 preferences_cleaned.json
def encrypt_preferences(input_file, output_file, key):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for item in data:
        item['pref_value'] = encrypt_sensitive_info(item['pref_value'], key)
        item['note'] = encrypt_sensitive_info(item['note'], key)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"加密完成: {input_file} -> {output_file}")

# 处理 knowledge_raw.txt
def encrypt_knowledge_raw(input_file, output_file, key):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = encrypt_sensitive_info(content, key)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"加密完成: {input_file} -> {output_file}")

# 处理 preferences_raw.csv
def encrypt_preferences_raw(input_file, output_file, key):
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        rows = []
        for row in reader:
            for key_name in row:
                if isinstance(row[key_name], str):
                    row[key_name] = encrypt_sensitive_info(row[key_name], key)
            rows.append(row)
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"加密完成: {input_file} -> {output_file}")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 加密密钥（实际使用时应从安全位置读取）
    ENCRYPTION_KEY = 'student-camp-encryption-key-2026'
    
    print("=" * 60)
    print("开始对敏感信息（邮箱、手机号）进行加密")
    print("加密方式: XOR + SHA256 哈希")
    print("=" * 60)
    
    # 加密各个文件
    encrypt_chat_logs(
        os.path.join(script_dir, 'chat_logs_cleaned.jsonl'),
        os.path.join(script_dir, 'chat_logs_encrypted.jsonl'),
        ENCRYPTION_KEY
    )
    
    encrypt_tool_results(
        os.path.join(script_dir, 'tool_result_cleaned.json'),
        os.path.join(script_dir, 'tool_result_encrypted.json'),
        ENCRYPTION_KEY
    )
    
    encrypt_knowledge(
        os.path.join(script_dir, 'knowledge_cleaned.json'),
        os.path.join(script_dir, 'knowledge_encrypted.json'),
        ENCRYPTION_KEY
    )
    
    encrypt_preferences(
        os.path.join(script_dir, 'preferences_cleaned.json'),
        os.path.join(script_dir, 'preferences_encrypted.json'),
        ENCRYPTION_KEY
    )
    
    encrypt_knowledge_raw(
        os.path.join(script_dir, 'knowledge_raw.txt'),
        os.path.join(script_dir, 'knowledge_encrypted.txt'),
        ENCRYPTION_KEY
    )
    
    encrypt_preferences_raw(
        os.path.join(script_dir, 'preferences_raw.csv'),
        os.path.join(script_dir, 'preferences_encrypted.csv'),
        ENCRYPTION_KEY
    )
    
    print("=" * 60)
    print("加密完成！")
    print(f"加密密钥: {ENCRYPTION_KEY}")
    print("解密时需要使用相同的密钥")
    print("=" * 60)
