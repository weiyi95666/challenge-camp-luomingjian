<template>
  <div class="app" :class="{ 'dark-theme': isDarkMode }">
    <!-- 头部标题 -->
    <header class="app-header">
      <div class="header-left">
        <div class="logo">
          <BotIcon :size="24" />
        </div>
        <div class="title-group">
          <h1 class="app-title">AI 编程小助手</h1>
          <span class="status-badge" :class="{ 'online': !connectionError }">
            {{ connectionError ? '已离线' : '在线' }}
          </span>
        </div>
      </div>
      
      <div class="header-actions">
        <button class="icon-button" @click="toggleDarkMode" :title="isDarkMode ? '切换日间模式' : '切换夜间模式'">
          <SunIcon v-if="isDarkMode" :size="20" />
          <MoonIcon v-else :size="20" />
        </button>
        <button class="icon-button" @click="confirmClearChat" title="清空聊天记录">
          <Trash2Icon :size="20" />
        </button>
      </div>
    </header>

    <div class="main-container">
      <!-- 侧边栏：历史会话 -->
      <aside class="sidebar" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
        <div class="sidebar-header">
          <button class="new-chat-btn" @click="createNewChat">
            <PlusIcon :size="18" />
            <span>开启新对话</span>
          </button>
        </div>
        
        <div class="chat-history">
          <div 
            v-for="chat in chatHistory" 
            :key="chat.id"
            class="history-item"
            :class="{ 'active': currentChatId === chat.id }"
            @click="switchChat(chat.id)"
          >
            <MessageSquareIcon :size="16" />
            <span class="history-title">{{ chat.title }}</span>
          </div>
        </div>

        <div class="sidebar-footer">
          <button class="action-btn data-workbench-btn" @click="showDataWorkbench = true">
            <DatabaseIcon :size="18" />
            <span>数据清洗工作台</span>
          </button>
        </div>
      </aside>

      <!-- 数据清洗工作台模态框 -->
      <div v-if="showDataWorkbench" class="modal-overlay" @click.self="showDataWorkbench = false">
        <div class="data-workbench-modal">
          <div class="modal-header">
            <h3>📊 工业级数据清洗工作台</h3>
            <button class="close-btn" @click="showDataWorkbench = false"><XIcon :size="20" /></button>
          </div>
          <div class="modal-body">
            <div 
              class="drop-zone" 
              @dragover.prevent="dragOver = true" 
              @dragleave.prevent="dragOver = false"
              @drop.prevent="handleDrop"
              :class="{ 'drag-over': dragOver }"
            >
              <div class="drop-content">
                <UploadCloudIcon :size="48" />
                <p>将文件或文件夹拖拽至此，立即触发自动清洗</p>
                <span>支持 CSV, TXT, JSONL, XLSX, DOCX</span>
              </div>
              <input type="file" ref="fileInput" @change="handleFileSelect" multiple hidden />
              <button class="select-btn" @click="$refs.fileInput.click()">选择文件</button>
            </div>
            
            <div v-if="isProcessing" class="processing-status">
              <LoaderIcon class="spinner" :size="20" />
              <span>正在执行全自动清洗流水线...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 主聊天区域 -->
      <main class="chat-container">
        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesContainer">
          <div v-if="messages.length === 0" class="welcome-section">
            <div class="welcome-card">
              <div class="welcome-icon">🚀</div>
              <h2>你好！我是你的 AI 编程助手</h2>
              <p>我可以帮你解决各种技术难题、优化代码或准备面试。</p>
              
              <div class="suggestion-grid">
                <div v-for="sug in suggestions" :key="sug" class="suggestion-item" @click="sendMessage(sug)">
                  {{ sug }}
                </div>
              </div>
            </div>
          </div>

          <!-- 历史消息 -->
          <ChatMessage
            v-for="message in messages"
            :key="message.id"
            :message="message.content"
            :image="message.image"
            :is-user="message.isUser"
            :timestamp="message.timestamp"
          />

          <!-- AI 正在回复的消息 -->
          <div v-if="isAiTyping" class="chat-message ai-message streaming-message">
            <div class="message-avatar">
              <div class="avatar-container ai-avatar">
                <BotIcon :size="20" />
              </div>
            </div>
            <div class="message-content">
              <div class="message-bubble">
                <div class="ai-typing-content">
                  <div class="ai-response-text message-markdown hljs" v-html="currentAiResponseRendered"></div>
                  <div v-if="isStreaming" class="typing-indicator">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入框 -->
        <ChatInput
          :disabled="isAiTyping && !isStreaming"
          :is-typing="isAiTyping"
          @send-message="sendMessage"
          @stop-generation="stopGeneration"
          placeholder="在这里输入你的编程问题..."
        />
      </main>
    </div>

    <!-- 错误通知 -->
    <transition name="fade">
      <div v-if="connectionError" class="error-toast">
        <AlertCircleIcon :size="18" />
        <span>无法连接到服务器，请确保后端服务已启动。</span>
      </div>
    </transition>
  </div>
</template>

<script>
import ChatMessage from './components/ChatMessage.vue'
import ChatInput from './components/ChatInput.vue'
import { chatWithSSE, chatWithMultimodal } from './api/chatApi.js'
import { generateMemoryId, renderMarkdown } from './utils/index.js'
import { 
  Bot as BotIcon, 
  Sun as SunIcon, 
  Moon as MoonIcon, 
  Trash2 as Trash2Icon, 
  AlertCircle as AlertCircleIcon, 
  Plus as PlusIcon, 
  MessageSquare as MessageSquareIcon, 
  Database as DatabaseIcon, 
  X as XIcon, 
  UploadCloud as UploadCloudIcon, 
  Loader as LoaderIcon, 
  Menu as MenuIcon
} from '@lucide/vue'

export default {
  name: 'App',
  components: {
    ChatMessage,
    ChatInput,
    BotIcon,
    SunIcon,
    MoonIcon,
    Trash2Icon,
    AlertCircleIcon,
    PlusIcon,
    MessageSquareIcon,
    DatabaseIcon,
    XIcon,
    UploadCloudIcon,
    LoaderIcon,
    MenuIcon
  },
  data() {
    return {
      messages: [],
      memoryId: null,
      isAiTyping: false,
      isStreaming: false,
      currentAiResponse: '',
      currentEventSource: null,
      connectionError: false,
      isDarkMode: false,
      isSidebarCollapsed: false,
      chatHistory: [
        { id: 1, title: '如何学习 Java？' },
        { id: 2, title: 'Spring Boot 自动装配' }
      ],
      currentChatId: null,
      suggestions: [
        '帮我清洗一下我上传的文件',
        '如何学习 Java 并发编程？',
        '请解释一下 Spring Boot 的自动装配原理',
        '帮我写一个快速排序算法'
      ],
      showDataWorkbench: false,
      dragOver: false,
      isProcessing: false
    }
  },
  computed: {
    currentAiResponseRendered() {
      return renderMarkdown(this.currentAiResponse || '正在思考中...')
    }
  },
  methods: {
    createNewChat() {
      this.messages = []
      this.currentChatId = null
      this.initializeChat()
    },
    switchChat(chatId) {
      this.currentChatId = chatId
    },
    handleDrop(event) {
      this.dragOver = false
      const files = Array.from(event.dataTransfer.files)
      if (files.length > 0) {
        this.processWorkbenchFiles(files)
      }
    },
    handleFileSelect(event) {
      const files = Array.from(event.target.files)
      if (files.length > 0) {
        this.processWorkbenchFiles(files)
      }
    },
    async processWorkbenchFiles(files) {
      this.isProcessing = true
      this.showDataWorkbench = false
      
      // 添加一条用户消息表示正在通过工作台处理
      const fileNames = files.map(f => f.name).join(', ')
      this.addMessage(`【工作台】丢入文件进行自动清洗: ${fileNames}`, true, files)
      
      // 发送静默指令给 AI
      this.startAiResponse("请立即扫描 outputs 目录并执行全自动清洗，仅汇报处理日志。", files)
      this.isProcessing = false
    },
    toggleDarkMode() {
      this.isDarkMode = !this.isDarkMode
      document.body.classList.toggle('dark-mode', this.isDarkMode)
    },
    
    sendMessage(messageData) {
      let text = ''
      let files = []
      
      if (typeof messageData === 'string') {
        text = messageData
      } else {
        text = messageData.text
        files = messageData.files || []
      }

      if (!text.trim() && files.length === 0) return
      
      // 添加用户消息（显示所有上传的文件）
      this.addMessage(text, true, files)
      
      // 开始AI回复
      this.startAiResponse(text, files)
    },
    
    addMessage(content, isUser = false, files = []) {
      const message = {
        id: Date.now() + Math.random(),
        content,
        isUser,
        files: [...files],
        timestamp: new Date()
      }
      this.messages.push(message)
      this.scrollToBottom()
    },
    
    startAiResponse(userMessage, files = []) {
      this.isAiTyping = true
      this.isStreaming = true
      this.currentAiResponse = ''
      this.connectionError = false
      
      // 开始多模态连接
      this.currentEventSource = chatWithMultimodal(
        this.memoryId,
        userMessage,
        files,
        this.handleAiMessage,
        this.handleAiError,
        this.handleAiClose
      )
    },
    
    handleAiMessage(data) {
      this.currentAiResponse += data
      this.scrollToBottom()
    },
    
    handleAiError(error) {
      console.error('AI 回复出错:', error)
      // 只有在完全没有收到回复内容时，才显示连接错误提示
      if (!this.currentAiResponse.trim()) {
        this.connectionError = true
        setTimeout(() => {
          this.connectionError = false
        }, 5000)
      }
      this.finishAiResponse()
    },
    
    handleAiClose() {
      this.finishAiResponse()
    },
    
    stopGeneration() {
      if (this.currentEventSource) {
        this.currentEventSource.close()
        this.finishAiResponse()
      }
    },
    
    finishAiResponse() {
      this.isStreaming = false
      
      if (this.currentAiResponse.trim()) {
        this.addMessage(this.currentAiResponse.trim(), false)
      }
      
      this.isAiTyping = false
      this.currentAiResponse = ''
      
      if (this.currentEventSource) {
        this.currentEventSource.close()
        this.currentEventSource = null
      }
    },
    
    confirmClearChat() {
      if (confirm('确定要清空所有聊天记录吗？')) {
        this.messages = []
        this.initializeChat()
      }
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
          })
        }
      })
    },
    
    initializeChat() {
      this.memoryId = generateMemoryId()
    }
  },
  
  mounted() {
    this.initializeChat()
    // 检查系统深色模式偏好
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      this.toggleDarkMode()
    }
  }
}
</script>

<style>
/* 全局样式 */
:root {
  --bg-app: #f7fafc;
  --bg-header: #ffffff;
  --text-main: #2d3748;
  --text-muted: #718096;
  --primary: #3182ce;
  --border-color: #edf2f7;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}

body.dark-mode {
  --bg-app: #1a202c;
  --bg-header: #2d3748;
  --text-main: #f7fafc;
  --text-muted: #a0aec0;
  --primary: #63b3ed;
  --border-color: #4a5568;
}

.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-app);
  color: var(--text-main);
  transition: background-color 0.3s;
}

.app-header {
  background-color: var(--bg-header);
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  width: 32px;
  height: 32px;
  background-color: var(--primary);
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.title-group {
  display: flex;
  flex-direction: column;
}

.app-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
}

.status-badge {
  font-size: 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-muted);
}

.status-badge::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #cbd5e0;
}

.status-badge.online::before {
  background-color: #48bb78;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.icon-button {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.icon-button:hover {
  background-color: var(--border-color);
  color: var(--text-main);
}

.main-container {
  display: flex;
  height: calc(100vh - 64px);
  overflow: hidden;
}

.sidebar {
  width: 260px;
  background-color: #f8fafc;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
}

.sidebar-header {
  padding: 16px;
}

.new-chat-btn {
  width: 100%;
  padding: 10px;
  background-color: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
  color: #475569;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.history-item {
  padding: 10px 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: #64748b;
  margin-bottom: 4px;
}

.history-item.active {
  background-color: #f1f5f9;
  color: #2563eb;
}

.history-title {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e2e8f0;
}

.data-workbench-btn {
  width: 100%;
  padding: 12px;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 600;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.data-workbench-modal {
  width: 500px;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.modal-header {
  padding: 16px 20px;
  background-color: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-body {
  padding: 24px;
}

.drop-zone {
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.drop-zone.drag-over {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

.drop-content {
  color: #64748b;
  margin-bottom: 20px;
}

.drop-content p {
  font-weight: 600;
  margin: 12px 0 4px;
}

.drop-content span {
  font-size: 12px;
}

.select-btn {
  padding: 8px 24px;
  background-color: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
}

.processing-status {
  margin-top: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #3b82f6;
  font-weight: 500;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  max-width: none;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
}

/* 欢迎区域 */
.welcome-section {
  display: flex;
  justify-content: center;
  padding: 40px 20px;
}

.welcome-card {
  background-color: var(--bg-header);
  border-radius: 20px;
  padding: 32px;
  text-align: center;
  max-width: 500px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--border-color);
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.welcome-card h2 {
  font-size: 22px;
  margin: 0 0 12px;
}

.welcome-card p {
  color: var(--text-muted);
  line-height: 1.6;
  margin-bottom: 24px;
}

.suggestion-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.suggestion-item {
  padding: 12px;
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.suggestion-item:hover {
  border-color: var(--primary);
  color: var(--primary);
  transform: translateY(-2px);
}

/* AI 回复动画 */
.streaming-message .message-bubble {
  border-left: 3px solid var(--primary);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator .dot {
  width: 6px;
  height: 6px;
  background-color: var(--text-muted);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator .dot:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); }
}

/* 错误通知 */
.error-toast {
  position: fixed;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #e53e3e;
  color: white;
  padding: 12px 20px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 12px rgba(229, 62, 62, 0.3);
  z-index: 100;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translate(-50%, 20px);
}

/* 滚动条 */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-thumb {
  background-color: var(--border-color);
  border-radius: 3px;
}

@media (max-width: 768px) {
  .suggestion-grid {
    grid-template-columns: 1fr;
  }
  
  .welcome-card {
    padding: 24px 16px;
  }
}
</style> 