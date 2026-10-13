<template>
  <div class="regression-test-container">
    <el-card class="main-card">
      <!-- OCR图片识别区域 -->
      <OCRImageUpload :service="regressionTestService" @dataExtracted="handleOCRDataExtracted" />

      <!-- 基本信息表单 -->
      <el-form 
        ref="basicInfoForm" 
        :model="basicInfo" 
        :rules="basicInfoRules" 
        label-width="120px"
        class="basic-info-form">
        <h3>基本信息</h3>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="所属领域" prop="domain">
              <el-select 
                v-model="basicInfo.domain" 
                placeholder="请选择所属领域" 
                style="width: 100%" 
                filterable
                allow-create
                default-first-option
                @change="handleDomainChange"
              >
                <el-option
                  v-for="item in domains"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value">
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="测试主管" prop="testManager">
              <el-select 
                v-model="basicInfo.testManager" 
                placeholder="请选择测试主管" 
                style="width: 100%" 
                filterable
                allow-create
                default-first-option
                @change="handleTestManagerChange"
              >
                <el-option
                  v-for="item in testManagers"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value">
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="测试人员" prop="testPersonnel">
              <el-select 
                v-model="basicInfo.testPersonnel" 
                placeholder="请选择测试人员" 
                style="width: 100%" 
                filterable
                allow-create
                default-first-option
                @change="handleTestPersonnelChange"
              >
                <el-option
                  v-for="item in testPersonnels"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value">
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="开发人员" prop="developer">
              <el-select 
                v-model="basicInfo.developer" 
                placeholder="请选择开发人员" 
                style="width: 100%" 
                filterable
                allow-create
                default-first-option
                @change="handleDeveloperChange"
              >
                <el-option
                  v-for="item in developers"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value">
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
          </el-col>
          <el-col :span="8">
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="软件名称" prop="softwareName">
              <el-input v-model="basicInfo.softwareName" placeholder="请输入软件名称"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="软件版本" prop="softwareVersion">
              <el-input v-model="basicInfo.softwareVersion" placeholder="请输入软件版本"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="软件标识" prop="softwareId">
              <el-input v-model="basicInfo.softwareId" placeholder="请输入软件标识"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        

        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="检测仪标识">
              <el-radio-group v-model="basicInfo.detectorFlag">
                <el-radio label="有检测仪">有检测仪</el-radio>
                <el-radio label="无检测仪">无检测仪</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="AI分析">
              <el-switch v-model="basicInfo.aiAnalysis" active-text="开启" inactive-text="关闭"></el-switch>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="深度分析">
              <el-switch v-model="basicInfo.deepAnalysis" active-text="开启" inactive-text="关闭"></el-switch>
            </el-form-item>
          </el-col>
        </el-row>
        

      </el-form>

      <!-- 可选信息区域 -->
      <el-collapse v-model="activeCollapse" class="optional-info-section">
        <el-collapse-item title="可选信息" name="optional">
          <template #title>
            <div class="collapse-title">
              <i class="el-icon-setting"></i>
              <span>可选信息</span>
              <span class="collapse-subtitle">（飞机型号、项目总师、研制部门、主任设计师）</span>
            </div>
          </template>
          
          <el-form 
            ref="optionalInfoForm" 
            :model="optionalInfo" 
            label-width="120px"
            class="optional-info-form">
            
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="飞机型号">
                  <el-select 
                    v-model="optionalInfo.aircraftModel" 
                    placeholder="请选择飞机型号" 
                    style="width: 100%" 
                    filterable
                    allow-create
                    default-first-option
                    @change="handleAircraftModelChange"
                  >
                    <el-option
                      v-for="item in aircraftModels"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value">
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="项目总师">
                  <el-select 
                    v-model="optionalInfo.projectDirector" 
                    placeholder="请选择项目总师" 
                    style="width: 100%" 
                    filterable
                    allow-create
                    default-first-option
                    @change="handleProjectDirectorChange"
                  >
                    <el-option
                      v-for="item in projectDirectors"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value">
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="研制部门">
                  <el-select 
                    v-model="optionalInfo.developmentDepartment" 
                    placeholder="请选择研制部门" 
                    style="width: 100%" 
                    filterable
                    allow-create
                    default-first-option
                    @change="handleDevelopmentDepartmentChange"
                  >
                    <el-option
                      v-for="item in developmentDepartments"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value">
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="主任设计师">
                  <el-select 
                    v-model="optionalInfo.chiefDesigner" 
                    placeholder="请选择主任设计师" 
                    style="width: 100%" 
                    filterable
                    allow-create
                    default-first-option
                    @change="handleChiefDesignerChange"
                  >
                    <el-option
                      v-for="item in chiefDesigners"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value">
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
              </el-col>
              <el-col :span="8">
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="24">
                <!-- 代码上传区域 -->
                <el-form-item>
                  <div class="code-upload-section">
                    <div class="upload-header">
                      <img src="@/assets/icons8-upload-to-cloud-64.png" alt="上传" class="upload-icon" />
                      <span class="upload-title">代码文件上传</span>
                    </div>
                    <div class="upload-content">
                      <el-upload
                        ref="codeUpload"
                        class="code-upload"
                        :before-upload="handleCodeUpload"
                        :file-list="codeFileList"
                        :on-remove="handleCodeRemove"
                        :disabled="codeAnalysis.isUploading"
                        accept=".zip,.py,.c,.cpp,.cc,.cxx,.c++,.h,.hpp,.hxx,.h++,.java,.js,.ts,.go,.cs,.php,.rb,.swift,.kt,.rs,.scala,.m,.mm,.f,.f90,.f95"
                        :multiple="false"
                        :show-file-list="false"
                        drag>
                        <div class="upload-content-inner">
                          <div class="upload-cloud-icon" v-if="!codeAnalysis.isUploading">
                            <img src="@/assets/icons8-upload-to-cloud-64.png" alt="上传" style="width: 48px; height: 48px;" />
                          </div>
                          <el-icon class="upload-loading-icon" v-else>
                            <Loading />
                          </el-icon>
                          <div class="upload-text">
                            <p v-if="!codeAnalysis.isUploading">拖拽代码文件到此处，或<em>点击上传</em></p>
                            <p v-else>正在分析代码...</p>
                          </div>
                          <div class="upload-tip">
                            支持 .zip 压缩包或单个代码文件
                          </div>
                        </div>
                      </el-upload>
                      
                      <div v-if="codeAnalysis.hasResult" class="upload-result">
                        <div class="result-info">
                          <el-icon class="result-icon"><CircleCheck /></el-icon>
                          <span class="result-text">
                            分析完成：<strong>{{ codeAnalysis.result.total_lines || 0 }}</strong> 行代码，
                            <strong>{{ codeAnalysis.result.total_files || 0 }}</strong> 个文件
                          </span>
                        </div>
                        <div class="result-actions">
                          <el-button 
                            size="small" 
                            type="success" 
                            @click="showCodeAnalysisDetails">
                            查看详情
                          </el-button>
                          <el-button 
                            size="small" 
                            type="danger" 
                            @click="clearCodeAnalysis">
                            重新上传
                          </el-button>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-collapse-item>
      </el-collapse>

      <el-divider></el-divider>

      <!-- 文档上传 -->
      <div class="upload-section">
        <h3>影响域分析报告</h3>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-upload
              ref="impactUpload"
              class="upload-demo compact"
              drag
              :before-upload="handleImpactUpload"
              :file-list="impactFileList"
              :on-remove="handleImpactRemove"
              :disabled="uploadInfo.impactUploaded"
                              accept=".docx"
              :multiple="false">
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                <span v-if="!uploadInfo.impactUploaded">拖拽影响域分析报告到此处，或<em>点击上传</em></span>
                <span v-else>影响域分析报告已上传</span>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  仅支持 .docx 格式，文件大小不超过 50MB
                </div>
              </template>
            </el-upload>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="是否有策划表单">
              <el-switch 
                v-model="uploadInfo.hasPlanning" 
                @change="handlePlanningChange"
                active-text="有" 
                inactive-text="无">
              </el-switch>
            </el-form-item>
            
            <div v-if="uploadInfo.hasPlanning" class="planning-upload">
              <el-upload
                ref="planningUpload"
                class="upload-demo compact"
                drag
                :before-upload="handlePlanningUpload"
                :file-list="planningFileList"
                :on-remove="handlePlanningRemove"
                :disabled="uploadInfo.planningUploaded"
                accept=".xlsx"
                :multiple="false">
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  <span v-if="!uploadInfo.planningUploaded">拖拽策划表单到此处，或<em>点击上传</em></span>
                  <span v-else>策划表单已上传</span>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    仅支持 .xlsx 格式，文件大小不超过 20MB
                  </div>
                </template>
              </el-upload>
            </div>

            <div v-if="!uploadInfo.hasPlanning" class="requirement-catalog-upload">
              <p class="upload-instruction">
                请使用WPS软件打开影响域分析报告，调节目录层级（4-6级），复制目录内容到新的docx文档中。
              </p>
              <div class="example-format">
                <p>3.1.3 修改库存报表生成需求</p>
                <p>3.1.4 删除过时的手动库存盘点导入需求</p>
                <p>3.2.1 新增智能预警模块设计</p>
              </div>
              <el-upload
                ref="catalogUpload"
                class="upload-demo compact"
                drag
                :before-upload="handleCatalogUpload"
                :file-list="catalogFileList"
                :on-remove="handleCatalogRemove"
                :disabled="uploadInfo.catalogUploaded"
                accept=".docx"
                :multiple="false">
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  <span v-if="!uploadInfo.catalogUploaded">拖拽需求目录文档到此处，或<em>点击上传</em></span>
                  <span v-else>需求目录文档已上传</span>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    仅支持 .docx 格式，文件大小不超过 50MB
                  </div>
                </template>
              </el-upload>
            </div>
          </el-col>
        </el-row>

        <!-- 影响域分析报告上传状态显示 -->
        <div v-if="uploadInfo.impactUploaded" class="upload-status success">
          <el-icon class="status-icon"><circle-check /></el-icon>
          <span class="status-text">影响域分析报告上传成功：{{ uploadInfo.impactFile?.name }}</span>
          <span class="file-size">({{ formatFileSize(uploadInfo.impactFile?.size || 0) }})</span>
        </div>

        <!-- 策划表单上传状态显示 -->
        <div v-if="uploadInfo.planningUploaded" class="upload-status success">
          <el-icon class="status-icon"><circle-check /></el-icon>
          <span class="status-text">策划表单上传成功：{{ uploadInfo.planningFile?.name }}</span>
          <span class="file-size">({{ formatFileSize(uploadInfo.planningFile?.size || 0) }})</span>
        </div>

        <!-- 需求目录文档上传状态显示 -->
        <div v-if="uploadInfo.catalogUploaded" class="upload-status success">
          <el-icon class="status-icon"><circle-check /></el-icon>
          <span class="status-text">需求目录文档上传成功：{{ uploadInfo.catalogFile?.name }}</span>
          <span class="file-size">({{ formatFileSize(uploadInfo.catalogFile?.size || 0) }})</span>
        </div>
      </div>

      <el-divider></el-divider>

      <!-- 生成操作区 -->
      <div class="generation-section">
        <div class="generation-actions">
          <el-button 
            type="primary" 
            size="large"
            @click="startGeneration"
            :disabled="!canGenerate || isGenerating"
            :loading="isGenerating">
            <el-icon><magic-stick /></el-icon>
            {{ isGenerating ? '正在生成...' : '开始生成测试表单' }}
          </el-button>
          
          <!-- 下载按钮放在生成按钮右侧 -->
          <el-button 
            v-if="generationComplete && downloadFiles.length > 0"
            type="success" 
            size="large"
            @click="downloadAllFiles"
            :loading="downloadingAll"
            style="margin-left: 20px;">
            <el-icon><download /></el-icon>
            下载测试表单
          </el-button>
        </div>

        <!-- 生成进度显示 -->
        <div v-if="isGenerating" class="generation-progress">
          <el-progress 
            :percentage="generationProgress" 
            :status="generationStatus"
            :stroke-width="8">
          </el-progress>
          <p class="progress-text">{{ generationMessage }}</p>
        </div>
      </div>


    </el-card>
  </div>
</template>

<style scoped>
.regression-test-container {
  padding: 0;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

.main-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(32, 101, 209, 0.08);
  max-width: 900px;
  margin: 0 auto;
}

.basic-info-form {
  margin-bottom: 15px;
}

.basic-info-form h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid #3498db;
  font-size: 16px;
}

.upload-section {
  margin-bottom: 15px;
}

.upload-section h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid #3498db;
  font-size: 16px;
}

.upload-demo {
  margin-bottom: 15px;
}

.upload-demo.compact {
  margin-bottom: 10px;
}

.upload-demo.compact :deep(.el-upload-dragger) {
  width: 100%;
  height: 120px;
  padding: 15px;
}

.upload-demo.compact :deep(.el-icon--upload) {
  font-size: 40px;
  margin-bottom: 8px;
}

.upload-demo.compact :deep(.el-upload__text) {
  font-size: 13px;
  line-height: 1.4;
}

.upload-demo.compact :deep(.el-upload__tip) {
  font-size: 11px;
  margin-top: 5px;
}

.upload-status {
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.upload-status.success {
  background-color: #f0f9ff;
  border: 1px solid #67c23a;
  color: #67c23a;
}

.status-icon {
  font-size: 14px;
}

.status-text {
  font-weight: 500;
}

.file-size {
  color: #909399;
  font-size: 11px;
}

.generation-section {
  margin-top: 20px;
}

.generation-actions {
  text-align: center;
  margin-bottom: 15px;
}

.generation-progress {
  margin-top: 15px;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  color: #606266;
  font-size: 13px;
}

.download-section {
  margin-top: 30px;
  padding: 20px;
  text-align: center;
}

.download-actions {
  display: flex;
  justify-content: center;
}

.planning-upload {
  margin-top: 10px;
}

.requirement-catalog-upload {
  margin-top: 10px;
}

.upload-instruction {
  color: #606266;
  font-size: 12px;
  line-height: 1.4;
  margin-bottom: 8px;
}

.example-format {
  background-color: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 10px;
  border-left: 3px solid #409eff;
}

.example-format p {
  margin: 2px 0;
  font-size: 11px;
  color: #606266;
}

.el-divider {
  margin: 20px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .regression-test-container {
    padding: 8px;
  }
  
  .generation-actions .el-button {
    display: block;
    margin: 8px auto;
    width: 180px;
  }
  
  .batch-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .batch-actions .el-button {
    width: 180px;
    margin: 4px 0;
  }
}

/* 确保页面内容可以滚动 */
:deep(.el-card__body) {
  padding: 15px;
}

/* 修复可能的父级容器高度限制 */
html, body {
  height: auto !important;
  overflow: visible !important;
}

/* 表单项间距优化 */
:deep(.el-form-item) {
  margin-bottom: 15px;
}

/* 上传组件样式优化 */
:deep(.el-upload-list) {
  margin-top: 8px;
}

/* 可选信息区域样式 */
.optional-info-section {
  margin: 20px 0;
}

.optional-info-section :deep(.el-collapse-item__header) {
  padding-left: 0;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  margin-bottom: 1px;
}

.optional-info-section :deep(.el-collapse-item__wrap) {
  border: none;
  background-color: #fff;
}

.optional-info-section :deep(.el-collapse-item__content) {
  padding: 20px;
  background-color: #fafbfc;
  border: 1px solid #e9ecef;
  border-top: none;
  border-radius: 0 0 6px 6px;
}

.collapse-title {
  display: flex;
  align-items: center;
  font-weight: 500;
  color: #2c3e50;
}

.collapse-title i {
  margin-right: 8px;
  color: #409eff;
}

.collapse-subtitle {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}

.optional-info-form {
  margin: 0;
}

.optional-info-form .el-form-item {
  margin-bottom: 20px;
}

/* 代码上传相关样式 */
.code-upload-section {
  background-color: #f8f9fa;
  border: 2px dashed #d1ecf1;
  border-radius: 12px;
  padding: 20px;
  margin: 15px 0;
  transition: all 0.3s ease;
}

.code-upload-section:hover {
  border-color: #3498db;
  background-color: #f0f8ff;
}

.upload-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e9ecef;
}

.upload-icon {
  width: 24px;
  height: 24px;
  margin-right: 10px;
}

.upload-title {
  font-size: 16px;
  font-weight: 500;
  color: #2c3e50;
}

.upload-content {
  position: relative;
}

.code-upload :deep(.el-upload) {
  width: 100%;
}

.code-upload :deep(.el-upload-dragger) {
  width: 100%;
  height: 120px;
  border: none;
  border-radius: 8px;
  background-color: #ffffff;
  transition: all 0.3s ease;
}

.code-upload :deep(.el-upload-dragger:hover) {
  border-color: #3498db;
  background-color: #f0f8ff;
}

.upload-content-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
}

.upload-cloud-icon {
  margin-bottom: 10px;
}

.upload-loading-icon {
  font-size: 48px;
  color: #3498db;
  margin-bottom: 10px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.upload-text {
  text-align: center;
  margin-bottom: 8px;
}

.upload-text p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.upload-text em {
  color: #3498db;
  font-style: normal;
  cursor: pointer;
}

.upload-tip {
  font-size: 12px;
  color: #999;
  text-align: center;
}

.upload-result {
  margin-top: 15px;
  padding: 15px;
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-info {
  display: flex;
  align-items: center;
}

.result-icon {
  font-size: 18px;
  color: #28a745;
  margin-right: 8px;
}

.result-text {
  color: #155724;
  font-size: 14px;
}

.result-actions {
  display: flex;
  gap: 8px;
}
</style>

<script>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, MagicStick, Document, Download, Refresh, CircleCheck, Loading } from '@element-plus/icons-vue'
import { regressionTestService } from '@/services/regressionTestService'
import OCRImageUpload from '@/components/OCRImageUpload.vue'

export default {
  name: 'RegressionTestView',
  components: {
    UploadFilled,
    MagicStick,
    Document,
    Download,
    Refresh,
    CircleCheck,
    OCRImageUpload
  },
  setup() {
    const basicInfoForm = ref(null)
    const impactUpload = ref(null)
    const planningUpload = ref(null)
    const catalogUpload = ref(null)
    
    // 会话ID
    const sessionId = ref(null)
    
    // 基本信息
    const basicInfo = reactive({
        domain: '',
        testManager: '',
        testPersonnel: '',
        developer: '',
        softwareName: '',
        softwareVersion: '',
        softwareId: '',
        detectorFlag: '有检测仪',
        aiAnalysis: true,
        deepAnalysis: true
    })

    // 可选信息
    const optionalInfo = reactive({
        aircraftModel: '',
        projectDirector: '',
        developmentDepartment: '',
        chiefDesigner: ''
    })

    // 折叠面板状态
    const activeCollapse = ref([])
    
    // 上传信息
    const uploadInfo = reactive({
      impactFile: null,
      planningFile: null,
      catalogFile: null,
      hasPlanning: false,
      impactUploaded: false,
      planningUploaded: false,
      catalogUploaded: false
    })
    
    // 文件列表
    const impactFileList = ref([])
    const planningFileList = ref([])
    const catalogFileList = ref([])
    
    // 生成状态
    const isGenerating = ref(false)
    const generationProgress = ref(0)
    const generationStatus = ref('')
    const generationMessage = ref('')
    const generationComplete = ref(false)
    
    // 下载信息
    const downloadFiles = ref([])
    const downloadingFiles = ref([])
    const downloadingAll = ref(false)
    
    // 下拉选项数据
    const testManagers = ref([])
    const testPersonnels = ref([])
    const developers = ref([])
    const domains = ref([])

    // 可选信息下拉数据
    const aircraftModels = ref([])
    const projectDirectors = ref([])
    const developmentDepartments = ref([])
    const chiefDesigners = ref([])

    // 代码分析相关
    const codeFileList = ref([])
    const codeAnalysis = ref({
      isUploading: false,
      hasResult: false,
      result: {},
      taskId: null
    })

    // 验证规则
    const basicInfoRules = {
      testManager: [{ required: true, message: '请选择测试主管', trigger: 'change' }],
      testPersonnel: [{ required: true, message: '请选择测试人员', trigger: 'change' }],
      developer: [{ required: true, message: '请选择开发人员', trigger: 'change' }],
      softwareName: [{ required: true, message: '请输入软件名称', trigger: 'blur' }],
      softwareVersion: [{ required: true, message: '请输入软件版本', trigger: 'blur' }],
      softwareId: [{ required: true, message: '请输入软件标识', trigger: 'blur' }],
      domain: [{ required: true, message: '请选择所属领域', trigger: 'change' }]
    }

    // 计算属性
    const canGenerate = computed(() => {
      const hasBasicInfo = basicInfo.testManager && 
                           basicInfo.testPersonnel && 
                           basicInfo.developer && 
                           basicInfo.softwareName && 
                           basicInfo.softwareVersion && 
                           basicInfo.softwareId &&
                           basicInfo.domain;
      
      const hasImpactFile = uploadInfo.impactUploaded;
      
      // 如果有策划表单，需要上传策划文件
      const hasPlanningFile = uploadInfo.hasPlanning ? uploadInfo.planningUploaded : true;
      
      // 如果没有策划表单，需要上传需求目录文档
      const hasCatalogFile = !uploadInfo.hasPlanning ? uploadInfo.catalogUploaded : true;
      
      return hasBasicInfo && hasImpactFile && hasPlanningFile && hasCatalogFile;
    })

    // 文件上传处理
    const handleImpactUpload = async (file) => {
      console.log('开始上传影响域分析报告:', file.name, '大小:', file.size)
      
      try {
        const response = await regressionTestService.uploadImpactAnalysis(file)
        console.log('影响域分析报告上传响应:', response)
        
        if (response && response.data && response.data.status === 'success') {
          // 创建文件信息对象
          const fileInfo = {
            name: file.name,
            size: file.size,
            type: file.type,
            uid: Date.now(),
            status: 'success'
          }
          
          // 立即更新状态
          sessionId.value = response.data.session_id
          uploadInfo.impactFile = fileInfo
          uploadInfo.impactUploaded = true
          impactFileList.value = [fileInfo]
          
          console.log('影响域分析报告状态更新完成:')
          console.log('- sessionId:', sessionId.value)
          console.log('- impactFile:', uploadInfo.impactFile)
          console.log('- impactUploaded:', uploadInfo.impactUploaded)
          
          ElMessage.success(`影响域分析报告 "${file.name}" 上传成功`)
          
          // 强制触发响应式更新
          await nextTick()
          
        } else {
          console.error('影响域分析报告上传响应格式错误:', response)
          ElMessage.error('影响域分析报告上传响应格式错误')
        }
      } catch (error) {
        console.error('影响域分析报告上传失败:', error)
        ElMessage.error('影响域分析报告上传失败: ' + error.message)
      }
      
      return false
    }
    
    const handlePlanningUpload = async (file) => {
      console.log('开始上传策划文档:', file.name, '大小:', file.size)
      
      try {
        if (!sessionId.value) {
          ElMessage.error('请先上传影响域分析报告')
          return false
        }
        
        const response = await regressionTestService.uploadPlanning(file, sessionId.value)
        console.log('策划文档上传响应:', response)
        
        if (response && response.data && response.data.status === 'success') {
          // 创建文件信息对象
          const fileInfo = {
            name: file.name,
            size: file.size,
            type: file.type,
            uid: Date.now(),
            status: 'success'
          }
          
          // 立即更新状态
          uploadInfo.planningFile = fileInfo
          uploadInfo.planningUploaded = true
          planningFileList.value = [fileInfo]
          
          console.log('策划文档状态更新完成:')
          console.log('- planningFile:', uploadInfo.planningFile)
          console.log('- planningUploaded:', uploadInfo.planningUploaded)
          
          ElMessage.success(`策划文档 "${file.name}" 上传成功`)
          
          // 强制触发响应式更新
          await nextTick()
          
        } else {
          console.error('策划文档上传响应格式错误:', response)
          ElMessage.error('策划文档上传响应格式错误')
        }
      } catch (error) {
        console.error('策划文档上传失败:', error)
        ElMessage.error('策划文档上传失败: ' + error.message)
      }
      
      return false
    }
    
    // 文件删除处理
    const handleImpactRemove = () => {
      uploadInfo.impactFile = null
      uploadInfo.impactUploaded = false
      impactFileList.value = []
      // 重置会话
      sessionId.value = null
      uploadInfo.planningUploaded = false
      planningFileList.value = []
    }
    
    const handlePlanningRemove = () => {
      uploadInfo.planningFile = null
      uploadInfo.planningUploaded = false
      planningFileList.value = []
    }
    
    const handleCatalogUpload = async (file) => {
      console.log('开始上传需求目录文档:', file.name, '大小:', file.size)
      
      try {
        // 验证文件类型
        const validTypes = ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if (!validTypes.includes(file.type)) {
          ElMessage.error('请上传 .docx 格式的文档')
          return false
        }
        
        // 验证文件大小（50MB）
        const maxSize = 50 * 1024 * 1024
        if (file.size > maxSize) {
          ElMessage.error('文件大小不能超过 50MB')
          return false
        }
        
        // 上传文件
        const response = await regressionTestService.uploadCatalog(file, sessionId.value)
        console.log('需求目录文档上传响应:', response)
        
        if (response && response.data && response.data.status === 'success') {
          const fileInfo = {
            name: file.name,
            size: file.size,
            status: 'success'
          }
          
          uploadInfo.catalogFile = fileInfo
          uploadInfo.catalogUploaded = true
          catalogFileList.value = [fileInfo]
          
          console.log('需求目录文档状态更新完成:')
          console.log('- catalogFile:', uploadInfo.catalogFile)
          console.log('- catalogUploaded:', uploadInfo.catalogUploaded)
          
          ElMessage.success(`需求目录文档 "${file.name}" 上传成功`)
          
          // 强制触发响应式更新
          await nextTick()
          
        } else {
          console.error('需求目录文档上传响应格式错误:', response)
          ElMessage.error('需求目录文档上传响应格式错误')
        }
      } catch (error) {
        console.error('需求目录文档上传失败:', error)
        ElMessage.error('需求目录文档上传失败: ' + error.message)
      }
      
      return false
    }
    
    const handleCatalogRemove = () => {
      uploadInfo.catalogFile = null
      uploadInfo.catalogUploaded = false
      catalogFileList.value = []
    }
    
    const handlePlanningChange = (value) => {
      if (!value) {
        uploadInfo.planningFile = null
        uploadInfo.planningUploaded = false
        planningFileList.value = []
      } else {
        // 当选择有策划表时，清空目录文档
        uploadInfo.catalogFile = null
        uploadInfo.catalogUploaded = false
        catalogFileList.value = []
      }
    }

    // 开始生成
    const startGeneration = async () => {
      try {
        console.log('开始生成回归测试表单...')
        console.log('会话ID:', sessionId.value)
        console.log('基本信息:', basicInfo)
        console.log('上传信息:', uploadInfo)
        
        // 验证表单
        const isValid = await basicInfoForm.value.validate()
        if (!isValid) {
          ElMessage.error('请完善基本信息')
          return
        }
        
        if (!sessionId.value) {
          ElMessage.error('请先上传影响域分析报告')
          return
        }
        
        isGenerating.value = true
        generationProgress.value = 0
        generationStatus.value = 'active'
        generationMessage.value = '正在准备生成...'
        generationComplete.value = false
        
        // 调用生成API启动异步任务
        const codeLines = codeAnalysis.value.hasResult ? codeAnalysis.value.result.total_lines : null
        const response = await regressionTestService.generateForms(sessionId.value, {
          ...basicInfo,
          hasPlanning: uploadInfo.hasPlanning
        }, optionalInfo, codeLines)
        
        console.log('任务启动响应:', response.data)
        
        if (response.data.status === 'success') {
          const taskId = response.data.task_id
          console.log('任务ID:', taskId)
          
          // 开始轮询任务状态
          const pollTaskStatus = async () => {
            try {
              const statusResponse = await regressionTestService.getTaskStatus(taskId)
              const taskStatus = statusResponse.data.task_status
              
              console.log('任务状态:', taskStatus)
              
              // 更新进度
              generationProgress.value = taskStatus.progress || 0
              generationMessage.value = taskStatus.message || '处理中...'
              
              if (taskStatus.status === 'completed') {
                // 任务完成
                generationProgress.value = 100
                generationStatus.value = 'success'
                generationMessage.value = '回归测试表单生成成功！'
                generationComplete.value = true
                isGenerating.value = false
                
                // 获取生成的文件列表
                downloadFiles.value = taskStatus.generated_files || []
                
                ElMessage.success('回归测试表单生成成功！')
                
              } else if (taskStatus.status === 'failed') {
                // 任务失败
                isGenerating.value = false
                throw new Error(taskStatus.error || '任务执行失败')
                
              } else if (taskStatus.status === 'running') {
                // 任务仍在运行，继续轮询
                setTimeout(pollTaskStatus, 2000) // 2秒后再次检查
                
              } else {
                // 未知状态，继续轮询
                setTimeout(pollTaskStatus, 2000)
              }
              
            } catch (error) {
              console.error('获取任务状态失败:', error)
              // 继续轮询，避免因网络问题中断
              setTimeout(pollTaskStatus, 3000)
            }
          }
          
          // 开始轮询
          setTimeout(pollTaskStatus, 1000) // 1秒后开始第一次检查
          
        } else {
          throw new Error(response.data.message || '任务启动失败')
        }
        
      } catch (error) {
        console.error('生成失败:', error)
        generationProgress.value = 0
        generationStatus.value = 'exception'
        generationMessage.value = '生成失败: ' + error.message
        isGenerating.value = false
        ElMessage.error('生成失败: ' + error.message)
      }
    }
    
    // 下载文件
    const downloadFile = async (filename) => {
      try {
        if (!sessionId.value) {
          ElMessage.error('会话不存在')
          return
        }
        
        // 添加到下载中列表
        downloadingFiles.value.push(filename)
        
        const response = await regressionTestService.downloadFile(sessionId.value, filename)
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        ElMessage.success(`文件 "${filename}" 下载成功`)
      } catch (error) {
        console.error('下载失败:', error)
        ElMessage.error('下载失败: ' + error.message)
      } finally {
        // 从下载中列表移除
        const index = downloadingFiles.value.indexOf(filename)
        if (index > -1) {
          downloadingFiles.value.splice(index, 1)
        }
      }
    }
    
    // 批量下载
    const downloadAllFiles = async () => {
      try {
        downloadingAll.value = true
        
        for (const fileInfo of downloadFiles.value) {
          // 从文件信息对象中提取文件名
          const filename = fileInfo.name || fileInfo
          await downloadFile(filename)
          // 添加延迟避免并发问题
          await new Promise(resolve => setTimeout(resolve, 500))
        }
        ElMessage.success('所有文件下载完成')
      } catch (error) {
        console.error('批量下载失败:', error)
        ElMessage.error('批量下载失败: ' + error.message)
      } finally {
        downloadingAll.value = false
      }
    }
    
    // 格式化文件大小
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    // 获取文件大小（模拟）
    const getFileSize = (filename) => {
      // 模拟文件大小，实际应该从服务器获取
      return Math.floor(Math.random() * 1000000) + 50000
    }

    // 加载下拉数据
    const loadDropdownData = async () => {
      try {
        // 并行加载所有下拉数据
        const [domainsRes, managersRes, personnelRes, developersRes] = await Promise.all([
          regressionTestService.getDomains(),
          regressionTestService.getTestManagers(),
          regressionTestService.getTestPersonnel(),
          regressionTestService.getDevelopers()
        ])

        domains.value = domainsRes.data.data || []
        testManagers.value = managersRes.data.data || []
        testPersonnels.value = personnelRes.data.data || []
        developers.value = developersRes.data.data || []
      } catch (error) {
        console.error('加载下拉数据失败:', error)
        ElMessage.error('加载下拉数据失败')
      }
    }

    // 加载可选信息下拉数据
    const loadOptionalDropdownData = async () => {
      try {
        const [modelsRes, directorsRes, departmentsRes, designersRes] = await Promise.all([
          regressionTestService.getAircraftModels(),
          regressionTestService.getProjectDirectors(),
          regressionTestService.getDevelopmentDepartments(),
          regressionTestService.getChiefDesigners()
        ])

        aircraftModels.value = modelsRes.data.data || []
        projectDirectors.value = directorsRes.data.data || []
        developmentDepartments.value = departmentsRes.data.data || []
        chiefDesigners.value = designersRes.data.data || []
      } catch (error) {
        console.error('加载可选信息下拉数据失败:', error)
        ElMessage.error('加载可选信息下拉数据失败')
      }
    }

    // 处理领域变化
    const handleDomainChange = async (value) => {
      if (value && !domains.value.find(item => item.value === value)) {
        try {
          await regressionTestService.addDomain(value)
          await loadDropdownData() // 重新加载数据
          ElMessage.success('新领域添加成功')
        } catch (error) {
          console.error('添加领域失败:', error)
          if (error.response?.status === 400) {
            ElMessage.warning('该领域已存在')
          } else {
            ElMessage.error('添加领域失败')
          }
        }
      }
    }

    // 处理测试主管变化
    const handleTestManagerChange = async (value) => {
      if (value && !testManagers.value.find(item => item.value === value)) {
        try {
          await regressionTestService.addTestManager(value)
          await loadDropdownData()
          ElMessage.success('新测试主管添加成功')
        } catch (error) {
          console.error('添加测试主管失败:', error)
          if (error.response?.status === 400) {
            ElMessage.warning('该测试主管已存在')
          } else {
            ElMessage.error('添加测试主管失败')
          }
        }
      }
    }

    // 处理测试人员变化
    const handleTestPersonnelChange = async (value) => {
      if (value && !testPersonnels.value.find(item => item.value === value)) {
        try {
          await regressionTestService.addTestPersonnel(value)
          await loadDropdownData()
          ElMessage.success('新测试人员添加成功')
        } catch (error) {
          console.error('添加测试人员失败:', error)
          if (error.response?.status === 400) {
            ElMessage.warning('该测试人员已存在')
          } else {
            ElMessage.error('添加测试人员失败')
          }
        }
      }
    }

    // 处理开发人员变化
    const handleDeveloperChange = async (value) => {
      if (value && !developers.value.find(item => item.value === value)) {
        try {
          await regressionTestService.addDeveloper(value)
          await loadDropdownData()
          ElMessage.success('新开发人员添加成功')
        } catch (error) {
          console.error('添加开发人员失败:', error)
          if (error.response?.status === 400) {
            ElMessage.warning('该开发人员已存在')
          } else {
            ElMessage.error('添加开发人员失败')
          }
        }
      }
    }

    // 可选信息字段处理函数
    const handleAircraftModelChange = async (value) => {
      if (value && !aircraftModels.value.find(item => item.value === value)) {
        try {
          await regressionTestService.addAircraftModel(value)
          await loadOptionalDropdownData()
          ElMessage.success('新飞机型号添加成功')
        } catch (error) {
          console.error('添加飞机型号失败:', error)
          if (error.response?.status === 400) {
            ElMessage.warning('该飞机型号已存在')
          } else {
            ElMessage.error('添加飞机型号失败')
          }
        }
      }
    }

    const handleProjectDirectorChange = async (value) => {
      if (value && !projectDirectors.value.find(item => item.value === value)) {
        try {
          await regressionTestService.addProjectDirector(value)
          await loadOptionalDropdownData()
          ElMessage.success('新项目总师添加成功')
        } catch (error) {
          console.error('添加项目总师失败:', error)
          if (error.response?.status === 400) {
            ElMessage.warning('该项目总师已存在')
          } else {
            ElMessage.error('添加项目总师失败')
          }
        }
      }
    }

    const handleDevelopmentDepartmentChange = async (value) => {
      if (value && !developmentDepartments.value.find(item => item.value === value)) {
        try {
          await regressionTestService.addDevelopmentDepartment(value)
          await loadOptionalDropdownData()
          ElMessage.success('新研制部门添加成功')
        } catch (error) {
          console.error('添加研制部门失败:', error)
          if (error.response?.status === 400) {
            ElMessage.warning('该研制部门已存在')
          } else {
            ElMessage.error('添加研制部门失败')
          }
        }
      }
    }

    const handleChiefDesignerChange = async (value) => {
      if (value && !chiefDesigners.value.find(item => item.value === value)) {
        try {
          await regressionTestService.addChiefDesigner(value)
          await loadOptionalDropdownData()
          ElMessage.success('新主任设计师添加成功')
        } catch (error) {
          console.error('添加主任设计师失败:', error)
          if (error.response?.status === 400) {
            ElMessage.warning('该主任设计师已存在')
          } else {
            ElMessage.error('添加主任设计师失败')
          }
        }
      }
    }

    // ========================= 代码分析相关方法 =========================
    
    // 处理代码文件上传
    const handleCodeUpload = async (file) => {
      try {
        codeAnalysis.value.isUploading = true
        
        const response = await regressionTestService.uploadCodeForAnalysis(file)
        
        if (response.data.status === 'success') {
          codeAnalysis.value.hasResult = true
          codeAnalysis.value.result = response.data.analysis_result
          codeAnalysis.value.taskId = response.data.task_id
          codeFileList.value = [{
            name: file.name,
            size: file.size,
            status: 'success'
          }]
          
          ElMessage.success(`代码分析完成！共${response.data.analysis_result.total_lines}行代码`)
        } else {
          ElMessage.error(response.data.message || '代码上传失败')
        }
      } catch (error) {
        console.error('代码上传失败:', error)
        ElMessage.error(error.response?.data?.detail || '代码上传失败')
      } finally {
        codeAnalysis.value.isUploading = false
      }
      
      return false // 阻止el-upload的默认上传行为
    }

    // 移除代码文件
    const handleCodeRemove = () => {
      clearCodeAnalysis()
    }

    // 清除代码分析结果
    const clearCodeAnalysis = async () => {
      try {
        if (codeAnalysis.value.taskId) {
          await regressionTestService.deleteCodeAnalysis(codeAnalysis.value.taskId)
        }
      } catch (error) {
        console.warn('删除代码分析任务失败:', error)
      }
      
      codeAnalysis.value = {
        isUploading: false,
        hasResult: false,
        result: {},
        taskId: null
      }
      codeFileList.value = []
      ElMessage.success('已清除代码分析结果')
    }

    // 显示代码分析详情
    const showCodeAnalysisDetails = () => {
      const result = codeAnalysis.value.result
      
      let detailsHtml = `
        <div style="text-align: left;">
          <h4>代码统计详情</h4>
          <p><strong>总行数:</strong> ${result.total_lines || 0} 行</p>
          <p><strong>文件数:</strong> ${result.total_files || 0} 个</p>
          <p><strong>分析方法:</strong> ${result.method === 'simple_count' ? '简单统计' : 'Lizard分析'}</p>
      `
      
      if (result.languages && Object.keys(result.languages).length > 0) {
        detailsHtml += `<h5>语言分布:</h5><ul>`
        for (const [ext, info] of Object.entries(result.languages)) {
          detailsHtml += `<li><strong>${ext}:</strong> ${info.files || 0} 个文件, ${info.lines || 0} 行代码</li>`
        }
        detailsHtml += `</ul>`
      }
      
      if (result.complexity_info && result.complexity_info.total_functions > 0) {
        const complexity = result.complexity_info
        detailsHtml += `
          <h5>复杂度信息:</h5>
          <ul>
            <li><strong>函数总数:</strong> ${complexity.total_functions}</li>
            <li><strong>平均复杂度:</strong> ${complexity.average_complexity?.toFixed(2) || 'N/A'}</li>
            <li><strong>高复杂度函数:</strong> ${complexity.high_complexity_functions} 个</li>
          </ul>
        `
      }
      
      detailsHtml += `</div>`
      
      ElMessageBox.alert(detailsHtml, '代码分析详情', {
        dangerouslyUseHTMLString: true,
        type: 'info'
      })
    }

    // 组件挂载时加载下拉数据
    onMounted(() => {
      loadDropdownData()
      loadOptionalDropdownData()
    })

    // 重置表单
    const resetForm = () => {
      // 重置会话
      sessionId.value = null
      
      // 重置基本信息
      Object.assign(basicInfo, {
        domain: '',
        testManager: '',
        testPersonnel: '',
        developer: '',
        softwareName: '',
        softwareVersion: '',
        softwareId: '',
        detectorFlag: '有检测仪',
        aiAnalysis: true,
        deepAnalysis: true
      })

      // 重置可选信息
      Object.assign(optionalInfo, {
        aircraftModel: '',
        projectDirector: '',
        developmentDepartment: '',
        chiefDesigner: ''
      })

      // 重置折叠状态
      activeCollapse.value = []
      
      // 重置上传信息
      Object.assign(uploadInfo, {
        impactFile: null,
        planningFile: null,
        catalogFile: null,
        hasPlanning: false,
        impactUploaded: false,
        planningUploaded: false,
        catalogUploaded: false
      })
      
      // 清空文件列表
      impactFileList.value = []
      planningFileList.value = []
      catalogFileList.value = []
      
      // 重置生成状态
      isGenerating.value = false
      generationProgress.value = 0
      generationStatus.value = ''
      generationMessage.value = ''
      generationComplete.value = false
      downloadFiles.value = []
      
      // 清空表单验证
      if (basicInfoForm.value) {
        basicInfoForm.value.clearValidate()
      }
      
      ElMessage.success('表单已重置')
    }

    // 处理OCR数据提取
    const handleOCRDataExtracted = (extractedData) => {
      try {
        console.log('收到OCR提取的数据:', extractedData)

        // 填充基本信息
        if (extractedData.basic_info) {
          const basicData = extractedData.basic_info

          if (basicData.domain) basicInfo.domain = basicData.domain
          if (basicData.test_manager) basicInfo.testManager = basicData.test_manager
          if (basicData.test_personnel) basicInfo.testPersonnel = basicData.test_personnel
          if (basicData.developer) basicInfo.developer = basicData.developer
          if (basicData.software_name) basicInfo.softwareName = basicData.software_name
          if (basicData.software_version) basicInfo.softwareVersion = basicData.software_version
          if (basicData.software_id) basicInfo.softwareId = basicData.software_id
        }

        // 填充可选信息
        if (extractedData.optional_info) {
          const optionalData = extractedData.optional_info

          if (optionalData.aircraft_model) optionalInfo.aircraftModel = optionalData.aircraft_model
          if (optionalData.project_director) optionalInfo.projectDirector = optionalData.project_director
          if (optionalData.development_department) optionalInfo.developmentDepartment = optionalData.development_department
          if (optionalData.chief_designer) optionalInfo.chiefDesigner = optionalData.chief_designer
        }

        ElMessage.success('OCR数据已自动填入表单')

      } catch (error) {
        console.error('处理OCR数据失败:', error)
        ElMessage.error('处理OCR数据失败')
      }
    }

    return {
      basicInfoForm,
      impactUpload,
      planningUpload,
      catalogUpload,
      sessionId,
      basicInfo,
      uploadInfo,
      impactFileList,
      planningFileList,
      catalogFileList,
      isGenerating,
      generationProgress,
      generationStatus,
      generationMessage,
      generationComplete,
      downloadFiles,
      downloadingFiles,
      downloadingAll,
      testManagers,
      testPersonnels,
      developers,
      domains,
      basicInfoRules,
      canGenerate,
      handleImpactUpload,
      handlePlanningUpload,
      handleCatalogUpload,
      handleImpactRemove,
      handlePlanningRemove,
      handleCatalogRemove,
      handlePlanningChange,
      startGeneration,
      downloadFile,
      downloadAllFiles,
      resetForm,
      formatFileSize,
      getFileSize,
      loadDropdownData,
      handleDomainChange,
      handleTestManagerChange,
      handleTestPersonnelChange,
      handleDeveloperChange,
      // 可选信息相关
      optionalInfo,
      activeCollapse,
      aircraftModels,
      projectDirectors,
      developmentDepartments,
      chiefDesigners,
      loadOptionalDropdownData,
      handleAircraftModelChange,
      handleProjectDirectorChange,
      handleDevelopmentDepartmentChange,
      handleChiefDesignerChange,
      // OCR相关
      handleOCRDataExtracted,
      regressionTestService,
      // 代码分析相关
      codeFileList,
      codeAnalysis,
      handleCodeUpload,
      handleCodeRemove,
      clearCodeAnalysis,
      showCodeAnalysisDetails
    }
  }
}
</script> 