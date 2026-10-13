<template>
  <div class="regression-document-upload">
    <el-form :model="uploadInfo" :rules="uploadRules" ref="uploadForm" label-width="120px">
      <el-form-item label="影响域分析报告" prop="impactAnalysisFile">
        <el-upload
          class="upload-demo"
          drag
          :auto-upload="false"
          :on-change="handleImpactAnalysisFileChange"
          :file-list="impactAnalysisFileList"
          accept=".docx,.doc,.pdf"
          :limit="1">
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将影响域分析报告拖拽到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .docx/.doc/.pdf 格式，文件大小不超过 50MB
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <el-form-item label="是否有策划表">
        <el-switch v-model="uploadInfo.hasPlanning" active-text="是" inactive-text="否"></el-switch>
      </el-form-item>

      <el-form-item v-if="uploadInfo.hasPlanning" label="策划表文档" prop="planningFile">
        <el-upload
          class="upload-demo"
          drag
          :auto-upload="false"
          :on-change="handlePlanningFileChange"
          :file-list="planningFileList"
          accept=".xlsx,.xls"
          :limit="1">
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将策划表拖拽到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .xlsx/.xls 格式，文件大小不超过 20MB
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <el-form-item label="是否有历史测试数据">
        <el-switch v-model="uploadInfo.hasHistoryData" active-text="是" inactive-text="否"></el-switch>
      </el-form-item>

      <el-form-item v-if="uploadInfo.hasHistoryData" label="历史测试数据" prop="historyDataFiles">
        <el-upload
          class="upload-demo"
          drag
          :auto-upload="false"
          :on-change="handleHistoryDataFileChange"
          :file-list="historyDataFileList"
          accept=".xlsx,.xls,.json,.xml"
          :limit="5"
          multiple>
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将历史测试数据拖拽到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .xlsx/.xls/.json/.xml 格式，最多5个文件，每个文件不超过 10MB
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <div class="upload-summary" v-if="uploadedFiles.length > 0">
        <h4>已上传文件</h4>
        <el-table :data="uploadedFiles" style="width: 100%">
          <el-table-column prop="name" label="文件名" min-width="250"></el-table-column>
          <el-table-column prop="size" label="文件大小" width="120"></el-table-column>
          <el-table-column prop="type" label="文件类型" width="150"></el-table-column>
          <el-table-column prop="category" label="文档类型" width="120"></el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button size="small" type="danger" @click="removeFile(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="upload-tips">
        <el-alert
          title="文档上传说明"
          type="info"
          :closable="false"
          show-icon>
          <ul>
            <li>影响域分析报告：必须上传，用于分析代码变更的影响范围</li>
            <li>策划表：可选，如果已有测试策划表可上传以提高生成质量</li>
            <li>历史测试数据：可选，用于参考历史测试结果和趋势分析</li>
          </ul>
        </el-alert>
      </div>
    </el-form>
  </div>
</template>

<script>
import { UploadFilled } from '@element-plus/icons-vue'

export default {
  name: 'RegressionDocumentUpload',
  components: {
    UploadFilled
  },
  props: {
    modelValue: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['update:modelValue', 'validate'],
  data() {
    return {
      uploadInfo: {
        impactAnalysisFile: null,
        planningFile: null,
        historyDataFiles: [],
        hasPlanning: false,
        hasHistoryData: false
      },
      impactAnalysisFileList: [],
      planningFileList: [],
      historyDataFileList: [],
      uploadRules: {
        impactAnalysisFile: [
          { required: true, message: '请上传影响域分析报告', trigger: 'change' }
        ]
      }
    }
  },
  computed: {
    uploadedFiles() {
      const files = [];
      
      if (this.impactAnalysisFileList.length > 0) {
        files.push({
          name: this.impactAnalysisFileList[0].name,
          size: this.formatFileSize(this.impactAnalysisFileList[0].size),
          type: this.getFileType(this.impactAnalysisFileList[0].name),
          category: '影响域分析报告'
        });
      }
      
      if (this.planningFileList.length > 0) {
        files.push({
          name: this.planningFileList[0].name,
          size: this.formatFileSize(this.planningFileList[0].size),
          type: this.getFileType(this.planningFileList[0].name),
          category: '策划表'
        });
      }
      
      this.historyDataFileList.forEach(file => {
        files.push({
          name: file.name,
          size: this.formatFileSize(file.size),
          type: this.getFileType(file.name),
          category: '历史测试数据'
        });
      });
      
      return files;
    }
  },
  watch: {
    modelValue: {
      handler(newVal) {
        this.uploadInfo = { ...this.uploadInfo, ...newVal };
      },
      deep: true,
      immediate: true
    },
    uploadInfo: {
      handler(newVal) {
        this.$emit('update:modelValue', newVal);
      },
      deep: true
    }
  },
  methods: {
    handleImpactAnalysisFileChange(file, fileList) {
      if (file.size > 50 * 1024 * 1024) {
        this.$message.error('文件大小不能超过50MB');
        return;
      }
      
      this.impactAnalysisFileList = fileList;
      this.uploadInfo.impactAnalysisFile = file.raw;
      this.validateField('impactAnalysisFile');
    },
    
    handlePlanningFileChange(file, fileList) {
      if (file.size > 20 * 1024 * 1024) {
        this.$message.error('文件大小不能超过20MB');
        return;
      }
      
      this.planningFileList = fileList;
      this.uploadInfo.planningFile = file.raw;
    },
    
    handleHistoryDataFileChange(file, fileList) {
      if (file.size > 10 * 1024 * 1024) {
        this.$message.error('文件大小不能超过10MB');
        return;
      }
      
      this.historyDataFileList = fileList;
      this.uploadInfo.historyDataFiles = fileList.map(f => f.raw);
    },
    
    removeFile(file) {
      if (file.category === '影响域分析报告') {
        this.impactAnalysisFileList = [];
        this.uploadInfo.impactAnalysisFile = null;
      } else if (file.category === '策划表') {
        this.planningFileList = [];
        this.uploadInfo.planningFile = null;
      } else if (file.category === '历史测试数据') {
        const index = this.historyDataFileList.findIndex(f => f.name === file.name);
        if (index > -1) {
          this.historyDataFileList.splice(index, 1);
          this.uploadInfo.historyDataFiles = this.historyDataFileList.map(f => f.raw);
        }
      }
    },
    
    getFileType(filename) {
      const extension = filename.split('.').pop().toLowerCase();
      const typeMap = {
        'docx': 'Word文档',
        'doc': 'Word文档',
        'pdf': 'PDF文档',
        'xlsx': 'Excel表格',
        'xls': 'Excel表格',
        'json': 'JSON数据',
        'xml': 'XML数据'
      };
      return typeMap[extension] || '未知类型';
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    validateField(field) {
      this.$refs.uploadForm.validateField(field);
    },
    
    validate() {
      return this.$refs.uploadForm.validate();
    },
    
    resetForm() {
      this.$refs.uploadForm.resetFields();
      this.impactAnalysisFileList = [];
      this.planningFileList = [];
      this.historyDataFileList = [];
    }
  }
}
</script>

<style scoped>
.regression-document-upload {
  padding: 20px;
}

.upload-demo {
  width: 100%;
}

.upload-summary {
  margin-top: 30px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.upload-summary h4 {
  margin-top: 0;
  color: #409eff;
}

.upload-tips {
  margin-top: 20px;
}

.upload-tips ul {
  margin: 10px 0;
  padding-left: 20px;
}

.upload-tips li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.el-upload__text {
  color: #606266;
}

.el-upload__tip {
  color: #909399;
  font-size: 12px;
}
</style> 