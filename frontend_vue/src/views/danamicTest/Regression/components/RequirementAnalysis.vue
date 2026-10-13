<template>
  <div class="requirement-analysis">
    <div class="analysis-options">
      <el-card class="option-card">
        <h4>需求分析选项</h4>
        <el-radio-group v-model="analysisType" @change="handleAnalysisTypeChange">
          <el-radio label="original">原始数据分析</el-radio>
          <el-radio label="final">最终需求提取</el-radio>
          <el-radio label="mapping">函数映射分析</el-radio>
        </el-radio-group>
        <div class="option-description">
          <p v-if="analysisType === 'original'">
            对影响域分析报告进行原始数据分析，提取基础的变更信息和影响范围。
          </p>
          <p v-else-if="analysisType === 'final'">
            基于原始分析结果，提取最终的测试需求和关键测试点。
          </p>
          <p v-else>
            分析函数调用关系和映射，生成详细的影响域图谱。
          </p>
        </div>
      </el-card>

      <el-card class="progress-card" v-if="isAnalyzing">
        <h4>分析进度</h4>
        <el-progress :percentage="analysisProgress" :status="analysisStatus"></el-progress>
        <p class="progress-text">{{ analysisMessage }}</p>
        <div class="analysis-details" v-if="analysisSteps.length > 0">
          <el-timeline>
            <el-timeline-item
              v-for="(step, index) in analysisSteps"
              :key="index"
              :timestamp="step.timestamp"
              :type="step.type">
              {{ step.message }}
            </el-timeline-item>
          </el-timeline>
        </div>
      </el-card>

      <el-card class="action-card">
        <el-button 
          type="primary" 
          size="large" 
          @click="startAnalysis"
          :loading="isAnalyzing"
          :disabled="!canAnalyze">
          {{ isAnalyzing ? '正在分析...' : '开始分析' }}
        </el-button>
        <el-button 
          v-if="!isAnalyzing && analysisResult" 
          type="success" 
          size="large" 
          @click="viewResult">
          查看结果
        </el-button>
        <el-button 
          v-if="isAnalyzing" 
          type="warning" 
          size="large" 
          @click="cancelAnalysis">
          取消分析
        </el-button>
      </el-card>
    </div>

    <!-- 分析结果展示 -->
    <div v-if="analysisResult && !isAnalyzing" class="analysis-result">
      <el-card class="result-card">
        <h4>分析结果</h4>
        <el-tabs v-model="activeTab" type="border-card">
          <el-tab-pane label="概览" name="overview">
            <div class="overview-content">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="分析类型">{{ getAnalysisTypeName() }}</el-descriptions-item>
                <el-descriptions-item label="分析时间">{{ analysisResult.analysisTime }}</el-descriptions-item>
                <el-descriptions-item label="影响文件数">{{ analysisResult.affectedFiles }}</el-descriptions-item>
                <el-descriptions-item label="影响函数数">{{ analysisResult.affectedFunctions }}</el-descriptions-item>
                <el-descriptions-item label="测试需求数">{{ analysisResult.testRequirements }}</el-descriptions-item>
                <el-descriptions-item label="风险等级">
                  <el-tag :type="getRiskLevelType()">{{ analysisResult.riskLevel }}</el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="详细结果" name="details">
            <div class="details-content">
              <el-table :data="analysisResult.details" style="width: 100%" max-height="400">
                <el-table-column prop="module" label="模块" width="150"></el-table-column>
                <el-table-column prop="function" label="函数/方法" width="200"></el-table-column>
                <el-table-column prop="impact" label="影响程度" width="120">
                  <template #default="scope">
                    <el-tag :type="getImpactType(scope.row.impact)">{{ scope.row.impact }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="testRequirement" label="测试需求" min-width="300"></el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="建议" name="suggestions">
            <div class="suggestions-content">
              <el-alert
                v-for="(suggestion, index) in analysisResult.suggestions"
                :key="index"
                :title="suggestion.title"
                :type="suggestion.type"
                :description="suggestion.description"
                show-icon
                style="margin-bottom: 15px">
              </el-alert>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RequirementAnalysis',
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
  emits: ['analysis-complete', 'analysis-error'],
  data() {
    return {
      analysisType: 'original',
      isAnalyzing: false,
      analysisProgress: 0,
      analysisStatus: '',
      analysisMessage: '',
      analysisSteps: [],
      analysisResult: null,
      activeTab: 'overview'
    }
  },
  computed: {
    canAnalyze() {
      return this.basicInfo.softwareName && 
             this.uploadInfo.impactAnalysisFile;
    }
  },
  methods: {
    handleAnalysisTypeChange(value) {
      this.analysisType = value;
    },
    
    async startAnalysis() {
      if (!this.canAnalyze) {
        this.$message.error('请先完成基本信息填写和文档上传');
        return;
      }
      
      this.isAnalyzing = true;
      this.analysisProgress = 0;
      this.analysisStatus = '';
      this.analysisMessage = '正在准备分析...';
      this.analysisSteps = [];
      this.analysisResult = null;
      
      try {
        this.addAnalysisStep('开始需求分析', 'primary');
        
        // 模拟分析过程
        await this.simulateAnalysis();
        
        this.analysisProgress = 100;
        this.analysisStatus = 'success';
        this.analysisMessage = '分析完成！';
        this.addAnalysisStep('需求分析完成', 'success');
        
        // 生成模拟分析结果
        this.generateAnalysisResult();
        
        this.$emit('analysis-complete', {
          analysisType: this.analysisType,
          result: this.analysisResult
        });
        
      } catch (error) {
        this.analysisProgress = 0;
        this.analysisStatus = 'exception';
        this.analysisMessage = '分析失败：' + error.message;
        this.addAnalysisStep('分析失败：' + error.message, 'danger');
        
        this.$emit('analysis-error', error);
      } finally {
        this.isAnalyzing = false;
      }
    },
    
    async simulateAnalysis() {
      const steps = this.getAnalysisSteps();
      
      for (const step of steps) {
        await this.delay(1500); // 模拟处理时间
        this.analysisProgress = step.progress;
        this.analysisMessage = step.message;
        this.addAnalysisStep(step.message, 'primary');
      }
    },
    
    getAnalysisSteps() {
      const baseSteps = [
        { message: '解析影响域分析报告', progress: 20 },
        { message: '提取变更信息', progress: 40 }
      ];
      
      if (this.analysisType === 'original') {
        return [
          ...baseSteps,
          { message: '分析原始数据结构', progress: 60 },
          { message: '生成基础分析报告', progress: 80 },
          { message: '整理分析结果', progress: 100 }
        ];
      } else if (this.analysisType === 'final') {
        return [
          ...baseSteps,
          { message: '提取最终测试需求', progress: 60 },
          { message: '生成测试点清单', progress: 80 },
          { message: '整理需求分析结果', progress: 100 }
        ];
      } else {
        return [
          ...baseSteps,
          { message: '分析函数调用关系', progress: 50 },
          { message: '构建影响域图谱', progress: 70 },
          { message: '生成映射分析报告', progress: 90 },
          { message: '整理映射结果', progress: 100 }
        ];
      }
    },
    
    generateAnalysisResult() {
      // 模拟生成分析结果
      this.analysisResult = {
        analysisTime: new Date().toLocaleString(),
        affectedFiles: Math.floor(Math.random() * 50) + 10,
        affectedFunctions: Math.floor(Math.random() * 200) + 50,
        testRequirements: Math.floor(Math.random() * 30) + 15,
        riskLevel: ['低', '中', '高'][Math.floor(Math.random() * 3)],
        details: this.generateAnalysisDetails(),
        suggestions: this.generateSuggestions()
      };
    },
    
    generateAnalysisDetails() {
      const modules = ['用户管理', '订单处理', '支付系统', '库存管理', '报表生成'];
      const functions = ['登录验证', '数据校验', '业务处理', '数据存储', '结果返回'];
      const impacts = ['高', '中', '低'];
      
      return Array.from({ length: 8 }, (_, i) => ({
        module: modules[Math.floor(Math.random() * modules.length)],
        function: functions[Math.floor(Math.random() * functions.length)] + `_${i + 1}`,
        impact: impacts[Math.floor(Math.random() * impacts.length)],
        testRequirement: `需要对${functions[Math.floor(Math.random() * functions.length)]}功能进行回归测试，确保变更不影响原有功能`
      }));
    },
    
    generateSuggestions() {
      const suggestions = [
        {
          title: '优先测试建议',
          type: 'warning',
          description: '建议优先测试核心业务流程和高风险变更区域'
        },
        {
          title: '测试覆盖建议',
          type: 'info',
          description: '建议增加边界条件和异常场景的测试覆盖'
        },
        {
          title: '自动化测试建议',
          type: 'success',
          description: '对于重复性高的测试场景，建议采用自动化测试'
        }
      ];
      
      return suggestions.slice(0, Math.floor(Math.random() * 3) + 1);
    },
    
    viewResult() {
      // 滚动到结果区域
      this.$nextTick(() => {
        const resultElement = this.$el.querySelector('.analysis-result');
        if (resultElement) {
          resultElement.scrollIntoView({ behavior: 'smooth' });
        }
      });
    },
    
    cancelAnalysis() {
      this.isAnalyzing = false;
      this.analysisProgress = 0;
      this.analysisStatus = '';
      this.analysisMessage = '';
      this.addAnalysisStep('用户取消分析', 'warning');
    },
    
    addAnalysisStep(message, type = 'primary') {
      this.analysisSteps.push({
        message,
        type,
        timestamp: new Date().toLocaleTimeString()
      });
    },
    
    getAnalysisTypeName() {
      const typeMap = {
        'original': '原始数据分析',
        'final': '最终需求提取',
        'mapping': '函数映射分析'
      };
      return typeMap[this.analysisType] || '未知类型';
    },
    
    getRiskLevelType() {
      const levelMap = {
        '低': 'success',
        '中': 'warning',
        '高': 'danger'
      };
      return levelMap[this.analysisResult?.riskLevel] || 'info';
    },
    
    getImpactType(impact) {
      const impactMap = {
        '低': 'info',
        '中': 'warning',
        '高': 'danger'
      };
      return impactMap[impact] || 'info';
    },
    
    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },
    
    reset() {
      this.analysisType = 'original';
      this.isAnalyzing = false;
      this.analysisProgress = 0;
      this.analysisStatus = '';
      this.analysisMessage = '';
      this.analysisSteps = [];
      this.analysisResult = null;
      this.activeTab = 'overview';
    }
  }
}
</script>

<style scoped>
.requirement-analysis {
  padding: 20px;
}

.analysis-options {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 30px;
}

.option-card,
.progress-card,
.action-card {
  margin-bottom: 20px;
}

.option-card h4,
.progress-card h4,
.result-card h4 {
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

.analysis-details {
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

.analysis-result {
  margin-top: 30px;
}

.overview-content,
.details-content,
.suggestions-content {
  padding: 20px;
}

.el-radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.el-radio {
  margin-right: 0;
}

.el-descriptions {
  margin-bottom: 20px;
}
</style> 