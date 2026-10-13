<template>
  <div class="regression-form-generation">
    <div class="generation-options">
      <el-card class="option-card">
        <h4>生成选项</h4>
        <el-radio-group v-model="generationType" @change="handleGenerationTypeChange">
          <el-radio label="planning">仅生成策划表</el-radio>
          <el-radio label="forms">生成完整表单</el-radio>
          <el-radio label="testcases">生成测试用例</el-radio>
        </el-radio-group>
        <div class="option-description">
          <p v-if="generationType === 'planning'">
            仅生成回归测试策划表，包含测试计划和测试方案。
          </p>
          <p v-else-if="generationType === 'forms'">
            生成完整的回归测试表单，包括项目信息表、策划表、需求分析表、用例生成表、问题单表等。
          </p>
          <p v-else>
            基于需求分析结果，生成详细的回归测试用例和测试脚本。
          </p>
        </div>
      </el-card>

      <el-card class="advanced-options" v-if="generationType === 'forms' || generationType === 'testcases'">
        <h4>高级选项</h4>
        <el-form label-width="140px">
          <el-form-item label="测试优先级策略">
            <el-select v-model="advancedOptions.priorityStrategy" style="width: 100%">
              <el-option label="风险驱动" value="risk-driven"></el-option>
              <el-option label="业务重要性" value="business-critical"></el-option>
              <el-option label="变更影响度" value="change-impact"></el-option>
              <el-option label="历史缺陷率" value="defect-history"></el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item label="测试覆盖策略">
            <el-checkbox-group v-model="advancedOptions.coverageStrategy">
              <el-checkbox label="功能覆盖">功能测试覆盖</el-checkbox>
              <el-checkbox label="接口覆盖">接口测试覆盖</el-checkbox>
              <el-checkbox label="性能覆盖">性能测试覆盖</el-checkbox>
              <el-checkbox label="安全覆盖">安全测试覆盖</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          
          <el-form-item label="自动化建议">
            <el-switch v-model="advancedOptions.automationSuggestion" active-text="启用" inactive-text="禁用"></el-switch>
          </el-form-item>
          
          <el-form-item label="历史数据参考">
            <el-switch v-model="advancedOptions.useHistoryData" active-text="启用" inactive-text="禁用"></el-switch>
          </el-form-item>
        </el-form>
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

    <!-- 生成预览 -->
    <div v-if="generationPreview && !isGenerating" class="generation-preview">
      <el-card class="preview-card">
        <h4>生成预览</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="生成类型">{{ getGenerationTypeName() }}</el-descriptions-item>
          <el-descriptions-item label="预计文件数">{{ generationPreview.estimatedFiles }}</el-descriptions-item>
          <el-descriptions-item label="测试用例数">{{ generationPreview.testCaseCount }}</el-descriptions-item>
          <el-descriptions-item label="预计时间">{{ generationPreview.estimatedTime }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="preview-files">
          <h5>将生成的文件：</h5>
          <el-tag 
            v-for="file in generationPreview.files" 
            :key="file" 
            type="info" 
            style="margin: 5px;">
            {{ file }}
          </el-tag>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RegressionFormGeneration',
  props: {
    basicInfo: {
      type: Object,
      required: true
    },
    uploadInfo: {
      type: Object,
      required: true
    },
    analysisResult: {
      type: Object,
      default: null
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
      taskId: null,
      generationPreview: null,
      advancedOptions: {
        priorityStrategy: 'risk-driven',
        coverageStrategy: ['功能覆盖'],
        automationSuggestion: true,
        useHistoryData: false
      }
    }
  },
  computed: {
    canGenerate() {
      return this.basicInfo.softwareName && 
             this.basicInfo.testManager && 
             this.uploadInfo.impactAnalysisFile;
    }
  },
  watch: {
    generationType: {
      handler() {
        this.updateGenerationPreview();
      },
      immediate: true
    },
    advancedOptions: {
      handler() {
        this.updateGenerationPreview();
      },
      deep: true
    }
  },
  methods: {
    handleGenerationTypeChange(value) {
      this.generationType = value;
    },
    
    updateGenerationPreview() {
      if (!this.canGenerate) {
        this.generationPreview = null;
        return;
      }
      
      const baseFiles = ['项目信息表.xlsx'];
      let files = [...baseFiles];
      let testCaseCount = 0;
      let estimatedTime = '1-2分钟';
      
      if (this.generationType === 'planning') {
        files.push('回归测试策划表.xlsx');
        testCaseCount = 0;
        estimatedTime = '30秒-1分钟';
      } else if (this.generationType === 'forms') {
        files.push(
          '回归测试策划表.xlsx',
          '需求分析表.xlsx',
          '测试用例表.xlsx',
          '问题单表.xlsx'
        );
        testCaseCount = this.analysisResult?.testRequirements || 15;
        estimatedTime = '2-3分钟';
      } else if (this.generationType === 'testcases') {
        files.push(
          '测试用例详细表.xlsx',
          '自动化测试脚本.txt',
          '测试数据模板.xlsx'
        );
        testCaseCount = (this.analysisResult?.testRequirements || 15) * 2;
        estimatedTime = '3-5分钟';
      }
      
      this.generationPreview = {
        estimatedFiles: files.length,
        testCaseCount,
        estimatedTime,
        files
      };
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
        this.addProgressDetail('开始生成回归测试表单', 'primary');
        
        // 模拟生成过程
        await this.simulateGeneration();
        
        this.generationProgress = 100;
        this.generationStatus = 'success';
        this.generationMessage = '生成完成！';
        this.addProgressDetail('回归测试表单生成完成', 'success');
        
        this.$emit('generation-complete', {
          taskId: this.taskId,
          generationType: this.generationType,
          advancedOptions: this.advancedOptions,
          preview: this.generationPreview
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
      const steps = this.getGenerationSteps();
      
      this.taskId = 'regression_task_' + Date.now();
      
      for (const step of steps) {
        await this.delay(1200); // 模拟处理时间
        this.generationProgress = step.progress;
        this.generationMessage = step.message;
        this.addProgressDetail(step.message, 'primary');
      }
    },
    
    getGenerationSteps() {
      const baseSteps = [
        { message: '解析影响域分析报告', progress: 15 },
        { message: '提取测试需求', progress: 30 }
      ];
      
      if (this.generationType === 'planning') {
        return [
          ...baseSteps,
          { message: '生成测试策划表', progress: 60 },
          { message: '整理策划文档', progress: 80 },
          { message: '完成策划表生成', progress: 100 }
        ];
      } else if (this.generationType === 'forms') {
        return [
          ...baseSteps,
          { message: '生成项目信息表', progress: 45 },
          { message: '生成测试策划表', progress: 60 },
          { message: '生成需求分析表', progress: 75 },
          { message: '生成测试用例表', progress: 90 },
          { message: '整理所有表单文件', progress: 100 }
        ];
      } else {
        return [
          ...baseSteps,
          { message: '分析测试场景', progress: 45 },
          { message: '生成测试用例', progress: 60 },
          { message: '生成自动化脚本', progress: 75 },
          { message: '生成测试数据', progress: 90 },
          { message: '整理测试用例文件', progress: 100 }
        ];
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
    
    getGenerationTypeName() {
      const typeMap = {
        'planning': '仅策划表',
        'forms': '完整表单',
        'testcases': '测试用例'
      };
      return typeMap[this.generationType] || '未知类型';
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
      this.generationPreview = null;
      this.advancedOptions = {
        priorityStrategy: 'risk-driven',
        coverageStrategy: ['功能覆盖'],
        automationSuggestion: true,
        useHistoryData: false
      };
    }
  }
}
</script>

<style scoped>
.regression-form-generation {
  padding: 20px;
}

.generation-options {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.option-card,
.advanced-options,
.progress-card,
.action-card,
.preview-card {
  margin-bottom: 20px;
}

.option-card h4,
.advanced-options h4,
.progress-card h4,
.preview-card h4 {
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

.generation-preview {
  margin-top: 30px;
}

.preview-files {
  margin-top: 20px;
}

.preview-files h5 {
  margin-bottom: 10px;
  color: #606266;
}

.el-radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.el-radio {
  margin-right: 0;
}

.el-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.advanced-options .el-form-item {
  margin-bottom: 20px;
}
</style> 