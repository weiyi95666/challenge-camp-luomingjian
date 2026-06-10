# Git 使用笔记

## 基本操作

### 初始化仓库
```bash
git init
```

### 配置用户信息
```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 添加远程仓库
```bash
git remote add origin https://github.com/weiyi95666/challenge-camp-luomingjian.git
```

### 查看状态
```bash
git status
```

### 添加文件
```bash
git add .              # 添加所有文件
git add 文件名         # 添加指定文件
```

### 提交更改
```bash
git commit -m "提交说明"
```

### 推送到远程
```bash
git push origin main
```

### 拉取更新
```bash
git pull origin main
```

## 常用命令

### 查看提交历史
```bash
git log
git log --oneline  # 简洁格式
```

### 撤销修改
```bash
git checkout -- 文件名    # 撤销工作区修改
git reset HEAD 文件名     # 撤销暂存区
```

### 分支操作
```bash
git branch              # 查看分支
git branch 分支名        # 创建分支
git checkout 分支名      # 切换分支
git merge 分支名         # 合并分支
```

## 解决冲突

### 远程仓库有新内容
```bash
git pull origin main --rebase
# 手动解决冲突后
git add .
git rebase --continue
```

### 强制推送（谨慎使用）
```bash
git push origin main --force
```

## 本项目结构
```
d4/
├── pipeline/          # 清洗脚本
│   └── run.py
├── cleaned_output/    # 清洗输出
├── *.jsonl           # 原始数据
├── *.csv             # 原始数据
├── config_manual.yaml # 配置文件
└── encrypt_pii.py    # 加密脚本
```