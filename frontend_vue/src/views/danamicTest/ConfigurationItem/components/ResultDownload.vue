<template>
  <div class="result-download">
    <el-card class="result-card">
      <h4>生成结果</h4>
      <div v-if="generatedFiles.length > 0">
        <el-table :data="generatedFiles" style="width: 100%">
          <el-table-column prop="name" label="文件名" min-width="200">
            <template #default="scope">
              <el-icon class="file-icon"><document /></el-icon>
              {{ scope.row.name }}
            </template>
          </el-table-column>
          <el-table-column prop="size" label="文件大小" width="120"></el-table-column>
          <el-table-column prop="type" label="类型" width="150"></el-table-column>
          <el-table-column prop="createTime" label="创建时间" width="180"></el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="scope">
              <el-button 
                size="small" 
                type="primary" 
                @click="downloadFile(scope.row)"
                :loading="scope.row.downloading">
                <el-icon><download /></el-icon>
                下载
              </el-button>
              <el-button 
                size="small" 
                type="success" 
                @click="previewFile(scope.row)"
                :disabled="!canPreview(scope.row)">
                <el-icon><view /></el-icon>
                预览
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="batch-actions">
          <el-button 
            type="primary" 
            @click="downloadAll"
            :loading="downloadingAll">
            <el-icon><download /></el-icon>
            批量下载
          </el-button>
          <el-button 
            type="warning" 
            @click="cleanupFiles">
            <el-icon><delete /></el-icon>
            清理文件
          </el-button>
        </div>
      </div>
      
      <div v-else class="no-files">
        <el-empty description="暂无生成的文件">
          <el-button type="primary" @click="$emit('restart')">重新生成</el-button>
        </el-empty>
      </div>
    </el-card>

    <el-card class="summary-card" v-if="generatedFiles.length > 0">
      <h4>生成摘要</h4>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务ID">{{ taskId }}</el-descriptions-item>
        <el-descriptions-item label="生成类型">{{ generationTypeText }}</el-descriptions-item>
        <el-descriptions-item label="文件数量">{{ generatedFiles.length }}</el-descriptions-item>
        <el-descriptions-item label="总大小">{{ totalSize }}</el-descriptions-item>
        <el-descriptions-item label="生成时间">{{ generateTime }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag type="success">已完成</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 预览对话框 -->
    <el-dialog 
      v-model="previewVisible" 
      title="文件预览" 
      width="80%"
      :before-close="handlePreviewClose">
      <div class="preview-content">
        <div v-if="previewLoading" class="preview-loading">
          <el-skeleton :rows="5" animated />
        </div>
        <div v-else-if="previewContent" class="preview-text">
          <pre>{{ previewContent }}</pre>
        </div>
        <div v-else class="preview-error">
          <el-alert 
            title="预览失败" 
            type="error" 
            description="无法预览此文件类型或文件损坏" 
            show-icon>
          </el-alert>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { Document, Download, View, Delete } from '@element-plus/icons-vue'

export default {
  name: 'ResultDownload',
  components: {
    Document,
    Download,
    View,
    Delete
  },
  props: {
    taskId: {
      type: String,
      required: true
    },
    generationType: {
      type: String,
      required: true
    },
    generatedFiles: {
      type: Array,
      default: () => []
    }
  },
  emits: ['restart', 'cleanup'],
  data() {
    return {
      downloadingAll: false,
      previewVisible: false,
      previewLoading: false,
      previewContent: '',
      previewFile: null
    }
  },
  computed: {
    generationTypeText() {
      return this.generationType === 'planning' ? '仅策划表' : '完整表单';
    },
    totalSize() {
      const totalBytes = this.generatedFiles.reduce((sum, file) => {
        return sum + (file.sizeBytes || 0);
      }, 0);
      return this.formatFileSize(totalBytes);
    },
    generateTime() {
      return new Date().toLocaleString();
    }
  },
  methods: {
    async downloadFile(file) {
      if (file.downloading) return;
      
      this.$set(file, 'downloading', true);
      
      try {
        // 这里应该调用实际的下载API
        await this.delay(1000); // 模拟下载时间
        
        // 创建下载链接
        const link = document.createElement('a');
        link.href = file.url || '#';
        link.download = file.name;
        link.click();
        
        this.$message.success(`文件 ${file.name} 下载成功`);
      } catch (error) {
        this.$message.error(`下载失败: ${error.message}`);
      } finally {
        this.$set(file, 'downloading', false);
      }
    },
    
    async downloadAll() {
      this.downloadingAll = true;
      
      try {
        for (const file of this.generatedFiles) {
          await this.downloadFile(file);
          await this.delay(200); // 避免并发下载过多
        }
        
        this.$message.success('所有文件下载完成');
      } catch (error) {
        this.$message.error(`批量下载失败: ${error.message}`);
      } finally {
        this.downloadingAll = false;
      }
    },
    
    async previewFile(file) {
      if (!this.canPreview(file)) {
        this.$message.warning('此文件类型不支持预览');
        return;
      }
      
      this.previewFile = file;
      this.previewVisible = true;
      this.previewLoading = true;
      this.previewContent = '';
      
      try {
        // 模拟获取预览内容
        await this.delay(1000);
        this.previewContent = `这是 ${file.name} 的预览内容...\n\n文件类型: ${file.type}\n文件大小: ${file.size}\n创建时间: ${file.createTime}`;
      } catch (error) {
        this.$message.error(`预览失败: ${error.message}`);
      } finally {
        this.previewLoading = false;
      }
    },
    
    canPreview(file) {
      const previewableTypes = ['txt', 'log', 'json', 'xml', 'csv'];
      const extension = file.name.split('.').pop().toLowerCase();
      return previewableTypes.includes(extension);
    },
    
    handlePreviewClose() {
      this.previewVisible = false;
      this.previewContent = '';
      this.previewFile = null;
    },
    
    async cleanupFiles() {
      try {
        await this.$confirm('确定要清理所有生成的文件吗？此操作不可恢复。', '确认清理', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        });
        
        // 调用清理API
        this.$emit('cleanup', this.taskId);
        this.$message.success('文件清理完成');
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error(`清理失败: ${error.message}`);
        }
      }
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    }
  }
}
</script>

<style scoped>
.result-download {
  padding: 20px;
}

.result-card,
.summary-card {
  margin-bottom: 20px;
}

.result-card h4,
.summary-card h4 {
  margin-top: 0;
  color: #409eff;
}

.file-icon {
  margin-right: 8px;
  color: #409eff;
}

.batch-actions {
  margin-top: 20px;
  text-align: center;
}

.batch-actions .el-button {
  margin: 0 10px;
}

.no-files {
  text-align: center;
  padding: 40px 0;
}

.preview-content {
  min-height: 300px;
}

.preview-loading {
  padding: 20px;
}

.preview-text {
  max-height: 500px;
  overflow-y: auto;
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
}

.preview-text pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
}

.preview-error {
  padding: 20px;
}

.el-table .el-button {
  margin-right: 5px;
}

.el-table .el-button:last-child {
  margin-right: 0;
}
</style> 