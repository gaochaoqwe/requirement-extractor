<template>
  <div class="regression-result-download">
    <div v-if="!generationResult" class="no-result">
      <el-empty description="暂无生成结果">
        <el-button type="primary" @click="$emit('back-to-generation')">返回生成页面</el-button>
      </el-empty>
    </div>

    <div v-else class="result-content">
      <!-- 生成摘要 -->
      <el-card class="summary-card">
        <h4>生成摘要</h4>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="任务ID">{{ generationResult.taskId }}</el-descriptions-item>
          <el-descriptions-item label="生成类型">{{ getGenerationTypeName() }}</el-descriptions-item>
          <el-descriptions-item label="生成时间">{{ formatDate(generationResult.generatedAt) }}</el-descriptions-item>
          <el-descriptions-item label="文件数量">{{ resultFiles.length }}</el-descriptions-item>
          <el-descriptions-item label="测试用例数">{{ generationResult.preview?.testCaseCount || 0 }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType()">{{ getStatusText() }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="generationResult.advancedOptions" class="advanced-summary">
          <h5>高级选项配置</h5>
          <el-tag type="info" style="margin: 5px;">
            优先级策略: {{ getPriorityStrategyText() }}
          </el-tag>
          <el-tag 
            v-for="coverage in generationResult.advancedOptions.coverageStrategy" 
            :key="coverage" 
            type="success" 
            style="margin: 5px;">
            {{ coverage }}
          </el-tag>
          <el-tag v-if="generationResult.advancedOptions.automationSuggestion" type="warning" style="margin: 5px;">
            自动化建议已启用
          </el-tag>
          <el-tag v-if="generationResult.advancedOptions.useHistoryData" type="primary" style="margin: 5px;">
            历史数据参考已启用
          </el-tag>
        </div>
      </el-card>

      <!-- 文件列表 -->
      <el-card class="files-card">
        <div class="files-header">
          <h4>生成的文件</h4>
          <div class="files-actions">
            <el-button type="primary" @click="downloadAll" :loading="isDownloadingAll">
              <el-icon><Download /></el-icon>
              批量下载
            </el-button>
            <el-button type="success" @click="refreshFiles" :loading="isRefreshing">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="warning" @click="previewFiles" v-if="canPreview">
              <el-icon><View /></el-icon>
              预览
            </el-button>
          </div>
        </div>

        <el-table :data="resultFiles" style="width: 100%" stripe>
          <el-table-column prop="name" label="文件名" min-width="200">
            <template #default="{ row }">
              <div class="file-name">
                <el-icon class="file-icon">
                  <component :is="getFileIcon(row.type)" />
                </el-icon>
                <span>{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="type" label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getFileTypeColor(row.type)" size="small">
                {{ getFileTypeText(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="size" label="大小" width="100">
            <template #default="{ row }">
              {{ formatFileSize(row.size) }}
            </template>
          </el-table-column>
          
          <el-table-column prop="description" label="描述" min-width="200">
            <template #default="{ row }">
              <span class="file-description">{{ row.description }}</span>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small" 
                @click="downloadFile(row)"
                :loading="row.downloading">
                <el-icon><Download /></el-icon>
                下载
              </el-button>
              <el-button 
                type="info" 
                size="small" 
                @click="previewFile(row)"
                v-if="canPreviewFile(row)">
                <el-icon><View /></el-icon>
                预览
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 生成详情 -->
      <el-card class="details-card" v-if="showDetails">
        <h4>生成详情</h4>
        <el-collapse v-model="activeDetails">
          <el-collapse-item title="测试需求分析" name="requirements">
            <div v-if="analysisDetails.requirements">
              <p><strong>总需求数:</strong> {{ analysisDetails.requirements.total }}</p>
              <p><strong>功能需求:</strong> {{ analysisDetails.requirements.functional }}</p>
              <p><strong>性能需求:</strong> {{ analysisDetails.requirements.performance }}</p>
              <p><strong>安全需求:</strong> {{ analysisDetails.requirements.security }}</p>
              <p><strong>兼容性需求:</strong> {{ analysisDetails.requirements.compatibility }}</p>
            </div>
          </el-collapse-item>
          
          <el-collapse-item title="测试用例统计" name="testcases">
            <div v-if="analysisDetails.testCases">
              <p><strong>总用例数:</strong> {{ analysisDetails.testCases.total }}</p>
              <p><strong>高优先级:</strong> {{ analysisDetails.testCases.high }}</p>
              <p><strong>中优先级:</strong> {{ analysisDetails.testCases.medium }}</p>
              <p><strong>低优先级:</strong> {{ analysisDetails.testCases.low }}</p>
              <p><strong>自动化建议:</strong> {{ analysisDetails.testCases.automation }}%</p>
            </div>
          </el-collapse-item>
          
          <el-collapse-item title="风险评估" name="risks">
            <div v-if="analysisDetails.risks">
              <el-tag 
                v-for="risk in analysisDetails.risks" 
                :key="risk.area"
                :type="getRiskTypeColor(risk.level)"
                style="margin: 5px;">
                {{ risk.area }}: {{ risk.level }}
              </el-tag>
            </div>
          </el-collapse-item>
          
          <el-collapse-item title="质量指标" name="quality">
            <div v-if="analysisDetails.quality">
              <el-progress 
                :percentage="analysisDetails.quality.coverage" 
                :status="analysisDetails.quality.coverage >= 80 ? 'success' : 'warning'">
                <span>测试覆盖率</span>
              </el-progress>
              <el-progress 
                :percentage="analysisDetails.quality.completeness" 
                :status="analysisDetails.quality.completeness >= 90 ? 'success' : 'warning'"
                style="margin-top: 10px;">
                <span>需求完整性</span>
              </el-progress>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-card>

      <!-- 操作按钮 -->
      <el-card class="actions-card">
        <div class="action-buttons">
          <el-button type="primary" size="large" @click="downloadAll" :loading="isDownloadingAll">
            <el-icon><Download /></el-icon>
            下载所有文件
          </el-button>
          <el-button type="success" size="large" @click="exportReport" :loading="isExportingReport">
            <el-icon><Document /></el-icon>
            导出测试报告
          </el-button>
          <el-button type="warning" size="large" @click="cleanupFiles" :loading="isCleaning">
            <el-icon><Delete /></el-icon>
            清理临时文件
          </el-button>
          <el-button size="large" @click="reset">
            <el-icon><RefreshLeft /></el-icon>
            重新生成
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 文件预览对话框 -->
    <el-dialog 
      v-model="previewDialogVisible" 
      :title="'预览: ' + (previewFile?.name || '')"
      width="80%"
      center>
      <div class="preview-content">
        <div v-if="previewFile?.type === 'excel'" class="excel-preview">
          <p>Excel文件预览功能开发中...</p>
          <el-button type="primary" @click="downloadFile(previewFile)">
            直接下载查看
          </el-button>
        </div>
        <div v-else-if="previewFile?.type === 'text'" class="text-preview">
          <pre>{{ previewContent }}</pre>
        </div>
        <div v-else class="unsupported-preview">
          <p>该文件类型暂不支持预览</p>
          <el-button type="primary" @click="downloadFile(previewFile)">
            下载文件查看
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { Download, Refresh, View, Document, Delete, RefreshLeft } from '@element-plus/icons-vue'

export default {
  name: 'RegressionResultDownload',
  components: {
    Download,
    Refresh,
    View,
    Document,
    Delete,
    RefreshLeft
  },
  props: {
    generationResult: {
      type: Object,
      default: null
    }
  },
  emits: ['back-to-generation', 'reset', 'files-cleaned'],
  data() {
    return {
      resultFiles: [],
      isDownloadingAll: false,
      isRefreshing: false,
      isCleaning: false,
      isExportingReport: false,
      showDetails: true,
      activeDetails: ['requirements'],
      previewDialogVisible: false,
      previewFile: null,
      previewContent: '',
      analysisDetails: {
        requirements: {
          total: 25,
          functional: 18,
          performance: 4,
          security: 2,
          compatibility: 1
        },
        testCases: {
          total: 45,
          high: 15,
          medium: 20,
          low: 10,
          automation: 75
        },
        risks: [
          { area: '功能回归', level: '中风险' },
          { area: '性能影响', level: '低风险' },
          { area: '接口兼容', level: '高风险' },
          { area: '数据安全', level: '中风险' }
        ],
        quality: {
          coverage: 85,
          completeness: 92
        }
      }
    }
  },
  computed: {
    canPreview() {
      return this.resultFiles.some(file => this.canPreviewFile(file));
    }
  },
  watch: {
    generationResult: {
      handler(newResult) {
        if (newResult) {
          this.loadResultFiles();
        }
      },
      immediate: true
    }
  },
  methods: {
    loadResultFiles() {
      if (!this.generationResult?.preview?.files) {
        return;
      }
      
      // 模拟文件信息
      this.resultFiles = this.generationResult.preview.files.map((fileName, index) => ({
        id: index + 1,
        name: fileName,
        type: this.getFileTypeFromName(fileName),
        size: Math.floor(Math.random() * 1000000) + 50000, // 模拟文件大小
        description: this.getFileDescription(fileName),
        downloading: false,
        url: `/api/regression/download/${this.generationResult.taskId}/${fileName}`
      }));
    },
    
    getFileTypeFromName(fileName) {
      if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
        return 'excel';
      } else if (fileName.endsWith('.txt')) {
        return 'text';
      } else if (fileName.endsWith('.docx') || fileName.endsWith('.doc')) {
        return 'word';
      }
      return 'other';
    },
    
    getFileDescription(fileName) {
      const descriptions = {
        '项目信息表.xlsx': '包含项目基本信息、测试人员配置、软件信息等',
        '回归测试策划表.xlsx': '测试策略、测试计划、资源分配等策划信息',
        '需求分析表.xlsx': '详细的需求分析结果和测试需求提取',
        '测试用例表.xlsx': '完整的测试用例设计和执行计划',
        '问题单表.xlsx': '问题跟踪和缺陷管理模板',
        '测试用例详细表.xlsx': '详细的测试用例设计，包含步骤和预期结果',
        '自动化测试脚本.txt': '自动化测试脚本代码和执行说明',
        '测试数据模板.xlsx': '测试数据准备模板和数据驱动配置'
      };
      return descriptions[fileName] || '生成的测试文档';
    },
    
    getFileIcon(type) {
      const icons = {
        excel: 'Document',
        text: 'Document',
        word: 'Document',
        other: 'Document'
      };
      return icons[type] || 'Document';
    },
    
    getFileTypeColor(type) {
      const colors = {
        excel: 'success',
        text: 'info',
        word: 'primary',
        other: 'warning'
      };
      return colors[type] || 'info';
    },
    
    getFileTypeText(type) {
      const texts = {
        excel: 'Excel',
        text: '文本',
        word: 'Word',
        other: '其他'
      };
      return texts[type] || '未知';
    },
    
    canPreviewFile(file) {
      return file.type === 'text';
    },
    
    async downloadFile(file) {
      if (!file) return;
      
      file.downloading = true;
      try {
        // 模拟下载
        await this.delay(1000);
        
        // 创建下载链接
        const link = document.createElement('a');
        link.href = file.url;
        link.download = file.name;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.$message.success(`${file.name} 下载完成`);
      } catch (error) {
        this.$message.error(`下载失败: ${error.message}`);
      } finally {
        file.downloading = false;
      }
    },
    
    async downloadAll() {
      this.isDownloadingAll = true;
      try {
        for (const file of this.resultFiles) {
          await this.downloadFile(file);
          await this.delay(500); // 避免并发下载过多
        }
        this.$message.success('所有文件下载完成');
      } catch (error) {
        this.$message.error(`批量下载失败: ${error.message}`);
      } finally {
        this.isDownloadingAll = false;
      }
    },
    
    async refreshFiles() {
      this.isRefreshing = true;
      try {
        await this.delay(1000);
        this.loadResultFiles();
        this.$message.success('文件列表已刷新');
      } catch (error) {
        this.$message.error(`刷新失败: ${error.message}`);
      } finally {
        this.isRefreshing = false;
      }
    },
    
    async previewFile(file) {
      this.previewFile = file;
      this.previewDialogVisible = true;
      
      if (file.type === 'text') {
        try {
          // 模拟获取文件内容
          await this.delay(500);
          this.previewContent = `这是 ${file.name} 的预览内容...\n\n这里会显示实际的文件内容。`;
        } catch (error) {
          this.$message.error('预览失败: ' + error.message);
        }
      }
    },
    
    previewFiles() {
      const previewableFiles = this.resultFiles.filter(file => this.canPreviewFile(file));
      if (previewableFiles.length > 0) {
        this.previewFile(previewableFiles[0]);
      }
    },
    
    async exportReport() {
      this.isExportingReport = true;
      try {
        await this.delay(2000);
        
        // 模拟导出报告
        const reportData = {
          taskId: this.generationResult.taskId,
          generationType: this.generationResult.generationType,
          summary: this.analysisDetails,
          files: this.resultFiles.map(f => ({ name: f.name, type: f.type, description: f.description }))
        };
        
        const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `回归测试报告_${this.generationResult.taskId}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        this.$message.success('测试报告导出完成');
      } catch (error) {
        this.$message.error(`导出失败: ${error.message}`);
      } finally {
        this.isExportingReport = false;
      }
    },
    
    async cleanupFiles() {
      try {
        await this.$confirm('确定要清理临时文件吗？清理后将无法重新下载。', '确认清理', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        });
        
        this.isCleaning = true;
        
        // 模拟清理过程
        await this.delay(1500);
        
        this.$message.success('临时文件清理完成');
        this.$emit('files-cleaned');
        
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error(`清理失败: ${error.message}`);
        }
      } finally {
        this.isCleaning = false;
      }
    },
    
    reset() {
      this.$emit('reset');
    },
    
    getGenerationTypeName() {
      const typeMap = {
        'planning': '仅策划表',
        'forms': '完整表单',
        'testcases': '测试用例'
      };
      return typeMap[this.generationResult?.generationType] || '未知类型';
    },
    
    getStatusType() {
      return 'success'; // 成功状态
    },
    
    getStatusText() {
      return '生成完成';
    },
    
    getPriorityStrategyText() {
      const strategyMap = {
        'risk-driven': '风险驱动',
        'business-critical': '业务重要性',
        'change-impact': '变更影响度',
        'defect-history': '历史缺陷率'
      };
      return strategyMap[this.generationResult?.advancedOptions?.priorityStrategy] || '未设置';
    },
    
    getRiskTypeColor(level) {
      const colorMap = {
        '高风险': 'danger',
        '中风险': 'warning',
        '低风险': 'success'
      };
      return colorMap[level] || 'info';
    },
    
    formatDate(timestamp) {
      if (!timestamp) return '未知时间';
      return new Date(timestamp).toLocaleString('zh-CN');
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    }
  },
  
  mounted() {
    if (this.generationResult) {
      this.loadResultFiles();
    }
  }
}
</script>

<style scoped>
.regression-result-download {
  padding: 20px;
}

.no-result {
  text-align: center;
  padding: 50px;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.summary-card h4,
.files-card h4,
.details-card h4 {
  margin-top: 0;
  color: #409eff;
}

.advanced-summary {
  margin-top: 20px;
}

.advanced-summary h5 {
  margin-bottom: 10px;
  color: #606266;
}

.files-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.files-actions {
  display: flex;
  gap: 10px;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: #409eff;
}

.file-description {
  color: #606266;
  font-size: 14px;
}

.actions-card {
  text-align: center;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.preview-content {
  max-height: 400px;
  overflow-y: auto;
}

.text-preview pre {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.excel-preview,
.unsupported-preview {
  text-align: center;
  padding: 50px;
}

@media (max-width: 768px) {
  .files-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .files-actions {
    justify-content: center;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .action-buttons .el-button {
    width: 200px;
  }
}
</style> 