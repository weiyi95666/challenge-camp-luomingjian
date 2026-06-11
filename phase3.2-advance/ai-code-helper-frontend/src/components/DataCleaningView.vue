<template>
  <div class="data-cleaning-container">
    <!-- Header -->
    <div class="cleaning-header">
      <h2>数据清洗智能体</h2>
      <p>上传数据文件，自动清洗并获得高质量数据</p>
    </div>

    <!-- Upload Section -->
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

    <!-- Analysis Section -->
    <div class="analysis-section" v-if="analysis">
      <div class="analysis-card">
        <div class="analysis-icon">📊</div>
        <div class="analysis-text">
          <h4>数据概览</h4>
          <p>{{ analysis.rowCount }} 行 × {{ analysis.columnCount }} 列</p>
        </div>
      </div>
    </div>

    <!-- Data Preview -->
    <div class="preview-section" v-if="sampleData.length > 0">
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

    <!-- Action Button -->
    <div class="action-section" v-if="uploadedFile && !cleaningReport">
      <button class="clean-btn" @click="startCleaning" :disabled="isCleaning">
        {{ isCleaning ? '清洗中...' : '开始清洗' }}
      </button>
    </div>

    <!-- Progress -->
    <div class="progress-section" v-if="isCleaning">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
      </div>
      <p>{{ progressText }}</p>
    </div>

    <!-- Cleaning Report -->
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
          <span class="stat-value">{{ cleaningReport.removedDuplicates }}</span>
        </div>
        <div class="stat-card highlight">
          <span class="stat-label">脱敏处理</span>
          <span class="stat-value">{{ cleaningReport.maskedSensitiveData }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">日期标准化</span>
          <span class="stat-value">{{ cleaningReport.standardizedDates }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">填充缺失值</span>
          <span class="stat-value">{{ cleaningReport.filledMissingValues }}</span>
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
      
      try {
        const formData = new FormData()
        formData.append('file', file)
        
        const response = await axios.post('/api/clean/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        this.taskId = response.data.taskId
        this.analysis = response.data.analysis
        this.sampleData = response.data.sample
        this.columns = Object.keys(response.data.sample[0] || {})
        
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
  margin-bottom: 32px;
  color: #cdd6f4;
}

.cleaning-header h2 {
  margin: 0 0 8px;
  font-size: 28px;
}

.cleaning-header p {
  margin: 0;
  color: #a6adc8;
}

.upload-section {
  background: rgba(255, 255, 255, 0.05);
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 48px 24px;
  text-align: center;
  margin-bottom: 24px;
  transition: all 0.3s;
}

.upload-section.dragover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.upload-content h3 {
  color: #cdd6f4;
  margin: 0 0 8px;
}

.upload-content p {
  color: #a6adc8;
  margin: 0 0 20px;
}

.upload-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  padding: 12px 32px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.upload-btn:hover {
  transform: translateY(-2px);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.file-icon {
  font-size: 36px;
}

.file-details {
  flex: 1;
  text-align: left;
}

.file-details h4 {
  color: #cdd6f4;
  margin: 0 0 4px;
}

.file-details p {
  color: #a6adc8;
  margin: 0;
}

.remove-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #a6adc8;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
}

.remove-btn:hover {
  background: rgba(255, 100, 100, 0.3);
  color: #fff;
}

.analysis-section {
  margin-bottom: 24px;
}

.analysis-card {
  background: rgba(255, 255, 255, 0.05);
  padding: 20px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.analysis-icon {
  font-size: 36px;
}

.analysis-text h4 {
  color: #cdd6f4;
  margin: 0 0 4px;
}

.analysis-text p {
  color: #a6adc8;
  margin: 0;
}

.preview-section {
  margin-bottom: 24px;
}

.preview-section h3 {
  color: #cdd6f4;
  margin: 0 0 16px;
}

.table-container {
  overflow-x: auto;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.preview-section table {
  width: 100%;
  border-collapse: collapse;
  color: #cdd6f4;
}

.preview-section th,
.preview-section td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.preview-section th {
  background: rgba(255, 255, 255, 0.05);
  font-weight: 600;
}

.action-section {
  text-align: center;
  margin-bottom: 24px;
}

.clean-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  padding: 16px 48px;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.clean-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.clean-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.progress-section {
  text-align: center;
  margin-bottom: 24px;
}

.progress-bar {
  width: 100%;
  max-width: 400px;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  margin: 0 auto 12px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 4px;
  transition: width 0.3s;
}

.progress-section p {
  color: #a6adc8;
  margin: 0;
}

.report-section {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 24px;
}

.report-section h3 {
  color: #cdd6f4;
  margin: 0 0 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  padding: 20px;
  border-radius: 12px;
  text-align: center;
}

.stat-card.highlight {
  background: rgba(102, 126, 234, 0.2);
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.stat-label {
  display: block;
  color: #a6adc8;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  display: block;
  color: #cdd6f4;
  font-size: 28px;
  font-weight: 700;
}

.column-stats {
  margin-bottom: 24px;
}

.column-stats h4 {
  color: #cdd6f4;
  margin: 0 0 12px;
}

.stat-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
}

.stat-item {
  background: rgba(255, 255, 255, 0.05);
  padding: 10px 16px;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
}

.stat-key {
  color: #a6adc8;
}

.stat-val {
  color: #667eea;
  font-weight: 600;
}

.report-actions {
  text-align: center;
}

.download-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  padding: 14px 32px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.download-btn:hover {
  transform: translateY(-2px);
}
</style>
