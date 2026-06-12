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
          {{ sidebarCollapsed ? '›' : '‹' }}
        </button>
      </div>

      <!-- Search box -->
      <div class="search-box" v-if="!sidebarCollapsed">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="搜索对话..."
          @input="filterConversations"
        />
      </div>

      <div class="conversation-list">
        <div
          v-for="conv in filteredConversations"
          :key="conv.id"
          :class="['conversation-item', { active: currentConversationId === conv.id }]"
          @click="selectConversation(conv.id)"
        >
          <span class="conv-icon">💬</span>
          <span class="conv-title" v-if="!sidebarCollapsed">
            <span v-if="!renamingConversation || renamingConversation.id !== conv.id">
              {{ conv.title }}
            </span>
            <input
              v-else
              type="text"
              v-model="newConversationTitle"
              @keyup.enter="confirmRename"
              @blur="cancelRename"
              ref="renameInput"
            />
          </span>
          <div class="conv-actions" v-if="!sidebarCollapsed && currentConversationId === conv.id">
            <button class="icon-btn" @click.stop="startRename(conv)" title="重命名">✏️</button>
            <button class="icon-btn" @click.stop="deleteConversation(conv.id)" title="删除">🗑️</button>
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

              <!-- Message Actions (only for assistant messages) -->
              <div v-if="msg.role === 'assistant'" class="message-actions">
                <button
                  class="action-btn"
                  @click="copyMessage(msg.content)"
                  :class="{ copied: copiedMessageId === msg.id }"
                >
                  {{ copiedMessageId === msg.id ? '✓ 已复制' : '📋 复制' }}
                </button>
                <button
                  class="action-btn"
                  @click="regenerateMessage(msg)"
                  :disabled="isGenerating || isStreaming"
                >
                  {{ regeneratingId === msg.id ? '⏳ 重新生成中...' : '🔄 重新生成' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Streaming message with cursor -->
          <div v-if="isStreaming" class="message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
              <div class="message-text">
                {{ streamingContent }}<span class="cursor">|</span>
              </div>
            </div>
          </div>

          <!-- Loading indicator (non-streaming) -->
          <div v-if="isGenerating && !isStreaming" class="message assistant">
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

            <div class="toggle-control">
              <label :class="['toggle-switch', { active: streamingMode }]" @click="streamingMode = !streamingMode">
                <span class="toggle-track"></span>
                <span class="toggle-thumb"></span>
              </label>
              <span class="toggle-label">✨ 流式输出</span>
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
            <button class="send-btn" @click="sendMessage" :disabled="!userInput.trim() || isGenerating || isStreaming">
              {{ isGenerating || isStreaming ? '⏳' : '发送' }}
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
      activeTab: 'chat',
      sidebarCollapsed: false,
      searchQuery: '',

      conversations: [],
      filteredConversations: [],
      currentConversationId: null,
      renamingConversation: null,
      newConversationTitle: '',

      messages: [],
      userInput: '',
      isGenerating: false,
      isStreaming: false,
      streamingContent: '',
      streamingEventSource: null,
      streamingMode: true,
      deepThinkingMode: false,
      webSearchEnabled: false,
      expandedThinking: {},

      copiedMessageId: null,
      regeneratingId: null,

      attachedFile: null
    }
  },
  mounted() {
    this.loadConversations()
  },
  methods: {
    async loadConversations() {
      try {
        const response = await axios.get('/api/chat/conversations')
        this.conversations = response.data
        this.filteredConversations = response.data
      } catch (err) {
        console.error('Failed to load conversations:', err)
      }
    },

    filterConversations() {
      if (!this.searchQuery.trim()) {
        this.filteredConversations = this.conversations
        return
      }

      const query = this.searchQuery.toLowerCase()
      this.filteredConversations = this.conversations.filter(conv =>
        conv.title.toLowerCase().includes(query)
      )
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
      this.$nextTick(() => {
        this.$refs.renameInput?.focus()
      })
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
        this.filteredConversations = this.filteredConversations.filter(c => c.id !== id)
        if (this.currentConversationId === id) {
          this.createNewConversation()
        }
      } catch (err) {
        console.error('Failed to delete conversation:', err)
      }
    },

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
      if (!this.userInput.trim() || this.isGenerating || this.isStreaming) return

      const inputText = this.userInput
      this.userInput = ''

      if (this.streamingMode) {
        await this.sendMessageStreaming(inputText)
      } else {
        await this.sendMessageNormal(inputText)
      }
    },

    async sendMessageNormal(userMessage) {
      this.isGenerating = true
      this.scrollToBottom()

      const userMsg = {
        id: Date.now().toString(),
        role: 'user',
        content: userMessage,
        timestamp: new Date()
      }
      this.messages.push(userMsg)

      try {
        const response = await axios.post('/api/chat/send', {
          conversationId: this.currentConversationId,
          message: userMessage,
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

    async sendMessageStreaming(userMessage) {
      this.isStreaming = true
      this.streamingContent = ''

      const userMsg = {
        id: Date.now().toString(),
        role: 'user',
        content: userMessage,
        timestamp: new Date()
      }
      this.messages.push(userMsg)
      this.scrollToBottom()

      try {
        const params = new URLSearchParams({
          message: userMessage,
          deepThinking: this.deepThinkingMode,
          webSearchEnabled: this.webSearchEnabled
        })
        if (this.currentConversationId) {
          params.append('conversationId', this.currentConversationId)
        }

        const url = `/api/chat/stream?${params}`
        console.log('📡 Connecting to streaming:', url)

        const eventSource = new EventSource(url)
        this.streamingEventSource = eventSource

        eventSource.onmessage = (event) => {
          if (event.data && event.data.trim()) {
            this.streamingContent += event.data
            this.scrollToBottom()
          }
        }

        eventSource.onerror = (error) => {
          console.log('📡 Stream closed or errored')
          eventSource.close()
          this.finalizeStreamingMessage(userMessage)
        }

        eventSource.onopen = () => {
          console.log('📡 SSE connection opened')
        }

      } catch (err) {
        console.error('Failed to send streaming message:', err)
        this.messages.push({
          id: Date.now().toString(),
          role: 'assistant',
          content: '抱歉，发生了错误，请稍后再试。'
        })
        this.isStreaming = false
      }
    },

    async finalizeStreamingMessage(userMessage) {
      if (this.streamingContent.trim()) {
        this.messages.push({
          id: Date.now().toString(),
          role: 'assistant',
          content: this.streamingContent
        })
      }

      this.isStreaming = false
      this.streamingContent = ''
      this.streamingEventSource = null
      this.scrollToBottom()

      await this.loadConversations()
    },

    async copyMessage(content) {
      try {
        await navigator.clipboard.writeText(content)
        this.copiedMessageId = null
        this.$nextTick(() => {
          this.copiedMessageId = this.messages.find(m => m.content === content)?.id
          setTimeout(() => {
            this.copiedMessageId = null
          }, 2000)
        })
      } catch (err) {
        console.error('Failed to copy:', err)
      }
    },

    async regenerateMessage(msg) {
      const msgIndex = this.messages.findIndex(m => m.id === msg.id)
      let userMessage = null

      for (let i = msgIndex - 1; i >= 0; i--) {
        if (this.messages[i].role === 'user') {
          userMessage = this.messages[i].content
          break
        }
      }

      if (!userMessage) return

      this.regeneratingId = msg.id
      this.messages = this.messages.filter(m => m.id !== msg.id)

      if (this.streamingMode) {
        await this.sendMessageStreaming(userMessage)
      } else {
        await this.sendMessageNormal(userMessage)
      }

      this.regeneratingId = null
    },

    scrollToBottom() {
      this.$nextTick(() => {
        if (this.$refs.chatMessagesRef) {
          this.$refs.chatMessagesRef.scrollTop = this.$refs.chatMessagesRef.scrollHeight
        }
      })
    },

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
  background: #0f0f1a;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  flex-shrink: 0;
  background: rgba(17, 24, 39, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  height: 100%;
}

.sidebar.collapsed {
  width: 72px;
}

.sidebar-header {
  padding: 16px 16px 12px;
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.search-box {
  padding: 0 16px 12px;
}

.search-box input {
  width: 100%;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #e5e7eb;
  font-size: 14px;
  outline: none;
  transition: all 0.2s;
}

.search-box input:focus {
  border-color: rgba(99, 102, 241, 0.5);
  background: rgba(255, 255, 255, 0.08);
}

.search-box input::placeholder {
  color: #6b7280;
}

.new-chat-btn {
  flex: 1;
  padding: 11px 16px;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  color: white;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);
}

.new-chat-btn:hover {
  transform: translateY(-1px) scale(1.01);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.toggle-sidebar-btn {
  width: 42px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  color: #9ca3af;
  cursor: pointer;
  font-size: 18px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.toggle-sidebar-btn:hover {
  background: rgba(255,255,255,0.1);
  color: #e5e7eb;
  transform: scale(1.05);
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
  min-height: 0;
}

.conversation-list::-webkit-scrollbar {
  width: 6px;
}

.conversation-list::-webkit-scrollbar-track {
  background: transparent;
}

.conversation-list::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.12);
  border-radius: 3px;
  transition: background 0.2s ease;
}

.conversation-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.2);
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  color: #d1d5db;
  margin-bottom: 4px;
  position: relative;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.conversation-item:hover {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.06);
  transform: translateX(2px);
}

.conversation-item.active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.18) 0%, rgba(139, 92, 246, 0.12) 100%);
  border-color: rgba(59, 130, 246, 0.35);
  box-shadow: 0 2px 10px rgba(59, 130, 246, 0.15);
}

.conversation-item.active::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: linear-gradient(180deg, #3b82f6 0%, #8b5cf6 100%);
  border-radius: 0 2px 2px 0;
}

.sidebar.collapsed .conversation-item.active::before {
  left: -10px;
  width: 4px;
}

.conv-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  color: #d1d5db;
}

.conv-title input {
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.5);
  border-radius: 6px;
  color: #fff;
  padding: 4px 8px;
  font-size: 14px;
  outline: none;
}

.sidebar.collapsed .conv-title,
.sidebar.collapsed .conv-actions,
.sidebar.collapsed .search-box {
  display: none;
}

.sidebar.collapsed .conversation-item {
  justify-content: center;
  padding: 12px;
}

.sidebar.collapsed .new-chat-btn .text {
  display: none;
}

.sidebar.collapsed .new-chat-btn {
  padding: 12px;
}

.conv-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.conversation-item:hover .conv-actions {
  opacity: 1;
}

.icon-btn {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background: rgba(255,255,255,0.12);
  color: #e5e7eb;
  transform: scale(1.1);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0f0f1a;
  margin: 0;
  border-radius: 0;
  overflow: hidden;
  min-width: 0;
  height: 100vh;
}

.tabs-header {
  display: flex;
  padding: 12px 24px;
  background: rgba(26, 26, 46, 0.6);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255,255,255,0.08);
  gap: 8px;
  flex-shrink: 0;
}

.tab-btn {
  padding: 10px 28px;
  border: none;
  background: transparent;
  color: #9ca3af;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  background: rgba(255,255,255,0.06);
  color: #d1d5db;
}

.tab-btn.active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.15) 100%);
  color: white;
  border: 1px solid rgba(99, 102, 241, 0.3);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
}

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
  padding: 32px;
  min-height: 0;
}

.chat-messages::-webkit-scrollbar {
  width: 10px;
}

.chat-messages::-webkit-scrollbar-track {
  background: rgba(255,255,255,0.03);
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.12);
  border-radius: 6px;
  border: 2px solid rgba(255,255,255,0.03);
  transition: all 0.3s ease;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.2);
}

.welcome-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  text-align: center;
  color: #e5e7eb;
  padding: 40px 20px;
  animation: fadeInUp 0.6s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.welcome-icon {
  font-size: 72px;
  margin-bottom: 28px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.welcome-section h1 {
  font-size: 36px;
  margin: 0 0 12px 0;
  background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.welcome-section p {
  color: #9ca3af;
  font-size: 16px;
  margin: 0 0 32px 0;
}

.welcome-features {
  display: flex;
  gap: 16px;
  margin-top: 24px;
  flex-wrap: wrap;
  justify-content: center;
}

.feature-card {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
  border: 1px solid rgba(99, 102, 241, 0.2);
  padding: 18px 28px;
  border-radius: 16px;
  font-size: 15px;
  color: #d1d5db;
  transition: all 0.3s ease;
  cursor: pointer;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.4);
}

.message {
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
  max-width: 900px;
  width: 100%;
  animation: messageIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.message.assistant .message-avatar {
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
  border: 1px solid rgba(255,255,255,0.1);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message.user .message-content {
  text-align: right;
}

.message-text {
  background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.04) 100%);
  border: 1px solid rgba(255,255,255,0.08);
  padding: 18px 22px;
  border-radius: 18px;
  color: #e5e7eb;
  line-height: 1.7;
  display: inline-block;
  text-align: left;
  max-width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
  transition: all 0.3s ease;
}

.message.user .message-text {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  color: white;
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.3);
}

.cursor {
  animation: blink 1s infinite;
  font-weight: bold;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.action-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #9ca3af;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: #e5e7eb;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.copied {
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.1);
}

.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3) {
  margin: 20px 0 12px 0;
  color: #f3f4f6;
  font-weight: 600;
}

.message-text :deep(code) {
  background: rgba(0,0,0,0.3);
  padding: 3px 8px;
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 14px;
  color: #f472b6;
}

.message-text :deep(pre) {
  background: #0a0a12;
  border: 1px solid rgba(255,255,255,0.1);
  padding: 16px;
  border-radius: 12px;
  overflow-x: auto;
  margin: 12px 0;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
  color: #e5e7eb;
}

.thinking-section {
  margin-bottom: 12px;
}

.thinking-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #a5b4fc;
  cursor: pointer;
  padding: 10px 0;
  font-size: 14px;
  transition: all 0.2s ease;
}

.thinking-toggle:hover {
  color: #c7d2fe;
}

.thinking-label {
  font-weight: 500;
}

.thinking-content {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.04) 100%);
  border: 1px solid rgba(99, 102, 241, 0.15);
  padding: 16px 20px;
  border-radius: 14px;
  color: #c7d2fe;
  font-size: 14px;
  line-height: 1.7;
  animation: expandIn 0.3s ease;
}

@keyframes expandIn {
  from {
    opacity: 0;
    max-height: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    max-height: 500px;
    transform: translateY(0);
  }
}

.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 18px 22px;
}

.typing-indicator span {
  width: 10px;
  height: 10px;
  background: #a5b4fc;
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
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.6;
  }
  30% {
    transform: translateY(-12px);
    opacity: 1;
  }
}

.chat-input-area {
  padding: 20px 32px 28px;
  background: linear-gradient(to top, rgba(26, 26, 46, 0.9) 0%, rgba(26, 26, 46, 0.7) 100%);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255,255,255,0.08);
  flex-shrink: 0;
}

.input-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.mode-toggle-group {
  display: flex;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 14px;
  padding: 5px;
  gap: 4px;
}

.mode-btn {
  padding: 10px 18px;
  border: none;
  background: transparent;
  color: #9ca3af;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.mode-btn:hover {
  background: rgba(255,255,255,0.08);
  color: #d1d5db;
}

.mode-btn.active {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.toggle-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toggle-switch {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.toggle-track {
  width: 48px;
  height: 26px;
  background: rgba(255,255,255,0.1);
  border-radius: 14px;
  position: relative;
  transition: all 0.3s ease;
  border: 1px solid rgba(255,255,255,0.1);
}

.toggle-switch.active .toggle-track {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.toggle-thumb {
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 3px;
  transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.toggle-switch.active .toggle-thumb {
  left: 23px;
}

.toggle-label {
  color: #9ca3af;
  font-size: 13px;
  font-weight: 500;
}

.attach-btn {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  color: #9ca3af;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 20px;
  transition: all 0.3s ease;
}

.attach-btn:hover {
  background: rgba(255,255,255,0.1);
  border-color: rgba(255,255,255,0.2);
  color: #d1d5db;
  transform: scale(1.05);
}

.attached-file-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  padding: 12px 16px;
  border-radius: 14px;
  margin-bottom: 16px;
  color: #e5e7eb;
}

.file-name {
  flex: 1;
  font-size: 14px;
}

.remove-file {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 18px;
  padding: 4px;
  transition: all 0.2s ease;
}

.remove-file:hover {
  color: #fca5a5;
  transform: scale(1.1);
}

.input-wrapper {
  display: flex;
  gap: 14px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 10px 12px 10px 18px;
  transition: all 0.3s ease;
}

.input-wrapper:focus-within {
  border-color: #6366f1;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15);
  background: rgba(255,255,255,0.08);
}

.input-wrapper textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: #e5e7eb;
  font-size: 15px;
  resize: none;
  outline: none;
  font-family: inherit;
  line-height: 1.6;
  max-height: 200px;
}

.input-wrapper textarea::placeholder {
  color: #6b7280;
}

.send-btn {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  color: white;
  padding: 14px 28px;
  border-radius: 16px;
  cursor: pointer;
  font-weight: 600;
  font-size: 15px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  align-self: flex-end;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.cleaning-tab {
  flex: 1;
  overflow: auto;
  padding: 32px;
  min-height: 0;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -280px;
    top: 0;
    z-index: 100;
    box-shadow: 4px 0 24px rgba(0,0,0,0.3);
  }

  .sidebar.mobile-open {
    left: 0;
  }

  .sidebar.collapsed {
    left: 0;
  }
}
</style>
