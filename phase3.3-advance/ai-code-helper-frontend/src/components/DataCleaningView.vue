<template>
  <div class="data-cleaning-container">
    <div class="cleaning-header">
      <h2>数据清洗智能体</h2>
      <p>上传数据文件，自动清洗并获得高质量数据</p>
    </div>

    <div class="upload-section" :class="{ 'dragover': isDragover }"
         @dragover.prevent="isDragover = true"
         @dragleave="isDragover = false"
         @drop.prevent="handleDrop">
      <input type="file" ref="fileInput" @change="handleFileSelect" accept=".csv,.xlsx,.xls,.json" style="display:none">
      
      <div class="upload-content" v-if="!uploadedFile">
        <div class="upload-icon">📁</div>
        <h3>点击或拖拽文件到此处</h3>
        <p>支持 CSV、Excel、JSON 格式</p>
        <button class="upload-btn" @click="triggerUpload">选择文件</button>
      </div>

      <div class="file-info" v-else>
        <div class="file-icon">📄</div>
        <div class="file-details">
          <h4>{{ uploadedFile.name }}</h4>
          <p>{{ formatFileSize(uploadedFile.size) }}</p>
        </div>
        <button class="remove-btn" @click="removeFile">✕</button>
      </div>
    </div>

    <div class="analysis-section" v-if="analysis && !isCleaning">
      <div class="analysis-card">
        <div class="analysis-icon">📊</div>
        <div class="analysis-text">
          <h4>数据概览</h4>
          <p>{{ analysis.rowCount }} 行 × {{ analysis.columnCount }} 列</p>
        </div>
      </div>
    </div>

    <div class="preview-section" v-if="sampleData.length > 0 && !isCleaning">
      <h3>数据预览</h3>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th v-for="col in columns" :key="col">{{ col }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in sampleData" :key="index">
              <td v-for="col in columns" :key="col">{{ row[col] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="action-section" v-if="uploadedFile && !isCleaning && !cleaningReport">
      <button class="clean-btn" @click="startCleaning" :disabled="isCleaning">
        {{ isGenerating ? '清洗中...' : '开始清洗' }}
      </button>
    </div>

    <div class="progress-section" v-if="isCleaning">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
      </div>
      <p>{{ progressText }}</p>
    </div>

    <div class="report-section" v-if="cleaningReport">
      <h3>清洗报告</h3>
      
      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-label">原行数</span>
          <span class="stat-value">{{ cleaningReport.originalRowCount }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">清洗后行数</span>
          <span class="stat-value">{{ cleaningReport.finalRowCount }}</span>
        </div>
        <div class="stat-card highlight">
          <span class="stat-label">移除重复</span>
          <span class="stat-value">{{ cleaningReport.removedDuplicates || 0 }}</span>
        </div>
        <div class="stat-card highlight">
          <span class="stat-label">脱敏处理</span>
          <span class="stat-value">{{ cleaningReport.maskedSensitiveData || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">日期标准化</span>
          <span class="stat-value">{{ cleaningReport.standardizedDates || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">填充缺失值</span>
          <span class="stat-value">{{ cleaningReport.filledMissingValues || 0 }}</span>
        </div>
      </div>

      <div v-if="cleaningReport.columnStats && cleaningReport.columnStats.length > 0" class="column-stats">
        <h4>各列处理统计</h4>
        <div class="stat-list">
          <div v-for="(stat, i) in cleaningReport.columnStats" :key="i" class="stat-item">
            <span class="stat-key">{{ Object.keys(stat)[0] }}</span>
            <span class="stat-val">{{ Object.values(stat)[0] }}</span>
          </div>
        </div>
      </div>

      <div class="report-actions">
        <button class="download-btn" @click="downloadResult">⬇️ 下载清洗结果</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'DataCleaningView',
  data() {
    return {
      isDragover: false,
      uploadedFile: null,
      taskId: null,
      analysis: null,
      sampleData: [],
      columns: [],
      isCleaning: false,
      progress: 0,
      progressText: '',
      cleaningReport: null
    }
  },
  methods: {
    triggerUpload() {
      this.$refs.fileInput.click()
    },
    
    handleFileSelect(e) {
      const file = e.target.files[0]
      if (file) this.uploadFile(file)
    },
    
    handleDrop(e) {
      this.isDragover = false
      const file = e.dataTransfer.files[0]
      if (file) this.uploadFile(file)
    },
    
    async uploadFile(file) {
      this.uploadedFile = file
      this.cleaningReport = null
      this.analysis = null
      this.sampleData = []
      this.taskId = null
      
      try {
        const formData = new FormData()
        formData.append('file', file)
        
        const response = await axios.post('/api/clean/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        this.taskId = response.data.taskId
        this.analysis = response.data.analysis
        this.sampleData = response.data.sample || []
        this.columns = this.sampleData.length > 0 ? Object.keys(this.sampleData[0]) : []
        
      } catch (err) {
        console.error('Upload failed:', err)
        alert('文件上传失败，请重试')
      }
    },
    
    removeFile() {
      this.uploadedFile = null
      this.taskId = null
      this.analysis = null
      this.sampleData = []
      this.cleaningReport = null
    },
    
    async startCleaning() {
      if (!this.taskId) return
      
      this.isCleaning = true
      this.progress = 0
      this.progressText = '正在准备...'
      
      try {
        this.progress = 20
        this.progressText = '正在读取数据...'
        
        const response = await axios.post(`/api/clean/start/${this.taskId}`, {
          autoAcceptLlm: true
        })
        
        this.progress = 80
        this.progressText = '正在保存结果...'
        
        this.cleaningReport = response.data.cleaningReport
        
        this.progress = 100
        this.progressText = '完成！'
        
      } catch (err) {
        console.error('Cleaning failed:', err)
        alert('清洗失败，请重试')
      } finally {
        setTimeout(() => {
          this.isCleaning = false
        }, 500)
      }
    },
    
    downloadResult() {
      if (!this.taskId) return
      window.open(`/api/clean/download/${this.taskId}`, '_blank')
    },
    
    formatFileSize(bytes) {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    }
  }
}
</script>

<style scoped>
.data-cleaning-container {
  max-width: 1000px;
  margin: 0 auto;
}

.cleaning-header {
  text-align: center;
  margin-bottom: 40px;
  color: #e5e7eb;
}

.cleaning-header h2 {
  margin: 0 0 12px;
  font-size: 36px;
  font-weight: 700;
  background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.cleaning-header p {
  margin: 0;
  color: #9ca3af;
  font-size: 16px;
}

.upload-section {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
  border: 2px dashed rgba(99, 102, 241, 0.3);
  border-radius: 20px;
  padding: 56px 32px;
  text-align: center;
  margin-bottom: 28px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.upload-section.dragover {
  border-color: #6366f1;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
  transform: scale(1.01);
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2);
}

.upload-icon {
  font-size: 72px;
  margin-bottom: 20px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.upload-content h3 {
  color: #e5e7eb;
  margin: 0 0 12px;
  font-size: 20px;
  font-weight: 600;
}

.upload-content p {
  color: #9ca3af;
  margin: 0 0 24px;
  font-size: 15px;
}

.upload-btn {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  color: white;
  padding: 14px 40px;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.upload-btn:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.file-icon {
  font-size: 48px;
}

.file-details {
  flex: 1;
  text-align: left;
}

.file-details h4 {
  color: #e5e7eb;
  margin: 0 0 6px;
  font-size: 17px;
  font-weight: 600;
}

.file-details p {
  color: #9ca3af;
  margin: 0;
  font-size: 14px;
}

.remove-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #9ca3af;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.remove-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  transform: scale(1.05);
}

.analysis-section {
  margin-bottom: 28px;
}

.analysis-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.04) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 24px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s ease;
}

.analysis-card:hover {
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.15);
}

.analysis-icon {
  font-size: 44px;
}

.analysis-text h4 {
  color: #e5e7eb;
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 600;
}

.analysis-text p {
  color: #9ca3af;
  margin: 0;
  font-size: 15px;
}

.preview-section {
  margin-bottom: 28px;
}

.preview-section h3 {
  color: #e5e7eb;
  margin: 0 0 20px;
  font-size: 20px;
  font-weight: 600;
}

.table-container {
  overflow-x: auto;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.04) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

.preview-section table {
  width: 100%;
  border-collapse: collapse;
  color: #e5e7eb;
}

.preview-section th,
.preview-section td {
  padding: 16px 20px;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.preview-section th {
  background: rgba(255, 255, 255, 0.06);
  font-weight: 600;
  color: #c7d2fe;
}

.preview-section tr:hover td {
  background: rgba(255, 255, 255, 0.04);
}

.action-section {
  text-align: center;
  margin-bottom: 28px;
}

.clean-btn {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  color: white;
  padding: 18px 56px;
  border-radius: 16px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.clean-btn:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 28px rgba(99, 102, 241, 0.4);
}

.clean-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.progress-section {
  text-align: center;
  margin-bottom: 28px;
}

.progress-bar {
  width: 100%;
  max-width: 450px;
  height: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  margin: 0 auto 16px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 6px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 16px rgba(99, 102, 241, 0.4);
}

.progress-section p {
  color: #9ca3af;
  margin: 0;
  font-size: 15px;
}

.report-section {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.04) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 32px;
}

.report-section h3 {
  color: #e5e7eb;
  margin: 0 0 28px;
  font-size: 22px;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 18px;
  margin-bottom: 28px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 24px;
  border-radius: 16px;
  text-align: center;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.15);
}

.stat-card.highlight {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
  border: 1px solid rgba(99, 102, 241, 0.3);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
}

.stat-label {
  display: block;
  color: #9ca3af;
  font-size: 14px;
  margin-bottom: 10px;
  font-weight: 500;
}

.stat-value {
  display: block;
  color: #e5e7eb;
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.column-stats {
  margin-bottom: 28px;
}

.column-stats h4 {
  color: #e5e7eb;
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 600;
}

.stat-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}

.stat-item {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 12px 18px;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  transition: all 0.2s ease;
}

.stat-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.stat-key {
  color: #9ca3af;
  font-size: 14px;
}

.stat-val {
  color: #a5b4fc;
  font-weight: 600;
  font-size: 14px;
}

.report-actions {
  text-align: center;
}

.download-btn {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  color: white;
  padding: 16px 40px;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.download-btn:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
}
</style>
