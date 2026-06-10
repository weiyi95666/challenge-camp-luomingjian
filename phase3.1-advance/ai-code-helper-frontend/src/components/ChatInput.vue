<template>
  <div class="chat-input" :class="{ 'is-focused': isFocused }">
    <div class="input-wrapper">
      <!-- 文件预览区域 -->
      <div v-if="selectedFiles.length > 0" class="image-preview-bar multi-file-preview">
        <div v-for="(file, index) in selectedFiles" :key="index" class="preview-container" :class="{ 'file-preview': !isImage(file) }">
          <img v-if="isImage(file)" :src="getPreviewUrl(file)" alt="预览图" />
          <div v-else class="file-icon-placeholder">
            <FileTextIcon :size="24" />
            <span class="file-name-tip">{{ file.name }}</span>
          </div>
          <button class="remove-image" @click="removeFile(index)">
            <XIcon :size="14" />
          </button>
        </div>
      </div>

      <div class="input-container">
        <!-- 上传按钮 -->
        <div class="input-left-actions">
          <label class="action-button image-upload-btn" title="上传文件">
            <PaperclipIcon :size="20" />
            <input type="file" @change="handleFileSelect" multiple hidden />
          </label>
          <label class="action-button folder-upload-btn" title="上传文件夹">
            <FolderUpIcon :size="20" />
            <input type="file" @change="handleFileSelect" webkitdirectory directory hidden />
          </label>
        </div>

        <textarea
          ref="inputRef"
          v-model="inputMessage"
          :placeholder="placeholder"
          :disabled="disabled"
          class="input-textarea"
          rows="1"
          @keydown="handleKeyDown"
          @paste="handlePaste"
          @input="adjustHeight"
          @focus="isFocused = true"
          @blur="isFocused = false"
        />
        
        <div class="input-actions">
          <div class="char-count" :class="{ 'near-limit': charCount > 1800 }">
            {{ charCount }}/2000
          </div>
          
          <button
            v-if="isTyping"
            type="button"
            @click="$emit('stop-generation')"
            class="stop-button"
            title="停止生成"
          >
            <SquareIcon :size="18" fill="currentColor" />
          </button>
          
          <button
            v-else
            :disabled="disabled || (!inputMessage.trim() && !selectedImage)"
            @click="sendMessage"
            class="send-button"
            :title="(inputMessage.trim() || selectedImage) ? '发送消息' : '请输入内容'"
          >
            <SendHorizonalIcon :size="20" />
          </button>
        </div>
      </div>
      <div class="input-tip">按 Enter 发送，Shift + Enter 换行</div>
    </div>
  </div>
</template>

<script>
import { SendHorizonal as SendHorizonalIcon, Square as SquareIcon, Paperclip as PaperclipIcon, FileText as FileTextIcon, X as XIcon, FolderUp as FolderUpIcon } from '@lucide/vue'

export default {
  name: 'ChatInput',
  components: {
    SendHorizonalIcon,
    SquareIcon,
    PaperclipIcon,
    FileTextIcon,
    XIcon,
    FolderUpIcon
  },
  props: {
    disabled: {
      type: Boolean,
      default: false
    },
    isTyping: {
      type: Boolean,
      default: false
    },
    placeholder: {
      type: String,
      default: '请输入您的问题...'
    }
  },
  data() {
    return {
      inputMessage: '',
      isFocused: false,
      selectedFiles: [],
      previewUrls: new Map()
    }
  },
  computed: {
    charCount() {
      return this.inputMessage.length
    }
  },
  methods: {
    isImage(file) {
      return file && file.type.startsWith('image/')
    },
    getPreviewUrl(file) {
      if (!this.isImage(file)) return null
      if (this.previewUrls.has(file)) return this.previewUrls.get(file)
      const url = URL.createObjectURL(file)
      this.previewUrls.set(file, url)
      return url
    },
    handleFileSelect(event) {
      const files = Array.from(event.target.files)
      if (files.length > 0) {
        this.selectedFiles = [...this.selectedFiles, ...files]
      }
      // Reset input value to allow selecting the same file again
      event.target.value = ''
    },
    handlePaste(event) {
      const items = (event.clipboardData || event.originalEvent?.clipboardData)?.items
      if (!items) return
      
      for (const item of items) {
        if (item.type.indexOf('image') !== -1) {
          const file = item.getAsFile()
          if (file) {
            this.selectedFiles.push(file)
          }
        }
      }
    },
    removeFile(index) {
      const file = this.selectedFiles[index]
      if (this.previewUrls.has(file)) {
        URL.revokeObjectURL(this.previewUrls.get(file))
        this.previewUrls.delete(file)
      }
      this.selectedFiles.splice(index, 1)
    },
    sendMessage() {
      if ((this.inputMessage.trim() || this.selectedFiles.length > 0) && !this.disabled) {
        this.$emit('send-message', {
          text: this.inputMessage.trim(),
          files: this.selectedFiles
        })
        this.inputMessage = ''
        // Clear all previews
        this.previewUrls.forEach(url => URL.revokeObjectURL(url))
        this.previewUrls.clear()
        this.selectedFiles = []
        this.adjustHeight()
      }
    },
    handleKeyDown(event) {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault()
        this.sendMessage()
      }
    },
    adjustHeight() {
      this.$nextTick(() => {
        const textarea = this.$refs.inputRef
        if (!textarea) return
        textarea.style.height = 'auto'
        const newHeight = Math.min(textarea.scrollHeight, 200)
        textarea.style.height = newHeight + 'px'
      })
    },
    focus() {
      this.$refs.inputRef?.focus()
    }
  },
  mounted() {
    this.adjustHeight()
  }
}
</script>

<style scoped>
.chat-input {
  padding: 16px 24px 24px;
  background-color: #ffffff;
  border-top: 1px solid #edf2f7;
  transition: all 0.3s ease;
}

.chat-input.is-focused {
  background-color: #fcfcfd;
}

.input-wrapper {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.image-preview-bar {
  display: flex;
  flex-wrap: wrap;
  padding: 8px 0;
  gap: 12px;
}

.preview-container {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow: visible;
  background-color: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-container.file-preview {
  width: 100px;
  padding: 8px;
}

.file-icon-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #64748b;
  width: 100%;
}

.file-name-tip {
  font-size: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px;
}

.preview-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-image {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: #ef4444;
  color: white;
  border: 2px solid white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: transform 0.2s;
}

.remove-image:hover {
  transform: scale(1.1);
}

.input-container {
  display: flex;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 8px 12px;
  transition: all 0.2s;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
  align-items: flex-end;
}

.input-container:focus-within {
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.input-left-actions {
  padding-bottom: 4px;
  margin-right: 4px;
}

.action-button {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #718096;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.action-button:hover {
  background-color: #f7fafc;
  color: #3182ce;
}

.input-textarea {
  flex: 1;
  padding: 8px 12px;
  border: none;
  background: transparent;
  font-size: 15px;
  line-height: 1.5;
  resize: none;
  outline: none;
  min-height: 24px;
  max-height: 200px;
  overflow-y: auto;
  color: #2d3748;
}

.input-textarea::placeholder {
  color: #a0aec0;
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 4px;
}

.char-count {
  font-size: 11px;
  color: #a0aec0;
  margin-right: 4px;
}

.char-count.near-limit {
  color: #e53e3e;
}

.send-button, .stop-button {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-button {
  background-color: #3182ce;
  color: white;
}

.send-button:hover:not(:disabled) {
  background-color: #2b6cb0;
  transform: translateY(-1px);
}

.send-button:disabled {
  background-color: #edf2f7;
  color: #a0aec0;
  cursor: not-allowed;
}

.stop-button {
  background-color: #e53e3e;
  color: white;
}

.stop-button:hover {
  background-color: #c53030;
}

.input-tip {
  font-size: 11px;
  color: #a0aec0;
  text-align: center;
}

@media (max-width: 768px) {
  .chat-input {
    padding: 12px 16px;
  }
  
  .input-textarea {
    font-size: 16px;
  }
}
</style> 