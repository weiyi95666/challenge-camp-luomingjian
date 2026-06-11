# 故障排查指南

## 🔍 问题：为什么模型不回答？

### 常见原因

#### 1. Ollama 未启动或未安装
**解决方案：**
```bash
# 检查 Ollama 是否运行
ollama list

# 如果没安装，下载安装：https://ollama.ai/download

# 启动 Ollama 服务
ollama serve
```

#### 2. 模型未下载
**解决方案：**
```bash
# 下载一个模型（推荐 gemma2:2b，轻量且快速）
ollama pull gemma2:2b

# 或者下载更大的模型
ollama pull gemma4:e2b
```

#### 3. application.yml 配置问题
检查 `src/main/resources/application.yml`：
```yaml
ollama:
  base-url: http://localhost:11434  # 确保地址正确
  model-name: gemma2:2b              # 确保模型名正确
  timeout-seconds: 60                # 增加超时时间
  enabled: true                      # 必须设为 true！
```

#### 4. 端口被占用
确保 11434 端口没有被其他程序占用。

---

## ✅ 当前修复内容

我已经修复了以下问题：

1. **改进了 fallback 响应** - 即使没有 Ollama，也能提供有意义的聊天响应
2. **智能识别** - 区分数据清洗请求和普通聊天请求
3. **深度思考模式支持** - 在没有 Ollama 时也能模拟深度思考效果

---

## 🚀 推荐快速开始（无需 Ollama）

即使没有 Ollama，你也可以：
- ✅ 测试完整的聊天界面
- ✅ 测试数据清洗功能
- ✅ 体验对话历史管理
- ✅ 看到模拟的深度思考过程

---

## 📝 完整的 Ollama 安装步骤

### Windows:
1. 访问 https://ollama.ai/download
2. 下载并安装
3. 打开 PowerShell，运行：
   ```bash
   ollama pull gemma2:2b
   ```

### Mac:
```bash
# 使用 Homebrew
brew install ollama
ollama pull gemma2:2b
```

### Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma2:2b
```

---

## 🔧 测试连接

启动后端后，查看日志应该看到：
```
Initialized Ollama client with model: gemma2:2b
```

如果看到：
```
Ollama is disabled, using fallback strategies only
```

说明 `ollama.enabled` 还是 `false`，需要改为 `true` 并重启。

---

## 💡 提示

- **gemma2:2b** 是轻量级模型，推荐用于开发测试
- **gemma4:e2b** 更大更强，但需要更多资源
- 首次响应可能较慢，需要加载模型
