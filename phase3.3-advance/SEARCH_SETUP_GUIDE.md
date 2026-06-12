# 🔍 联网搜索功能设置指南

## 📋 概述

已将搜索功能从 DuckDuckGo 切换到 **Brave Search API**，更稳定、成功率更高！

## 🚀 快速开始

### 1️⃣ 获取 Brave Search API Key

1. 访问：https://brave.com/search/api/
2. 注册账号（免费）
3. 获取免费 API Key（每月 2000 次请求）

### 2️⃣ 配置环境变量

#### 方式一：设置系统环境变量（推荐）

**Windows:**
```powershell
# 临时设置（当前终端有效）
set BRAVE_API_KEY=your_actual_api_key

# 永久设置
[Environment]::SetEnvironmentVariable("BRAVE_API_KEY", "your_actual_api_key", "User")
```

**Linux/Mac:**
```bash
export BRAVE_API_KEY=your_actual_api_key
```

#### 方式二：创建 .env 文件

在项目根目录创建 `.env` 文件：
```env
BRAVE_API_KEY=your_actual_api_key
```

### 3️⃣ 启动应用

启动后端服务后，会看到：
```
✅ Brave Search API initialized
```

## 📁 文件变更

| 文件 | 说明 |
|------|------|
| `src/main/java/.../BraveSearchService.java` | 新的搜索服务实现 |
| `src/main/java/.../SearchService.java` | 重构，优先使用 Brave Search |
| `src/main/resources/application.yml` | 添加 Brave Search 配置 |
| `.env.example` | 环境变量示例 |

## 🧪 验证功能

### 方式一：使用测试脚本

```javascript
// 测试搜索功能
const response = await fetch('http://localhost:8080/api/chat/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: '2024年奥运会在哪里举办？',
        webSearchEnabled: true
    })
});
```

### 方式二：使用前端 UI

1. 打开 http://localhost:3000
2. 开启"🔍 联网搜索"开关
3. 发送搜索问题

## ⚙️ 配置说明

### application.yml

```yaml
brave:
    search:
        api-key: ${BRAVE_API_KEY:}
```

- `BRAVE_API_KEY`：从环境变量读取
- 不硬编码，安全！

### 搜索特性

✅ **自动跳过简单问题**：问候语、问时间等不会触发搜索  
✅ **智能 Fallback**：没有 API Key 或超时时使用兜底  
✅ **2秒超时**：快速响应，不阻塞聊天  
✅ **最多5条结果**：减少 token 消耗  

## 🔧 故障排查

### 问题：提示"Brave Search not available"

**原因：** 没有配置 API Key

**解决：** 设置 `BRAVE_API_KEY` 环境变量

### 问题：搜索超时

**原因：** 网络问题或 API 限流

**解决：** 系统会自动使用 Fallback 结果

### 问题：如何确认正在使用 Brave Search？

**查看后端日志：**
```
✅ Brave Search API initialized
🔍 Using Brave Search for: your query
✅ Found X results from Brave Search
```

## 📊 费用说明

| 方案 | 价格 | 限制 |
|------|------|------|
| 免费版 | $0 | 2000 次/月 |
| 付费版 | $3/1000次 | 无限量 |

## 💡 使用建议

1. **开发阶段**：可以先不用 API Key，使用 Fallback 结果
2. **生产环境**：务必配置 API Key
3. **监控用量**：每月检查 API 使用量

## 🎯 下一步

1. [ ] 申请 Brave Search API Key
2. [ ] 配置环境变量
3. [ ] 重启后端服务
4. [ ] 测试搜索功能

---
有问题？查看日志！📖
