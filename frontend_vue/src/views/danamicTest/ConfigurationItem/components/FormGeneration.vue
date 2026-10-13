<template>
  <div class="form-generation">
    <div class="generation-options">
      <el-card class="option-card">
        <h4>生成选项</h4>
        <el-radio-group v-model="generationType" @change="handleGenerationTypeChange">
          <el-radio label="planning">仅生成策划表</el-radio>
          <el-radio label="forms">生成完整表单</el-radio>
        </el-radio-group>
        <div class="option-description">
          <p v-if="generationType === 'planning'">
            仅生成测试策划表，包含测试计划和测试方案。
          </p>
          <p v-else>
            生成完整的配置项测试表单，包括项目信息表、策划表、需求分析表、用例生成表、问题单表等。
          </p>
        </div>
      </el-card>

      <el-card class="progress-card" v-if="isGenerating">
        <h4>生成进度</h4>
        <el-progress :percentage="generationProgress" :status="generationStatus"></el-progress>
        <p class="progress-text">{{ generationMessage }}</p>
        <div class="progress-details" v-if="progressDetails.length > 0">
          <el-timeline>
            <el-timeline-item
              v-for="(detail, index) in progressDetails"
              :key="index"
              :timestamp="detail.timestamp"
              :type="detail.type">
              {{ detail.message }}
            </el-timeline-item>
          </el-timeline>
        </div>
      </el-card>

      <el-card class="action-card">
        <el-button 
          type="primary" 
          size="large" 
          @click="startGeneration"
          :loading="isGenerating"
          :disabled="!canGenerate">
          {{ isGenerating ? '正在生成...' : '开始生成' }}
        </el-button>
        <el-button 
          v-if="!isGenerating && taskId" 
          type="success" 
          size="large" 
          @click="checkStatus">
          检查状态
        </el-button>
        <el-button 
          v-if="isGenerating" 
          type="warning" 
          size="large" 
          @click="cancelGeneration">
          取消生成
        </el-button>
      </el-card>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FormGeneration',
  props: {
    basicInfo: {
      type: Object,
      required: true
    },
    uploadInfo: {
      type: Object,
      required: true
    }
  },
  emits: ['generation-complete', 'generation-error'],
  data() {
    return {
      generationType: 'forms',
      isGenerating: false,
      generationProgress: 0,
      generationStatus: '',
      generationMessage: '',
      progressDetails: [],
      taskId: null
    }
  },
  computed: {
    canGenerate() {
      return this.basicInfo.softwareName && 
             this.basicInfo.testManager && 
             this.uploadInfo.requirementFile;
    }
  },
  methods: {
    handleGenerationTypeChange(value) {
      this.generationType = value;
    },
    
    async startGeneration() {
      if (!this.canGenerate) {
        this.$message.error('请先完成基本信息填写和文档上传');
        return;
      }
      
      this.isGenerating = true;
      this.generationProgress = 0;
      this.generationStatus = '';
      this.generationMessage = '正在准备生成...';
      this.progressDetails = [];
      
      try {
        this.addProgressDetail('开始生成配置项测试表单', 'primary');
        
        // 模拟生成过程
        await this.simulateGeneration();
        
        this.generationProgress = 100;
        this.generationStatus = 'success';
        this.generationMessage = '生成完成！';
        this.addProgressDetail('表单生成完成', 'success');
        
        this.$emit('generation-complete', {
          taskId: this.taskId,
          generationType: this.generationType
        });
        
      } catch (error) {
        this.generationProgress = 0;
        this.generationStatus = 'exception';
        this.generationMessage = '生成失败：' + error.message;
        this.addProgressDetail('生成失败：' + error.message, 'danger');
        
        this.$emit('generation-error', error);
      } finally {
        this.isGenerating = false;
      }
    },
    
    async simulateGeneration() {
      // 模拟生成过程的各个步骤
      const steps = [
        { message: '解析需求文档', progress: 20 },
        { message: '分析配置项', progress: 40 },
        { message: '生成测试用例', progress: 60 },
        { message: '生成表单文件', progress: 80 },
        { message: '整理输出文件', progress: 100 }
      ];
      
      this.taskId = 'task_' + Date.now();
      
      for (const step of steps) {
        await this.delay(1000); // 模拟处理时间
        this.generationProgress = step.progress;
        this.generationMessage = step.message;
        this.addProgressDetail(step.message, 'primary');
      }
    },
    
    async checkStatus() {
      if (!this.taskId) {
        this.$message.warning('没有正在进行的任务');
        return;
      }
      
      try {
        // 这里应该调用实际的状态检查API
        this.$message.success('任务状态检查完成');
      } catch (error) {
        this.$message.error('状态检查失败：' + error.message);
      }
    },
    
    cancelGeneration() {
      this.isGenerating = false;
      this.generationProgress = 0;
      this.generationStatus = '';
      this.generationMessage = '';
      this.addProgressDetail('用户取消生成', 'warning');
    },
    
    addProgressDetail(message, type = 'primary') {
      this.progressDetails.push({
        message,
        type,
        timestamp: new Date().toLocaleTimeString()
      });
    },
    
    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },
    
    reset() {
      this.generationType = 'forms';
      this.isGenerating = false;
      this.generationProgress = 0;
      this.generationStatus = '';
      this.generationMessage = '';
      this.progressDetails = [];
      this.taskId = null;
    }
  }
}
</script>

<style scoped>
.form-generation {
  padding: 20px;
}

.generation-options {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.option-card,
.progress-card,
.action-card {
  margin-bottom: 20px;
}

.option-card h4,
.progress-card h4 {
  margin-top: 0;
  color: #409eff;
}

.option-description {
  margin-top: 15px;
  padding: 10px;
  background: #f0f9ff;
  border-radius: 4px;
  color: #606266;
}

.progress-text {
  margin: 10px 0;
  font-weight: 500;
  color: #409eff;
}

.progress-details {
  margin-top: 20px;
  max-height: 200px;
  overflow-y: auto;
}

.action-card {
  text-align: center;
}

.action-card .el-button {
  margin: 0 10px;
}

.el-radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.el-radio {
  margin-right: 0;
}
</style> 