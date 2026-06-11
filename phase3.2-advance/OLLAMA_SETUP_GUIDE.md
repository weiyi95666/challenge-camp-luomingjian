# Ollama 本地模型配置指南

## 快速开始

### 1. 安装 Ollama

访问 [Ollama 官网](https://ollama.com) 下载并安装适合你操作系统的版本。

### 2. 拉取模型

打开终端/命令行，运行以下命令拉取模型：

```bash
# 推荐使用 gemma2:2b（轻量但够用）
ollama pull gemma2:2b

# 或者你喜欢的其他模型
ollama pull qwen2:7b
ollama pull llama3.1:8b
```

### 3. 验证 Ollama 运行

```bash
# 检查 Ollama 是否在运行
ollama list

# 测试模型
ollama run gemma2:2b
```

### 4. 更新配置

编辑 `src/main/resources/application.yml`，将模型名称改为你拉取的模型：

```yaml
ollama:
  base-url: http://localhost:11434
  model-name: gemma2:2b  # 改成你实际拉取的模型
  timeout-seconds: 60
  enabled: true
```

### 5. 重启后端

修改配置后，重启后端服务。

## 常见问题

### Ollama 连接失败

确保 Ollama 服务正在运行：
```bash
# Windows
ollama serve

# Mac/Linux
ollama serve
```

### 模型不存在

运行 `ollama list` 查看已安装的模型，确保 `application.yml` 中的模型名称与实际一致。

## 推荐模型

| 模型 | 大小 | 速度 | 质量 |
|------|------|------|------|
| gemma2:2b | 1.6GB | ⚡⚡⚡ | ⭐⭐⭐ |
| qwen2:7b | 4.5GB | ⚡⚡ | ⭐⭐⭐⭐ |
| llama3.1:8b | 4.7GB | ⚡⚡ | ⭐⭐⭐⭐ |
