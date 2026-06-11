<template>
  <div class="app-container">
    <!-- Sidebar: Conversation History -->
    <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="createNewConversation">
          <span class="icon">+</span>
          <span class="text" v-if="!sidebarCollapsed">新对话</span>
        </button>
        <button class="toggle-sidebar-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          {{ sidebarCollapsed ? '→' : '←' }}
        </button>
      </div>

      <div class="conversation-list">
        <div 
          v-for="conv in conversations" 
          :key="conv.id"
          :class="['conversation-item', { active: currentConversationId === conv.id }]"
          @click="selectConversation(conv.id)"
        >
          <span class="conv-icon">💬</span>
          <span class="conv-title" v-if="!sidebarCollapsed">{{ conv.title }}</span>
          <div class="conv-actions" v-if="!sidebarCollapsed && currentConversationId === conv.id">
            <button class="icon-btn" @click.stop="startRename(conv)" title="重命名">✏️</button>
            <button class="icon-btn" @click.stop="deleteConversation(conv.id)" title="删除">🗑️</button>
          </div>
        </div>
      </div>

      <!-- Rename Dialog -->
      <div v-if="renamingConversation" class="rename-dialog-overlay" @click.self="cancelRename">
        <div class="rename-dialog">
          <h3>重命名对话</h3>
          <input 
            v-model="newConversationTitle" 
            @keyup.enter="confirmRename"
            placeholder="输入新标题"
          />
          <div class="dialog-actions">
            <button @click="cancelRename" class="btn-secondary">取消</button>
            <button @click="confirmRename" class="btn-primary">确认</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Tabs: Chat vs Data Cleaning -->
      <div class="tabs-header">
        <button 
          :class="['tab-btn', { active: activeTab === 'chat' }]"
          @click="activeTab = 'chat'"
        >
          智能对话
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'cleaning' }]"
          @click="activeTab = 'cleaning'"
        >
          数据清洗
        </button>
      </div>

      <!-- Chat Tab Content -->
      <div v-if="activeTab === 'chat'" class="chat-tab">
        <!-- Chat Messages -->
        <div class="chat-messages" ref="chatMessagesRef">
          <!-- Welcome message -->
          <div v-if="messages.length === 0" class="welcome-section">
            <div class="welcome-icon">🤖</div>
            <h1>智能数据助手</h1>
            <p>我可以帮你：</p>
            <div class="welcome-features">
              <div class="feature-card">💬 回答问题和咨询</div>
              <div class="feature-card">📊 分析和清洗数据</div>
              <div class="feature-card">🔍 联网搜索资讯</div>
            </div>
          </div>

          <!-- Messages -->
          <div v-for="msg in messages" :key="msg.id" :class="['message', msg.role]">
            <div class="message-avatar">
              {{ msg.role === 'user' ? '👤' : '🤖' }}
            </div>
            <div class="message-content">
              <!-- Thinking process (for deep thinking mode) -->
              <div v-if="msg.thinkingProcess" class="thinking-section">
                <div class="thinking-toggle" @click="toggleThinking(msg.id)">
                  <span class="thinking-label">🧠 思考过程</span>
                  <span class="toggle-icon">{{ expandedThinking[msg.id] ? '▼' : '▶' }}</span>
                </div>
                <div v-if="expandedThinking[msg.id]" class="thinking-content" v-html="renderMarkdown(msg.thinkingProcess)"></div>
              </div>

              <!-- Message content -->
              <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
            </div>
          </div>

          <!-- Loading indicator -->
          <div v-if="isGenerating" class="message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Chat Input -->
        <div class="chat-input-area">
          <!-- Mode controls -->
          <div class="input-controls">
            <div class="mode-toggle-group">
              <button 
                :class="['mode-btn', { active: !deepThinkingMode }]"
                @click="deepThinkingMode = false"
                title="快速回答"
              >
                ⚡ 快速
              </button>
              <button 
                :class="['mode-btn', { active: deepThinkingMode }]"
                @click="deepThinkingMode = true"
                title="深度思考"
              >
                🧠 深度
              </button>
            </div>
            
            <div class="toggle-control">
              <label :class="['toggle-switch', { active: webSearchEnabled }]" @click="webSearchEnabled = !webSearchEnabled">
                <span class="toggle-track"></span>
                <span class="toggle-thumb"></span>
              </label>
              <span class="toggle-label">🔍 联网搜索</span>
            </div>

            <button class="attach-btn" @click="triggerFileUpload" title="上传文件">
              📎
            </button>
          </div>

          <!-- File preview (if any) -->
          <div v-if="attachedFile" class="attached-file-preview">
            <span class="file-icon">📄</span>
            <span class="file-name">{{ attachedFile.name }}</span>
            <button class="remove-file" @click="removeAttachedFile">✕</button>
          </div>

          <!-- Text input -->
          <div class="input-wrapper">
            <textarea 
              v-model="userInput"
              @keydown="handleKeydown"
              placeholder="输入你的问题..."
              rows="1"
              ref="textareaRef"
            ></textarea>
            <button class="send-btn" @click="sendMessage" :disabled="!userInput.trim() || isGenerating">
              {{ isGenerating ? '...' : '发送' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Data Cleaning Tab Content -->
      <div v-if="activeTab === 'cleaning'" class="cleaning-tab">
        <DataCleaningView />
      </div>
    </div>

    <!-- Hidden file input -->
    <input 
      type="file" 
      ref="fileInputRef" 
      style="display: none" 
      @change="handleFileSelect"
      accept=".csv,.xlsx,.xls,.txt,.json"
    />
  </div>
</template>

<script>
import axios from 'axios'
import { marked } from 'marked'
import DataCleaningView from './components/DataCleaningView.vue'

export default {
  name: 'App',
  components: { DataCleaningView },
  data() {
    return {
      // UI state
      activeTab: 'chat',
      sidebarCollapsed: false,
      
      // Conversations
      conversations: [],
      currentConversationId: null,
      renamingConversation: null,
      newConversationTitle: '',
      
      // Chat state
      messages: [],
      userInput: '',
      isGenerating: false,
      deepThinkingMode: false,
      webSearchEnabled: false,
      expandedThinking: {},
      
      // Files
      attachedFile: null,
    }
  },
  mounted() {
    this.loadConversations()
  },
  methods: {
    // ==================== Conversation Management ====================
    async loadConversations() {
      try {
        const response = await axios.get('/api/chat/conversations')
        this.conversations = response.data
      } catch (err) {
        console.error('Failed to load conversations:', err)
      }
    },

    createNewConversation() {
      this.currentConversationId = null
      this.messages = []
      this.userInput = ''
    },

    async selectConversation(id) {
      if (this.currentConversationId === id) return
      
      this.currentConversationId = id
      
      try {
        const response = await axios.get(`/api/chat/conversations/${id}`)
        this.messages = response.data.messages || []
      } catch (err) {
        console.error('Failed to load conversation:', err)
      }
    },

    startRename(conv) {
      this.renamingConversation = conv
      this.newConversationTitle = conv.title
    },

    cancelRename() {
      this.renamingConversation = null
      this.newConversationTitle = ''
    },

    async confirmRename() {
      if (!this.renamingConversation || !this.newConversationTitle.trim()) return
      
      try {
        await axios.put(`/api/chat/conversations/${this.renamingConversation.id}`, {
          title: this.newConversationTitle
        })
        this.renamingConversation.title = this.newConversationTitle
      } catch (err) {
        console.error('Failed to rename conversation:', err)
      }
      
      this.cancelRename()
    },

    async deleteConversation(id) {
      if (!confirm('确定要删除这个对话吗？')) return
      
      try {
        await axios.delete(`/api/chat/conversations/${id}`)
        this.conversations = this.conversations.filter(c => c.id !== id)
        if (this.currentConversationId === id) {
          this.createNewConversation()
        }
      } catch (err) {
        console.error('Failed to delete conversation:', err)
      }
    },

    // ==================== Chat ====================
    renderMarkdown(text) {
      if (!text) return ''
      return marked.parse(text, { breaks: true, gfm: true })
    },

    toggleThinking(msgId) {
      this.$set(this.expandedThinking, msgId, !this.expandedThinking[msgId])
    },

    handleKeydown(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        this.sendMessage()
      }
    },

    async sendMessage() {
      if (!this.userInput.trim() || this.isGenerating) return

      const userMsg = {
        id: Date.now().toString(),
        role: 'user',
        content: this.userInput,
        timestamp: new Date()
      }
      this.messages.push(userMsg)
      const inputText = this.userInput
      this.userInput = ''
      
      this.isGenerating = true
      this.scrollToBottom()

      try {
        const response = await axios.post('/api/chat/send', {
          conversationId: this.currentConversationId,
          message: inputText,
          deepThinking: this.deepThinkingMode,
          webSearchEnabled: this.webSearchEnabled
        })

        const { conversationId, message } = response.data
        
        if (!this.currentConversationId) {
          this.currentConversationId = conversationId
          await this.loadConversations()
        }
        
        this.messages.push({
          id: message.id,
          role: message.role,
          content: message.content,
          thinkingProcess: message.thinkingProcess
        })

      } catch (err) {
        console.error('Failed to send message:', err)
        this.messages.push({
          id: Date.now().toString(),
          role: 'assistant',
          content: '抱歉，发生了错误，请稍后再试。'
        })
      } finally {
        this.isGenerating = false
        this.scrollToBottom()
      }
    },

    scrollToBottom() {
      this.$nextTick(() => {
        if (this.$refs.chatMessagesRef) {
          this.$refs.chatMessagesRef.scrollTop = this.$refs.chatMessagesRef.scrollHeight
        }
      })
    },

    // ==================== File Upload ====================
    triggerFileUpload() {
      this.$refs.fileInputRef.click()
    },

    async handleFileSelect(e) {
      const file = e.target.files[0]
      if (!file) return
      
      this.attachedFile = file
      e.target.value = ''
      
      try {
        const formData = new FormData()
        formData.append('file', file)
        const response = await axios.post('/api/chat/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        console.log('File uploaded:', response.data)
      } catch (err) {
        console.error('Failed to upload file:', err)
      }
    },

    removeAttachedFile() {
      this.attachedFile = null
    }
  }
}
</script>

<style scoped>
/* 全局重置，确保没有溢出 */
* {
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}

.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 280px;
  flex-shrink: 0;
  background: #1e1e2e;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  height: 100%;
}

.sidebar.collapsed {
  width: 70px;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.new-chat-btn {
  flex: 1;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.new-chat-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.toggle-sidebar-btn {
  width: 40px;
  background: rgba(255,255,255,0.1);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  font-size: 18px;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  min-height: 0;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #cdd6f4;
  margin-bottom: 4px;
  position: relative;
}

.conversation-item:hover {
  background: rgba(255,255,255,0.1);
}

.conversation-item.active {
  background: rgba(102, 126, 234, 0.3);
}

.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-actions {
  display: flex;
  gap: 4px;
}

.icon-btn {
  background: none;
  border: none;
  color: #cdd6f4;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  font-size: 14px;
}

.icon-btn:hover {
  background: rgba(255,255,255,0.2);
}

/* Rename Dialog */
.rename-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.rename-dialog {
  background: white;
  padding: 24px;
  border-radius: 12px;
  min-width: 300px;
}

.rename-dialog h3 {
  margin: 0 0 16px 0;
}

.rename-dialog input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.btn-primary {
  background: #667eea;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}

.btn-secondary {
  background: #f1f1f1;
  color: #333;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}

/* Main Content */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #181825;
  margin: 12px;
  border-radius: 16px;
  overflow: hidden;
  min-width: 0;
  height: calc(100vh - 24px);
}

.tabs-header {
  display: flex;
  padding: 8px 16px;
  background: #1e1e2e;
  gap: 8px;
  flex-shrink: 0;
}

.tab-btn {
  padding: 10px 24px;
  border: none;
  background: transparent;
  color: #a6adc8;
  font-weight: 500;
  cursor: pointer;
  border-radius: 8px;
}

.tab-btn:hover {
  background: rgba(255,255,255,0.05);
}

.tab-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* Chat Tab */
.chat-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px;
  min-height: 0;
}

/* 美化滚动条 */
.chat-messages::-webkit-scrollbar,
.conversation-list::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track,
.conversation-list::-webkit-scrollbar-track {
  background: rgba(255,255,255,0.05);
}

.chat-messages::-webkit-scrollbar-thumb,
.conversation-list::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.2);
  border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb:hover,
.conversation-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.3);
}

/* Welcome Section */
.welcome-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  text-align: center;
  color: #cdd6f4;
  padding: 40px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 24px;
}

.welcome-section h1 {
  font-size: 32px;
  margin: 0 0 16px 0;
}

.welcome-features {
  display: flex;
  gap: 16px;
  margin-top: 24px;
  flex-wrap: wrap;
  justify-content: center;
}

.feature-card {
  background: rgba(255,255,255,0.1);
  padding: 16px 24px;
  border-radius: 12px;
  font-size: 16px;
}

/* Messages */
.message {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  max-width: 900px;
  width: 100%;
}

.message.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.message.assistant .message-avatar {
  background: rgba(255,255,255,0.1);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message.user .message-content {
  text-align: right;
}

.message-text {
  background: rgba(255,255,255,0.1);
  padding: 16px 20px;
  border-radius: 16px;
  color: #cdd6f4;
  line-height: 1.6;
  display: inline-block;
  text-align: left;
  max-width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.message.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* Markdown styling in messages */
.message-text :deep(h1), .message-text :deep(h2), .message-text :deep(h3) {
  margin: 16px 0 8px 0;
}

.message-text :deep(code) {
  background: rgba(0,0,0,0.2);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.message-text :deep(pre) {
  background: #1e1e2e;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
}

.message-text :deep(pre code) {
  background: none;
}

/* Thinking Section */
.thinking-section {
  margin-bottom: 8px;
}

.thinking-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #89b4fa;
  cursor: pointer;
  padding: 8px 0;
}

.thinking-label {
  font-weight: 500;
}

.thinking-content {
  background: rgba(137, 180, 250, 0.1);
  padding: 12px 16px;
  border-radius: 8px;
  color: #bac2de;
  font-size: 14px;
  line-height: 1.6;
}

/* Typing indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 16px 20px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #cdd6f4;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

/* Chat Input */
.chat-input-area {
  padding: 16px 24px 24px;
  background: #1e1e2e;
  flex-shrink: 0;
}

.input-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.mode-toggle-group {
  display: flex;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
  padding: 4px;
}

.mode-btn {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: #a6adc8;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.mode-btn:hover {
  background: rgba(255,255,255,0.05);
}

.mode-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.toggle-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-switch {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.toggle-track {
  width: 40px;
  height: 20px;
  background: rgba(255,255,255,0.1);
  border-radius: 10px;
  position: relative;
  transition: background 0.3s;
}

.toggle-switch.active .toggle-track {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.toggle-thumb {
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: left 0.3s;
}

.toggle-switch.active .toggle-thumb {
  left: 22px;
}

.toggle-label {
  color: #a6adc8;
  font-size: 13px;
}

.attach-btn {
  background: rgba(255,255,255,0.1);
  border: none;
  color: #a6adc8;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 18px;
}

.attach-btn:hover {
  background: rgba(255,255,255,0.15);
}

.attached-file-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255,255,255,0.05);
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 12px;
  color: #cdd6f4;
}

.file-name {
  flex: 1;
}

.remove-file {
  background: none;
  border: none;
  color: #a6adc8;
  cursor: pointer;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  background: rgba(255,255,255,0.05);
  border-radius: 16px;
  padding: 8px;
}

.input-wrapper textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: #cdd6f4;
  font-size: 15px;
  resize: none;
  outline: none;
  font-family: inherit;
  line-height: 1.5;
}

.input-wrapper textarea::placeholder {
  color: #6c7086;
}

.send-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  padding: 12px 24px;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Cleaning Tab */
.cleaning-tab {
  flex: 1;
  overflow: auto;
  padding: 24px;
  min-height: 0;
}
</style>
