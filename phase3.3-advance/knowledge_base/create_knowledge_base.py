#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据清洗知识库构建脚本
使用 Milvus Lite 和 sentence-transformers
"""

import os
import sys
import json
import hashlib
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient, FieldSchema, CollectionSchema, DataType, Collection

# 配置
MILVUS_DB_PATH = "./milvus.db"
COLLECTION_NAME = "data_cleaning_knowledge"
MODEL_NAME = "shibing624/text2vec-base-chinese"
# 也可以使用: "all-MiniLM-L6-v2"

# 预定义的高质量数据清洗知识文档
KNOWLEDGE_DOCUMENTS = [
    # === 缺失值处理 ===
    {
        "id": "001",
        "title": "缺失值删除法",
        "category": "缺失值处理",
        "content": """
缺失值删除法是最直接的缺失值处理方法，包括删除法适用于缺失值较少且随机分布的情况。

适用场景：
- 缺失值比例低（<5%），且删除后数据量仍足够；- 缺失值无明显模式；- 缺失值特征对分析影响不大的列。

方法：
1. 行删除：直接删除包含缺失值的行
2. 列删除：删除缺失值过多的列（>30%）
3. 条件删除：按特定条件删除缺失值。

代码示例：
```python
import pandas as pd

# 行删除 - 删除任何包含 NaN 的行
df_clean = df.dropna()

# 列删除 - 删除缺失值超过 30% 的列
threshold = len(df) * 0.7
df_clean = df.dropna(axis=1, thresh=threshold)

# 条件删除 - 删除特定列缺失的行
df_clean = df.dropna(subset=['important_column'])
```

注意事项：
- 删除可能导致信息丢失，影响模型性能
- 可能引入样本偏差
- 不要过度使用会降低统计推断能力
- 记录删除前后统计
""",
        "tags": ["缺失值", "数据预处理", "数据清洗"]
    },
    {
        "id": "002",
        "title": "均值/中位数/众数填充",
        "category": "缺失值处理",
        "content": """
均值/中位数/众数填充是最简单的缺失值填充方法。

适用场景：
- 数值型数据：均值填充（正态分布）或中位数填充（偏态分布）
- 分类数据：众数填充
- 缺失值模式简单且无明显模式的情况。

代码示例：
```python
import pandas as pd
import numpy as np

# 均值填充
df['age'].fillna(df['age'].mean(), inplace=True)

# 中位数填充（更稳健，对异常值不敏感）
df['income'].fillna(df['income'].median(), inplace=True)

# 众数填充（分类变量）
df['category'].fillna(df['category'].mode()[0], inplace=True)
```

注意事项：
- 均值填充可能引入误差，特别是异常值影响
- 中位数更稳健，但信息丢失
- 可能降低方差，导致 underestimation
- 建议分位数填充前先分析分布形态
""",
        "tags": ["缺失值填充", "统计学", "数据清洗"]
    },
    {
        "id": "003",
        "title": "KNN 缺失值填充",
        "category": "缺失值处理",
        "content": """
KNN（K近邻）填充法通过找到与缺失值样本最相似的 K 个样本，用它们的值来填充。

适用场景：
- 特征之间有强相关性
- 样本量适中
- 数据为数值型或可向量化

算法原理：
- 计算样本间距离（欧氏/曼哈顿/余弦）
- 找到 K 个最近邻
- 用加权平均填充

代码示例：
```python
import pandas as pd
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler

# 标准化数据
scaler = StandardScaler()
scaled_df = scaler.fit_transform(df.select_dtypes(include=[np.number]))

# KNN 填充
imputer = KNNImputer(n_neighbors=5)
imputed_data = imputer.fit_transform(scaled_df)
df_imputed = pd.DataFrame(
    imputed_data,
    columns=df.select_dtypes(include=[np.number]).columns
)
```

注意事项：
- K 值选择很重要（推荐 3-10
- 计算成本高
- 对距离计算敏感
- 计算开销大
- 需要先归一化
""",
        "tags": ["机器学习", "缺失值", "KNN", "数据清洗"]
    },
    
    # === 重复数据检测 ===
    {
        "id": "004",
        "title": "精确去重",
        "category": "重复数据处理",
        "content": """
精确去重是删除完全相同的重复行。

适用场景：
- 完全重复的记录
- 数据录入错误
- 数据合并产生重复

代码示例：
```python
import pandas as pd

# 检查重复行
duplicates = df.duplicated()
print(f'发现 {duplicates.sum()} 行重复')

# 删除重复行，保留第一条
df_clean = df.drop_duplicates()

# 基于特定列去重
df_clean = df.drop_duplicates(subset=['user_id', 'order_id'], keep='first')
```

注意事项：
- 决定保留哪一条（first/last）
- 检查业务规则可能包含重要信息差异
- 重复数据可能有业务意义（如重复下单
""",
        "tags": ["去重", "数据清洗"]
    },
    {
        "id": "005",
        "title": "模糊去重（相似度匹配）",
        "category": "重复数据处理",
        "content": """
模糊去重用于处理近似重复的记录，通过文本相似度检测。

适用场景：
- 名称/地址/描述等文本字段
- 拼写错误
- OCR识别错误
- 格式不一致

方法：
- 字符串相似度（Levenshtein、Jaro-Winkler
- 文本向量化 + 聚类
- 哈希方法

代码示例：
```python
import pandas as pd
from fuzzywuzzy import fuzz, process

def find_duplicates_by_similarity(df, column, threshold=90):
    candidates = []
    values = df[column].dropna().unique()
    
    for i, val1 in enumerate(values):
        matches = process.extract(val1, values[i+1:], limit=5)
        for match, score in matches:
            if score >= threshold:
                candidates.append((val1, match, score))
    return candidates

# 找到相似项
duplicates = find_duplicates_by_similarity(df, 'company_name', threshold=85)
```

注意事项：
- 阈值选择要平衡召回率和精确率
- 需人工验证高风险字段
- 根据实际业务调整策略
""",
        "tags": ["模糊匹配", "相似度", "去重"]
    },
    
    # === 异常值检测 ===
    {
        "id": "006",
        "title": "Z-score 异常值检测",
        "category": "异常值处理",
        "content": """
Z-score 方法通过计算数据点与均值的距离判断是否异常值。

适用场景：
- 数据近似正态分布
- 单变量异常值检测

Z-score = (X - μ) / σ
- Z-score > 3 或 < -3

代码示例：
```python
import pandas as pd
import numpy as np
from scipy import stats

# 计算 Z-score
z_scores = np.abs(stats.zscore(df['price']))

# 标记异常值
threshold = 3
outliers = df[z_scores > threshold]
print(f'发现 {len(outliers)} 个异常值')

# 处理异常值（删除或替换
df_clean = df[z_scores <= threshold]

# 或用中位数替换
median = df['price'].median()
df.loc[z_scores > threshold, 'price'] = median
```

注意事项：
- 敏感异常值阈值通常用稳健统计方法
- 影响正态分布假设
- 不适用于偏态数据
- 可考虑中位数绝对偏差替代方法
""",
        "tags": ["统计", "异常值", "Z-score"]
    },
    {
        "id": "007",
        "title": "IQR 箱线图异常值检测",
        "category": "异常值处理",
        "content": """
IQR（四分位距）方法使用四分位数检测异常值，更稳健。

适用场景：
- 偏态分布数据
- 对异常值不敏感

方法：
- Q1：第25百分位数
- Q3：第75百分位数
- IQR = Q3 - Q1
- 异常值范围：< Q1 - 1.5 * IQR 或 > Q3 + 1.5 * IQR

代码示例：
```python
import pandas as pd
import numpy as np

def detect_outliers_iqr(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    
    outliers = df[(df[column] < lower) | (df[column] > upper)]
    return outliers

outliers = detect_outliers_iqr(df, 'salary')

# 处理异常值
df_clean = df[(df['salary'] >= lower) & (df['salary'] <= upper)]
```

注意事项：
- IQR 乘以系数可以根据情况调整（1.5为标准，3极度异常
- 适合偏态分布
- 更稳健，受极值影响小
""",
        "tags": ["异常值", "IQR", "统计方法"]
    },
    
    # === 数据类型转换 ===
    {
        "id": "008",
        "title": "字符串到数字类型转换",
        "category": "数据类型转换",
        "content": """
字符串到数字转换处理是数据清洗中常见的操作。

适用场景：
- 包含货币符号、千位分隔符、百分比等脏数据
- 格式不统一
- 有异常值

常见问题：
- ¥1,234.56 → 1234.56
- 50% → 0.5
- 1,000 → 1000

代码示例：
```python
import pandas as pd
import numpy as np

# 基本转换
df['price'] = pd.to_numeric(df['price'], errors='coerce')

# 处理特殊字符
def clean_currency(value):
    if pd.isna(value):
        return np.nan
    value = str(value).strip()
    if '$¥', '').replace(',', '')
    return float(value) if value else np.nan

df['price_clean'] = df['price'].apply(clean_currency)
df['percentage'] = df['percentage'].str.rstrip('%').astype(float) / 100
```

注意事项：
- 使用 coerce 参数将无法转换的设为 NaN
- 记录转换失败的样本
- 检查转换后统计验证
""",
        "tags": ["数据类型", "字符串", "转换"]
    },
    {
        "id": "009",
        "title": "日期格式转换与标准化",
        "category": "数据类型转换",
        "content": """
日期格式统一处理多种格式的日期数据。

适用场景：
- 日期格式混乱（2023-01、01/2023、2023年1月1日等
- 时间戳需要转换
- 时区问题

代码示例：
```python
import pandas as pd
from datetime import datetime

# 自动推断日期
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# 指定格式解析
df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')

# 处理 Unix 时间戳
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

# 标准化输出
df['date_standard'] = df['date'].dt.strftime('%Y-%m-%d')
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
```

注意事项：
- pd.to_datetime 功能强大但需谨慎
- 统一时区问题
- 处理时区转换（pytz / zoneinfo）
- 保存为字符串存为 datetime64[ns] 类型
""",
        "tags": ["日期", "时间", "数据类型"]
    },
    
    # === 文本清洗 ===
    {
        "id": "010",
        "title": "文本基础清洗（去空格、统一大小写）",
        "category": "文本清洗",
        "content": """
基础文本清洗处理文本数据中的常见问题。

适用场景：
- 空格过多
- 大小写混乱
- 前后空格

代码示例：
```python
import pandas as pd
import re

def clean_text(text):
    if pd.isna(text):
        return ''
    text = str(text)
    # 去除前后空格
    text = text.strip()
    # 多个空格替换
    text = re.sub(r'\s+', ' ', text)
    # 统一小写（可选
    text = text.lower()
    return text

df['name_clean'] = df['name'].apply(clean_text)
```

进阶：
```python
# 去除特殊字符
df['text'] = df['text'].str.replace(r'[^\w\s]', '', regex=True)
```

注意事项：
- 根据业务需求选择方法
- 中文文本注意全角/半角
""",
        "tags": ["文本", "清洗", "预处理"]
    },
    {
        "id": "011",
        "title": "繁简转换与中文文本清洗",
        "category": "中文文本预处理",
        "content": """
中文文本需要专门的处理方法。

适用场景：
- 繁体简体混合
- 全角半角混乱
- 特殊符号

代码示例：
```python
import pandas as pd
import opencc

# 使用 OpenCC 转换
converter = opencc.OpenCC('t2s.json')  # 繁体转简体
df['text_simplified'] = df['text'].apply(lambda x: converter.convert(x) if pd.notna(x) else x)

# 全角转半角
def full2half(s):
    if pd.isna(s):
        return s
    s = str(s)
    res = []
    for char in s:
        code = ord(char)
        if 65281 <= code <= 65374:
            res.append(chr(code - 65248))
        elif code == 12288:
            res.append(chr(32))
        else:
            res.append(char)
    return ''.join(res)

df['text'] = df['text'].apply(full2half)
```

注意事项：
- 繁简体转换可能有误
- 人名地名等专有名词
- 根据具体场景选择工具
- 可考虑使用 HanLP、jieba 等工具
""",
        "tags": ["中文", "文本", "NLP"]
    },
    {
        "id": "012",
        "title": "正则表达式文本替换",
        "category": "文本清洗",
        "content": """
正则表达式强大的文本模式匹配和替换。

适用场景：
- 替换特定模式
- 提取信息
- 标准化

常用正则模式：
- 邮箱替换
- 手机号
- URL

代码示例：
```python
import pandas as pd
import re

def clean_with_regex(text):
    if pd.isna(text):
        return text
    
    # 去除 URL
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # 去除电话
    text = re.sub(r'\d{3}[-\s]?\d{4}[-\s]?\d{4}', '[PHONE]', text)
    # 去除邮箱
    text = re.sub(r'\S+@\S+\.\S+', '[EMAIL]', text)
    
    return text

df['text_clean'] = df['text'].apply(clean_with_regex)
```

正则速查：
- . 任意字符
- \d 数字
- \s 空白
- \w 单词字符
- * 0+
- + 1+
- ? 0或1
- {n,m} n到m次
- ^开始
- $结尾
""",
        "tags": ["正则", "文本", "模式匹配"]
    },
    
    # === 敏感信息 ===
    {
        "id": "013",
        "title": "手机号脱敏",
        "category": "敏感信息处理",
        "content": """
手机号脱敏保护用户隐私，符合GDPR等合规要求。

适用场景：
- 用户数据保护
- 数据导出
- 数据共享

方法：
- 替换中间位（如 138****1234

代码示例：
```python
import pandas as pd
import re

def mask_phone(phone):
    if pd.isna(phone):
        return phone
    phone = str(phone)
    # 匹配 11位手机号
    if re.match(r'^1[3-9]\d{9}$', phone):
        return phone[:3] + '****' + phone[7:])
    return phone

df['phone_masked'] = df['phone'].apply(mask_phone)
```

其他方式：
- 全部脱敏：***********
- 哈希加密：不可逆 SHA-256
- 仅保留后4位：****1234
""",
        "tags": ["脱敏", "隐私", "数据保护"]
    },
    {
        "id": "014",
        "title": "身份证号脱敏",
        "category": "敏感信息处理",
        "content": """
身份证号敏感信息处理。

适用场景：
- 个人信息保护
- 合规要求
- 数据脱敏标准

方法：
- 中间8位脱敏
- 出生日期脱敏
- 校验码保留或脱敏示例代码：
```python
import pandas as pd
import re

def mask_id_card(id_number):
    if pd.isna(id_number):
        return id_number
    id_str = str(id_number)
    if len(id_str) == 18:
        # 18位身份证
        return id_str[:6] + '********' + id_str[-4:]
    elif len(id_str) == 15:
        # 15位身份证
        return id_str[:6] + '******' + id_str[-3:]
    return id_number

df['id_masked'] = df['id_card'].apply(mask_id_card)
```

其他：
- 加密存储：AES加密存储
- 哈希：SHA-256，可加
- 假名化：替换为假数据
""",
        "tags": ["身份证", "脱敏", "数据安全"]
    },
    
    # === 数据标准化 ===
    {
        "id": "015",
        "title": "Min-Max 归一化",
        "category": "数据标准化",
        "content": """
Min-Max 归一化将数据缩放到[0,1]范围。

适用场景：
- 特征尺度差异大
- 神经网络
- 距离计算

公式：
X_normalized = (X - X_min) / (X_max - X_min)

代码示例：
```python
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# 使用 sklearn
scaler = MinMaxScaler()
df_scaled = scaler.fit_transform(df[['age', 'income']])

# 手动实现
def min_max_normalize(series):
    return (series - series.min()) / (series.max() - series.min())

df['age_normalized'] = min_max_normalize(df['age']))
```

注意事项：
- 对异常值非常敏感
- 受 max/min值变化
- 新数据需要重新计算
- 建议先处理异常值
""",
        "tags": ["归一化", "特征工程", "机器学习"]
    },
    {
        "id": "016",
        "title": "Z-score 标准化",
        "category": "数据标准化",
        "content": """
Z-score 标准化（Standardization）将数据转换为标准正态分布。

适用场景：
- 算法假设正态分布
- 异常值相对较少
- 比较不同单位特征

公式：
Z = (X - μ) / σ

代码示例：
```python
import pandas as pd
from sklearn.preprocessing import StandardScaler

# 使用 sklearn
scaler = StandardScaler()
df_scaled = scaler.fit_transform(df[['age', 'income']]))

# 手动
df['age_zscore'] = (df['age'] - df['age'].mean()) / df['age'].std()
```

注意事项：
- 均值为0，标准差为1
- 不改变分布
- 异常值影响
- 非正态分布数据需谨慎
""",
        "tags": ["标准化", "特征工程", "机器学习"]
    },
    
    # === 最佳实践 ===
    {
        "id": "017",
        "title": "数据清洗最佳实践流程",
        "category": "数据清洗流程",
        "content": """
系统化的数据清洗流程最佳实践。

推荐步骤：
1. 数据探索与理解：
- 基本统计 info(), describe()
- 可视化分析
- 缺失值统计
- 异常值检测

2. 制定计划：
- 按步骤文档记录
- 备份原始数据
- 确定清洗策略

3. 分块处理（大数据）：
- 分批处理
- 内存优化
- 并行处理

4. 验证与监控：
- 检查统计
- 完整性检查
- 业务规则验证
- 可视化对比

代码示例：
```python
import pandas as pd

def data_cleaning_pipeline(df):
    # 0. 备份
    df_original = df.copy()
    
    # 1. 探索
    print('=== 原始数据 ===')
    print(df.info())
    print(df.describe())
    
    # 2. 处理缺失值
    df['age'].fillna(df['age'].median(), inplace=True)
    df.dropna(subset=['email'], inplace=True)
    
    # 3. 去重
    df.drop_duplicates(inplace=True)
    
    # 4. 处理异常值
    Q1 = df['price'].quantile(0.25)
    Q3 = df['price'].quantile(0.75)
    IQR = Q3 - Q1
    df = df[(df['price'] >= Q1 - 1.5 * IQR) & 
               (df['price'] <= Q3 + 1.5 * IQR))]
    
    # 5. 保存清洗前后对比
    
    return df
```

注意事项：
- 不要覆盖原数据
- 详细日志
- 版本控制
- 可复现
""",
        "tags": ["最佳实践", "流程", "方法论"]
    },
    {
        "id": "018",
        "title": "编码问题处理（UTF-8 BOM）",
        "category": "编码问题",
        "content": """
编码问题是文本数据中常见的问题。

常见问题：
- UTF-8 BOM 头
- GBK/GB2312 与 UTF-8 混淆
- chardet 检测
- 乱码恢复

代码示例：
```python
import pandas as pd
import chardet

# 检测编码
with open('data.csv', 'rb') as f:
    raw_data = f.read(10000)  # 读取样本
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    confidence = result['confidence']
    print(f'检测编码: {encoding} (置信度: {confidence:.2f}')

# 读取带 BOM 的 UTF-8
df = pd.read_csv('data.csv', encoding='utf-8-sig')

# 或者移除 BOM
with open('data.csv', 'rb') as f:
    content = f.read()
if content.startswith(b'\xef\xbb\xbf'):
    content = content[3:]

# 保存时指定编码
df.to_csv('clean_data.csv', encoding='utf-8-sig', index=False)
```

常见编码：
- utf-8-sig：UTF-8 with BOM
- gbk / gb2312 / gb18030：中文
- big5：繁体
- latin1 / iso-8859-1
""",
        "tags": ["编码", "字符", "数据"]
    },
    {
        "id": "019",
        "title": "DBSCAN 密度聚类异常值检测",
        "category": "异常值处理",
        "content": """
DBSCAN 基于密度的聚类算法，可用于多维异常值检测。

适用场景：
- 多维数据异常值
- 异常簇形状
- 聚类问题

代码示例：
```python
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

# 标准化
scaler = StandardScaler()
X = scaler.fit_transform(df[['feature1', 'feature2', 'feature3']])

# DBSCAN
dbscan = DBSCAN(eps=0.5, min_samples=5)
labels = dbscan.fit_predict(X)

# -1 表示异常值
df['cluster'] = labels
outliers = df[df['cluster'] == -1]
print(f'发现 {len(outliers)} 个异常值')
```

参数调整：
- eps：邻域半径
- min_samples：核心点样本数
- metric：距离计算方法
""",
        "tags": ["机器学习", "聚类", "异常值", "DBSCAN"]
    },
    {
        "id": "020",
        "title": "停用词去除（文本清洗）",
        "category": "文本清洗",
        "content": """
停用词去除是NLP预处理的重要步骤，去除无意义词汇。

适用场景：
- 文本分析前处理
- 关键词提取
- 文本相似度

方法：
- 中文常用停用词表（哈工大、百度等
- TF-IDF筛选
- 词频过滤

代码示例：
```python
import pandas as pd
import jieba
import re

# 加载停用词
def load_stopwords(filepath='stopwords.txt'):
    with open(filepath, 'r', encoding='utf-8') as f:
        return set([line.strip() for line in f])

stopwords = load_stopwords()

def remove_stopwords(text):
    if pd.isna(text):
        return ''
    # 分词
    words = jieba.lcut(str(text))
    # 去除停用词
    words = [w for w in words if w not in stopwords and w.strip() != '']
    return ' '.join(words)

df['text_clean'] = df['text'].apply(remove_stopwords)
```

注意事项：
- 停用词表
- 专业领域
- 去除标点符号
- 与具体业务场景
""",
        "tags": ["停用词", "NLP", "文本", "中文分词"]
    },
    {
        "id": "021",
        "title": "插值法缺失值填充",
        "category": "缺失值处理",
        "content": """
插值法利用数据点之间插值填充缺失值，适用于时间序列数据。

适用场景：
- 时间序列数据
- 空间数据
- 有序序列

方法：
- 线性插值
- 多项式插值
- 样条插值
- 前向/后向填充

代码示例：
```python
import pandas as pd
import numpy as np

# 线性插值
df['value_interpolated'] = df['value'].interpolate(method='linear')

# 时间序列插值
df['date'] = pd.to_datetime(df['date']))
df.set_index('date', inplace=True)
df['value_interpolated'] = df['value'].interpolate(method='time')

# 前向填充 (ffill)
df['value_ffill'] = df['value'].fillna(method='ffill')
# 后向填充 (bfill)
df['value_bfill'] = df['value'].fillna(method='bfill')
```

注意事项：
- 线性插值：适合趋势数据
- 时间索引 interpolation
- 不要过度使用
- 检查插值对业务
""",
        "tags": ["插值", "时间序列", "缺失值"]
    },
    {
        "id": "022",
        "title": "数据清洗分块处理（大数据）",
        "category": "数据清洗流程",
        "content": """
大数据集分块处理策略避免内存不足。

适用场景：
- 文件大于内存
- 分批处理
- 流式处理

方法：
- pandas 分块读取
- Dask
- PySpark
- 数据库查询分批处理

代码示例：
```python
import pandas as pd

# pandas 分块读取
chunk_size = 10_000
chunks = []
for chunk in pd.read_csv('large_data.csv', chunksize=chunk_size):
    # 清洗每一块
    chunk_clean = clean_chunk(chunk)
    chunks.append(chunk_clean)
    
# 合并处理
df_final = pd.concat(chunks, ignore_index=True)

# 使用 Dask
import dask.dataframe as dd
dask_df = dd.read_csv('large_data.csv')
dask_df_clean = clean_dask(dask_df)
df_final = dask_df_clean.compute()
```

注意事项：
- 分块大小
- 跨块统计
- 内存监控
- 中间结果保存
- 并行处理加速
""",
        "tags": ["大数据", "分块", "内存优化"]
    },
    {
        "id": "023",
        "title": "数据清洗日志记录",
        "category": "数据清洗流程",
        "content": """
数据清洗日志记录可复现和审计追踪。

日志内容：
- 处理时间
- 操作类型
- 影响行数
- 前后统计
- 原因说明

代码示例：
```python
import pandas as pd
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleaning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_cleaning_operation(operation, before, after, reason=''):
    diff = before - after
    logger.info(f"[{operation}] 前:{before} -> 后:{after} | 影响:{diff} | {reason}")

# 使用
initial_count = len(df)
df_clean = df.drop_duplicates()
log_cleaning_operation('去重', initial_count, len(df_clean), '去除重复行')
```

推荐记录内容：
- 删除的原因
- 替换策略
- 参数配置
- 版本信息
""",
        "tags": ["日志", "审计", "可复现"]
    },
    {
        "id": "024",
        "title": "数据分箱（数据类型",
        "category": "特征工程",
        "content": """
数据分箱将连续数据离散化，提高模型稳定性。

适用场景：
- 连续变量离散化
- 减少异常值影响
- 非线性关系建模

方法：
- 等宽分箱
- 等频分箱
- 自定义分箱
- K-Means分箱
- 决策树分箱

代码示例：
```python
import pandas as pd
import numpy as np

# 等宽分箱
df['age_binned'] = pd.cut(df['age'], bins=5, labels=['0-18', '19-30', '31-45', '46-60', '60+'])

# 等频分箱
df['income_binned'] = pd.qcut(df['income'], q=4, labels=['低收入', '中低收入', '中高收入', '高收入'])

# 自定义分箱
bins = [0, 1000, 5000, 20000, np.inf]
labels = ['低', '中', '高', '极高']
df['price_binned'] = pd.cut(df['price'], bins=bins, labels=labels, include_lowest=True)
```

注意事项：
- 分箱数量选择
- 业务意义
- WOE / IV分箱
- 决策树分箱更优
""",
        "tags": ["分箱", "特征工程", "离散化"]
    },
    {
        "id": "025",
        "title": "邮箱地址标准化",
        "category": "数据清洗",
        "content": """
邮箱清洗和标准化统一邮箱格式。

适用场景：
- 用户注册邮箱
- 联系信息
- 重复邮箱检测

方法：
- 统一小写
- 去除空格
- 验证格式
- 去除别名（+号部分）

代码示例：
```python
import pandas as pd
import re

def clean_email(email):
    if pd.isna(email):
        return email
    email = str(email).strip().lower()
    
    # 去除 + 号部分
    if '+' in email:
        local, domain = email.split('@', 1)
        local = local.split('+')[0]
        email = local + '@' + domain
    
    # 验证格式
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email
    return None  # 无效邮箱

df['email_clean'] = df['email'].apply(clean_email)
```

常见问题：
- 大小写不一致
- 别名变体
- 临时邮箱
- 拼写错误（gmail.com 等）
""",
        "tags": ["邮箱", "字符串", "验证"]
    }
]

def create_knowledge_base():
    """创建知识库并插入数据"""
    print("=" * 60)
    print("数据清洗知识库构建")
    print("=" * 60)
    
    # 1. 连接 Milvus Lite
    print(f"\n[1/4 连接 Milvus Lite: {MILVUS_DB_PATH}")
    client = MilvusClient(MILVUS_DB_PATH)
    
    # 2. 删除已存在的 collection
    if client.has_collection(COLLECTION_NAME):
        print(f"删除已存在的 collection: {COLLECTION_NAME}")
        client.drop_collection(COLLECTION_NAME)
    
    # 3. 创建字段
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=50, is_primary=True),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),  # all-MiniLM-L6-v2
        # shibing624/text2vec-base-chinese: 768
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=500),
    ]
    
    # 4. 创建 schema
    schema = CollectionSchema(fields=fields, description="数据清洗知识集合")
    
    # 5. 创建 collection
    print(f"[2/4 创建 collection: {COLLECTION_NAME}")
    client.create_collection(collection_name=COLLECTION_NAME, schema=schema)
    
    # 6. 加载模型
    print(f"[3/4 加载嵌入模型: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    
    # 7. 准备数据
    print(f"[4/4 插入 {len(KNOWLEDGE_DOCUMENTS)} 条知识")
    
    # 格式化文档
    texts = []
    ids = []
    titles = []
    categories = []
    tags_list = []
    
    for doc in KNOWLEDGE_DOCUMENTS:
        full_text = f"标题: {doc['title']}\n分类: {doc['category']}\n内容: {doc['content']}"
        texts.append(full_text)
        ids.append(doc['id'])
        titles.append(doc['title'])
        categories.append(doc['category'])
        tags_list.append(','.join(doc['tags']))
    
    # 生成向量
    print("正在生成嵌入向量...")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # 插入数据
    data = [
        ids,
        texts,
        embeddings.tolist(),
        titles,
        categories,
        tags_list
    ]
    
    insert_result = client.insert(collection_name=COLLECTION_NAME, data=data)
    print(f"✓ 成功插入 {len(insert_result['insert_count'])} 条记录")
    
    # 创建索引
    print("\n创建索引...")
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }
    client.create_index(
        collection_name=COLLECTION_NAME,
        index_name="vector_index",
        field_name="embedding",
        index_params=index_params
    )
    
    print("\n" + "=" * 60)
    print("知识库构建完成！")
    print("=" * 60)
    print(f"总记录数: {len(KNOWLEDGE_DOCUMENTS)}")
    print(f"collection: {COLLECTION_NAME}")
    print(f"模型: {MODEL_NAME}")
    print("\n使用 search_knowledge.py 进行搜索")
    print("=" * 60)
    
    return client

if __name__ == "__main__":
    create_knowledge_base()
