<template>
  <div class="chat-message" :class="{ 'user-message': isUser, 'ai-message': !isUser }">
    <div class="message-avatar">
      <div class="avatar-container" :class="{ 'user-avatar': isUser, 'ai-avatar': !isUser }">
        <component :is="isUser ? 'UserIcon' : 'BotIcon'" :size="20" />
      </div>
    </div>
    <div class="message-content">
      <div class="message-bubble" @click="handleBubbleClick">
        <!-- 显示上传的文件列表 -->
        <div v-if="files && files.length > 0" class="message-files">
          <div v-for="(file, index) in files" :key="index" class="file-item">
            <img v-if="isImage(file)" :src="getFileUrl(file)" alt="图片" @click.stop="previewFile(file)" />
            <div v-else class="file-attachment" @click.stop="previewFile(file)">
              <FileTextIcon :size="20" />
              <span class="file-name">{{ getFileName(file) }}</span>
            </div>
          </div>
        </div>
        
        <!-- 用户消息使用普通文本 -->
        <pre v-if="isUser" class="message-text">{{ message }}</pre>
        <!-- AI回复使用Markdown渲染 -->
        <div v-else class="message-markdown hljs" v-html="processedAiMessage"></div>
        
        <!-- 复制按钮 (仅针对AI消息中的代码块，简化版) -->
        <button v-if="!isUser && hasCode" class="copy-all-button" @click.stop="copyMessage" title="复制完整消息">
          <CopyIcon v-if="!copied" :size="14" />
          <CheckIcon v-else :size="14" />
        </button>
      </div>
      <div class="message-footer">
        <span class="message-time">{{ formatTime(timestamp) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { formatTime, renderMarkdown } from '../utils/index.js'
import { User as UserIcon, Bot as BotIcon, Copy as CopyIcon, Check as CheckIcon, FileText as FileTextIcon, Download as DownloadIcon, Eye as EyeIcon } from '@lucide/vue'

export default {
  name: 'ChatMessage',
  components: {
    UserIcon,
    BotIcon,
    CopyIcon,
    CheckIcon,
    FileTextIcon,
    DownloadIcon,
    EyeIcon
  },
  props: {
    message: {
      type: String,
      required: true
    },
    files: {
      type: Array,
      default: () => []
    },
    isUser: {
      type: Boolean,
      default: false
    },
    timestamp: {
      type: Date,
      default: () => new Date()
    }
  },
  data() {
    return {
      copied: false,
      fileUrls: new Map()
    }
  },
  computed: {
    processedAiMessage() {
      // 增强 Markdown 渲染，处理 [下载/预览](api/ai/files/download?path=...) 链接
      let html = renderMarkdown(this.message)
      const baseUrl = 'http://localhost:8081'
      
      // 替换下载链接为带图标的按钮样式
      html = html.replace(
        /\[下载\/预览\]\((api\/ai\/files\/download\?path=.*?)\)/g,
        (match, url) => {
          const fullUrl = `${baseUrl}/${url}`
          return `<div class="ai-file-actions">
            <a href="${fullUrl}" target="_blank" class="action-btn preview-btn"><i class="icon-eye"></i> 预览</a>
            <a href="${fullUrl}" download class="action-btn download-btn"><i class="icon-download"></i> 下载</a>
          </div>`
        }
      )
      return html
    },
    hasCode() {
      return this.message.includes('```')
    }
  },
  methods: {
    formatTime,
    isImage(file) {
      if (file instanceof File) return file.type.startsWith('image/')
      if (typeof file === 'string') return file.match(/\.(jpg|jpeg|png|gif|webp)$/i)
      return false
    },
    getFileName(file) {
      if (file instanceof File) return file.name
      return '附件'
    },
    getFileUrl(file) {
      if (typeof file === 'string') return file
      if (file instanceof File) {
        if (this.fileUrls.has(file)) return this.fileUrls.get(file)
        const url = URL.createObjectURL(file)
        this.fileUrls.set(file, url)
        return url
      }
      return null
    },
    previewFile(file) {
      const url = this.getFileUrl(file)
      if (url) window.open(url, '_blank')
    },
    async copyMessage() {
      try {
        await navigator.clipboard.writeText(this.message)
        this.copied = true
        setTimeout(() => {
          this.copied = false
        }, 2000)
      } catch (err) {
        console.error('无法复制:', err)
      }
    },
    handleBubbleClick(e) {
      // 可以在这里处理代码块内的点击事件，例如单独复制某个代码块
      const target = e.target
      if (target.tagName === 'CODE' && target.parentElement.tagName === 'PRE') {
        const code = target.innerText
        navigator.clipboard.writeText(code).then(() => {
          // 可以添加一个微小的反馈，比如改变背景色或显示提示
          const originalBg = target.style.backgroundColor
          target.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'
          setTimeout(() => {
            target.style.backgroundColor = originalBg
          }, 200)
        })
      }
    }
  }
}
</script>

<style scoped>
.chat-message {
  display: flex;
  margin-bottom: 24px;
  padding: 0 24px;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.user-message {
  justify-content: flex-end;
}

.user-message .message-avatar {
  order: 2;
  margin-left: 12px;
  margin-right: 0;
}

.user-message .message-content {
  align-items: flex-end;
}

.ai-message {
  justify-content: flex-start;
}

.ai-message .message-avatar {
  order: 1;
  margin-right: 12px;
  margin-left: 0;
}

.message-avatar {
  display: flex;
  align-items: flex-start;
}

.avatar-container {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.user-avatar {
  background: linear-gradient(135deg, #6e8efb, #a777e3);
}

.ai-avatar {
  background: linear-gradient(135deg, #3f4c6b, #606c88);
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: 80%;
}

.message-bubble {
  position: relative;
  padding: 12px 16px;
  border-radius: 12px;
  max-width: 100%;
  word-wrap: break-word;
}

.user-message .message-bubble {
  background-color: #007bff;
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-message .message-bubble {
  background-color: #ffffff;
  color: #2c3e50;
  border-bottom-left-radius: 4px;
  border: 1px solid #edf2f7;
}

.message-text {
  font-family: inherit;
  font-size: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
  margin: 0;
}

.message-files {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 10px;
}

.file-item img {
  max-width: 200px;
  max-height: 200px;
  border-radius: 8px;
  cursor: pointer;
}

/* AI 处理后的文件操作按钮 */
:deep(.ai-file-actions) {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

:deep(.action-btn) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
}

:deep(.preview-btn) {
  background-color: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
}

:deep(.preview-btn:hover) {
  background-color: #e2e8f0;
}

:deep(.download-btn) {
  background-color: #3b82f6;
  color: white;
}

:deep(.download-btn:hover) {
  background-color: #2563eb;
}

.file-attachment {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  color: #475569;
}

.file-attachment:hover {
  background-color: #f1f5f9;
}

.file-name {
  font-size: 14px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-footer {
  margin-top: 6px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.message-time {
  font-size: 11px;
  color: #a0aec0;
}

.copy-all-button {
  position: absolute;
  top: 8px;
  right: 8px;
  background-color: rgba(255, 255, 255, 0.8);
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 4px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4a5568;
}

.message-bubble:hover .copy-all-button {
  opacity: 1;
}

.copy-all-button:hover {
  background-color: #f7fafc;
}

/* Markdown样式增强 */
.message-markdown {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 15px;
  line-height: 1.6;
}

:deep(.message-markdown) p {
  margin: 0.8em 0;
}

:deep(.message-markdown) p:first-child { margin-top: 0; }
:deep(.message-markdown) p:last-child { margin-bottom: 0; }

:deep(.message-markdown) code {
  background-color: #f0f2f5;
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 0.9em;
  color: #e83e8c;
}

:deep(.message-markdown) pre {
  background-color: #1a202c;
  padding: 1.2em;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1em 0;
  position: relative;
}

:deep(.message-markdown) pre code {
  background-color: transparent;
  padding: 0;
  color: #e2e8f0;
  font-size: 0.85em;
}

:deep(.message-markdown) ul, :deep(.message-markdown) ol {
  margin: 0.8em 0;
  padding-left: 1.5em;
}

:deep(.message-markdown) blockquote {
  border-left: 4px solid #cbd5e0;
  padding-left: 1em;
  margin: 1em 0;
  color: #718096;
  font-style: italic;
}

:deep(.message-markdown) a {
  color: #007bff;
  text-decoration: underline;
}

:deep(.message-markdown) table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.8em 0;
}

:deep(.message-markdown) th,
:deep(.message-markdown) td {
  border: 1px solid #e2e8f0;
  padding: 0.6em;
  text-align: left;
}

:deep(.message-markdown) th {
  background-color: #f7fafc;
  font-weight: bold;
}

@media (max-width: 768px) {
  .message-content {
    max-width: 85%;
  }
  
  .chat-message {
    padding: 0 12px;
  }
}
</style> 