<template>
  <div class="configuration-test-container">
    <el-card class="main-card">
      <!-- 两列布局 -->
      <el-row :gutter="30" class="main-layout">
        <!-- 左侧：上传+表单区域 (60%) -->
        <el-col :span="15" class="left-section">
          <!-- 第一行：需求文档上传 + 智能表单填写 -->
          <el-row :gutter="20" class="top-row">
            <!-- 需求文档上传 -->
            <el-col :span="12">
              <div class="upload-section no-title">
            <el-upload
              ref="requirementUpload"
              class="upload-demo compact"
              drag
              :before-upload="handleRequirementUpload"
              :file-list="requirementFileList"
              :show-file-list="false"
              :on-remove="handleRequirementRemove"
              :disabled="uploadInfo.requirementUploaded"
              accept=".docx"
              :multiple="false">
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                <span v-if="!uploadInfo.requirementUploaded">拖拽需求文档到此处，或<em>点击上传</em></span>
                <span v-else>需求文档已上传</span>
              </div>
              <div v-if="uploadInfo.requirementUploaded" class="el-upload__success-inline">
                <div class="success-file">{{ uploadInfo.requirementFile?.name }}</div>
                <div class="success-meta">
                  <el-icon class="status-icon"><circle-check /></el-icon>
                  <span>需求文档上传成功</span>
                  <span class="file-size">({{ formatFileSize(uploadInfo.requirementFile?.size || 0) }})</span>
                </div>
              </div>
              <div class="el-upload__tip-inline">
                仅支持 .docx 格式，文件大小不超过 50MB
              </div>
            </el-upload>
              </div>
            </el-col>
            
            <!-- 智能表单填写 -->
            <el-col :span="12">
              <OCRImageUpload :service="configurationItemService" @dataExtracted="handleOCRDataExtracted" />
            </el-col>
          </el-row>
          
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
                <el-form-item label="组件" prop="productType">
                  <el-select 
                    v-model="basicInfo.productType" 
                    placeholder="请选择组件" 
                    style="width: 100%"
                    @change="handleProductTypeChange"
                  >
                    <el-option label="转塔" value="转塔"></el-option>
                    <el-option label="对抗告警" value="对抗告警"></el-option>
                    <el-option label="光电雷达" value="光电雷达"></el-option>
                    <el-option label="吊舱" value="吊舱"></el-option>
                    <el-option label="火控" value="火控"></el-option>
                    <el-option label="外挂" value="外挂"></el-option>
                    <el-option label="显示" value="显示"></el-option>
                  </el-select>
                </el-form-item>
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
            
          </el-form>

          <!-- 可选信息区域 -->
          <el-collapse v-model="activeCollapse" class="optional-info-section">
            <el-collapse-item title="可选信息" name="optional">
              <template #title>
                <div class="collapse-title">
                  <i class="el-icon-setting"></i>
                  <span>可选信息</span>
                  <span class="collapse-subtitle">（飞机型号、项目总师、研制部门、主任设计师、项目主管）</span>
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
                    <el-form-item label="项目主管">
                      <el-select 
                        v-model="optionalInfo.projectManager" 
                        placeholder="请选择项目主管" 
                        style="width: 100%" 
                        filterable
                        allow-create
                        default-first-option
                        @change="handleProjectManagerChange"
                      >
                        <el-option
                          v-for="item in projectManagers"
                          :key="item.value"
                          :label="item.label"
                          :value="item.value">
                        </el-option>
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="代码文件">
                      <div class="code-upload-compact-row">
                        <el-upload
                          ref="codeUpload"
                          class="code-upload-compact"
                          :before-upload="handleCodeUpload"
                          :file-list="codeFileList"
                          :on-remove="handleCodeRemove"
                          :disabled="codeAnalysis.isUploading"
                          accept=".zip,.py,.c,.cpp,.cc,.cxx,.c++,.h,.hpp,.hxx,.h++,.java,.js,.ts,.go,.cs,.php,.rb,.swift,.kt,.rs,.scala,.m,.mm,.f,.f90,.f95"
                          :multiple="false"
                          :show-file-list="false"
                        >
                          <el-tooltip content="支持 .zip 压缩包或单个代码文件" placement="top">
                            <el-button
                              class="code-upload-compact-btn"
                              style="width: 100%"
                              :loading="codeAnalysis.isUploading"
                              type="primary"
                              plain
                            >
                              {{ codeAnalysis.isUploading ? '正在分析...' : (codeAnalysis.hasResult ? '已分析，重新上传' : '上传代码文件') }}
                            </el-button>
                          </el-tooltip>
                        </el-upload>

                        <el-button
                          v-if="codeAnalysis.hasResult"
                          class="code-upload-compact-action"
                          type="success"
                          plain
                          @click="showCodeAnalysisDetails"
                        >
                          详情
                        </el-button>
                      </div>
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </el-collapse-item>
          </el-collapse>
          
        </el-col>
        
        <!-- 右侧：测试需求来源信息 (40%) -->
        <el-col :span="9" class="right-section">
          <div class="requirement-catalog-section">
            <h3>测试策划信息</h3>
            <div class="catalog-info">
              系统将自动从需求文档规格说明中提取测试需求条目信息
            </div>

            <!-- 需求目录提取区域 -->
            <div class="catalog-extraction-section">
              <!-- 等待上传状态 -->
              <div v-if="!uploadInfo.requirementUploaded" class="catalog-waiting">
                <div class="waiting-content">
                  <el-icon class="waiting-icon"><document /></el-icon>
                  <span class="waiting-text">请先上传需求规格说明文档</span>
                </div>
              </div>

              <!-- 需求提取界面 -->
              <div v-else class="catalog-content">
                <!-- 提取按钮（等待状态） -->
                <div class="catalog-extract-actions" v-if="catalogExtraction.status === 'waiting'">
                  <el-button type="primary" @click="extractCatalog" :loading="catalogExtraction.extracting">
                    <el-icon><search /></el-icon>
                    {{ catalogExtraction.extracting ? '正在提取需求目录...' : '提取测试需求目录' }}
                  </el-button>
                </div>

                <!-- 🔧 新增：正在分析状态显示 -->
                <div v-else-if="catalogExtraction.status === 'extracting'" class="catalog-extracting">
                  <div class="extracting-content">
                    <el-icon class="extracting-icon rotating"><loading /></el-icon>
                    <span class="extracting-text">正在分析章节名称，请稍候...</span>
                  </div>
                  <div class="extracting-progress">
                    <el-progress :percentage="50" :show-text="false" />
                    <span class="progress-text">正在使用PyWin32增强算法提取3.2章节标题</span>
                  </div>
                </div>

                <!-- 已提取状态显示 -->
                <div v-else-if="catalogExtraction.status === 'extracted'" class="catalog-extracted">
                  <div class="catalog-header">
                    <el-icon class="status-icon success"><circle-check-filled /></el-icon>
                    <span class="status-text">
                      已提取 {{ catalogExtraction.totalItems }} 个测试需求项
                      <span v-if="catalogExtraction.duration > 0" class="duration-info">
                        (耗时: {{ (catalogExtraction.duration / 1000).toFixed(2) }}秒)
                      </span>
                    </span>
                    <div class="catalog-actions">
                      <el-button size="small" type="success" @click="quickConfirmCatalog">
                        确认需求
                      </el-button>
                      <el-button size="small" type="primary" @click="enableCatalogEdit">
                        编辑需求
                      </el-button>
                      <el-button size="small" type="default" @click="reExtractCatalog">
                        重新提取
                      </el-button>
                    </div>
                  </div>
                  
                  <!-- 级别选择器和说明 -->
                  <div class="level-selector">
                    <span class="level-label">显示级别：</span>
                    <el-select 
                      v-model="catalogLevelFilter" 
                      size="small" 
                      style="width: 100px;"
                      @change="updateCatalogDisplay">
                      <el-option label="3级" value="3" />
                      <el-option label="4级" value="4" />
                      <el-option label="5级" value="5" />
                      <el-option label="6级" value="6" />
                      <el-option label="全部" value="all" />
                    </el-select>
                    <span class="level-description">
                      ({{ getFilterDescription() }})
                    </span>
                  </div>
                  
                  <!-- 颜色说明 -->
                  <div class="color-legend">
                    <span class="legend-item">
                      <span class="legend-color" style="color: #000; font-weight: bold;">■</span>
                      <span>黑色：将用于测试生成</span>
                    </span>
                    <span class="legend-item">
                      <span class="legend-color" style="color: #999;">■</span>
                      <span>灰色：已过滤（有子章节）</span>
                    </span>
                  </div>
                  
                  <!-- 需求列表预览（彩色渲染） -->
                  <div class="catalog-preview-colored">
                    <div 
                      v-for="(item, index) in catalogItemsWithFilterStatus" 
                      :key="index"
                      :class="['catalog-item', { 'filtered-out': item.isFiltered }]"
                      :style="{ paddingLeft: (item.indent * 20) + 'px' }">
                      {{ item.displayText }}
                    </div>
                  </div>
                </div>

                <!-- 已确认状态显示 -->
                <div v-else-if="catalogExtraction.status === 'confirmed'" class="catalog-confirmed">
                  <div class="catalog-header">
                    <el-icon class="status-icon success"><circle-check-filled /></el-icon>
                    <span class="status-text">测试需求已确认 ({{ catalogExtraction.totalItems }} 个需求项)</span>
                    <div class="catalog-actions">
                      <el-button size="small" type="primary" @click="enableCatalogEdit">
                        重新编辑
                      </el-button>
                      <el-button size="small" type="default" @click="reExtractCatalog">
                        重新提取
                      </el-button>
                    </div>
                  </div>
                  
                  <!-- 级别选择器和说明 -->
                  <div class="level-selector">
                    <span class="level-label">显示级别：</span>
                    <el-select 
                      v-model="catalogLevelFilter" 
                      size="small" 
                      style="width: 100px;"
                      @change="updateCatalogDisplay">
                      <el-option label="3级" value="3" />
                      <el-option label="4级" value="4" />
                      <el-option label="5级" value="5" />
                      <el-option label="6级" value="6" />
                      <el-option label="全部" value="all" />
                    </el-select>
                    <span class="level-description">
                      ({{ getFilterDescription() }})
                    </span>
                  </div>
                  
                  <!-- 颜色说明 -->
                  <div class="color-legend">
                    <span class="legend-item">
                      <span class="legend-color" style="color: #000; font-weight: bold;">■</span>
                      <span>黑色：将用于测试生成</span>
                    </span>
                    <span class="legend-item">
                      <span class="legend-color" style="color: #999;">■</span>
                      <span>灰色：已过滤（有子章节）</span>
                    </span>
                  </div>
                  
                  <!-- 需求列表确认显示（彩色渲染） -->
                  <div class="catalog-confirmed-colored">
                    <div 
                      v-for="(item, index) in catalogItemsWithFilterStatus" 
                      :key="index"
                      :class="['catalog-item', { 'filtered-out': item.isFiltered }]"
                      :style="{ paddingLeft: (item.indent * 20) + 'px' }">
                      {{ item.displayText }}
                    </div>
                  </div>
                </div>

                <!-- 编辑状态 -->
                <div v-else-if="catalogExtraction.status === 'editing'" class="catalog-editing">
                  <div class="catalog-header">
                    <el-icon class="status-icon warning"><edit /></el-icon>
                    <span class="status-text">编辑测试需求内容</span>
                    <div class="catalog-actions">
                      <el-button size="small" type="success" @click="confirmCatalogEdit">
                        保存确认
                      </el-button>
                      <el-button size="small" type="default" @click="cancelCatalogEdit">
                        取消
                      </el-button>
                    </div>
                  </div>
                  
                  <!-- 级别选择器和说明 -->
                  <div class="level-selector">
                    <span class="level-label">显示级别：</span>
                    <el-select 
                      v-model="catalogLevelFilter" 
                      size="small" 
                      style="width: 100px;"
                      @change="updateCatalogDisplay">
                      <el-option label="3级" value="3" />
                      <el-option label="4级" value="4" />
                      <el-option label="5级" value="5" />
                      <el-option label="6级" value="6" />
                      <el-option label="全部" value="all" />
                    </el-select>
                    <span class="level-description">
                      ({{ getFilterDescription() }})
                    </span>
                  </div>
                  
                  <!-- 颜色说明 -->
                  <div class="color-legend">
                    <span class="legend-item">
                      <span class="legend-color" style="color: #000; font-weight: bold;">■</span>
                      <span>黑色：将用于测试生成</span>
                    </span>
                    <span class="legend-item">
                      <span class="legend-color" style="color: #999;">■</span>
                      <span>灰色：已过滤（有子章节）</span>
                    </span>
                    <span class="legend-item edit-tip">
                      <el-icon style="color: #e6a23c;"><edit /></el-icon>
                      <span style="color: #e6a23c;">可编辑模式：点击任意行进行修改</span>
                    </span>
                  </div>
                  
                  <!-- 可编辑的需求列表（彩色渲染，contenteditable） -->
                  <div class="catalog-edit-colored">
                    <div 
                      v-for="(item, index) in editableCatalogItems" 
                      :key="index"
                      :class="['catalog-item-editable', { 'filtered-out': item.isFiltered }]"
                      :style="{ paddingLeft: (item.indent * 20) + 'px' }"
                      contenteditable="true"
                      @blur="updateCatalogItemText(index, $event)"
                      @keydown.enter.prevent="handleEnterKey(index, $event)"
                      :data-index="index">
                      {{ item.displayText }}
                    </div>
                  </div>
                  
                  <!-- 验证结果显示 -->
                  <div v-if="catalogDialog.validation" class="validation-result">
                    <div v-if="catalogDialog.validation.errors.length > 0" class="validation-errors">
                      <h4>错误:</h4>
                      <ul>
                        <li v-for="error in catalogDialog.validation.errors" :key="error" class="error-item">
                          {{ error }}
                        </li>
                      </ul>
                    </div>
                    <div v-if="catalogDialog.validation.warnings.length > 0" class="validation-warnings">
                      <h4>警告:</h4>
                      <ul>
                        <li v-for="warning in catalogDialog.validation.warnings" :key="warning" class="warning-item">
                          {{ warning }}
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                <!-- 提取失败状态 -->
                <div v-else-if="catalogExtraction.status === 'failed'" class="catalog-error">
                  <div class="error-content">
                    <el-icon class="status-icon error"><circle-close /></el-icon>
                    <span class="error-text">测试需求提取失败: {{ catalogExtraction.error }}</span>
                    <el-button size="small" type="primary" @click="reExtractCatalog">
                      重试
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
      
      <!-- 生成操作区 - 分步生成 -->
      <el-divider></el-divider>
      <div class="generation-section">
        <div class="generation-header">
          <div class="generation-header-left">
            <h3 class="generation-title">
              <el-icon><magic-stick /></el-icon>
              表单生成流程
            </h3>
            <p class="generation-description">请按照以下步骤依次生成测试表单，每个步骤依赖于前一步骤的完成。</p>
          </div>

          <div class="generation-header-right">
            <div class="generation-meta-item">
              <span class="generation-meta-label">检测仪标识</span>
              <el-switch v-model="hasDetector" active-text="有检测仪" inactive-text="无检测仪"></el-switch>
            </div>

            <div class="generation-meta-item">
              <span class="generation-meta-label">AI分析</span>
              <el-switch v-model="basicInfo.aiAnalysis" active-text="开启" inactive-text="关闭"></el-switch>
            </div>

            <div class="generation-meta-item">
              <span class="generation-meta-label">深度分析</span>
              <el-switch v-model="basicInfo.deepAnalysis" active-text="开启" inactive-text="关闭"></el-switch>
            </div>
          </div>
        </div>
        
        <!-- 步骤卡片 -->
        <div class="step-cards">
          <!-- 步骤1: 项目信息表 -->
          <el-card class="step-card" :class="{'step-completed': step1State.completed, 'step-running': step1State.running}" :body-style="{ padding: '12px' }">
            <div class="step-header">
              <div class="step-number">
                <el-icon v-if="step1State.completed" class="step-icon success"><circle-check-filled /></el-icon>
                <el-icon v-else-if="step1State.running" class="step-icon running"><loading /></el-icon>
                <span v-else class="step-num">1</span>
              </div>
              <div class="step-title-area">
                <h4>生成项目信息表</h4>
                <p class="step-subtitle">项目基本信息 + 软件配置项信息</p>
              </div>
            </div>
            
            <div class="step-body">
              <div v-if="step1State.completed" class="step-result">
                <p class="result-text">✓ 已完成 ({{ step1State.files.length }} 个文件)</p>
                <ul class="file-list">
                  <li v-for="file in step1State.files" :key="file">
                    <span>{{ file }}</span>
          <el-button 
                      size="default" 
            type="primary" 
                      @click="downloadFile(file)">
                      <el-icon><download /></el-icon>
                      下载
          </el-button>
                  </li>
                </ul>
                <p class="completion-time">{{ step1State.completedAt }}</p>
              </div>
              
              <div v-else-if="step1State.running" class="step-progress">
                <el-progress :percentage="step1State.progress" :status="''" />
                <p class="progress-msg">{{ step1State.message }}</p>
              </div>
              
              <div v-else class="step-action">
                <!-- ✨ 新增：前置条件列表 -->
                <div class="precondition-list">
                  <div class="precondition-item" :class="{'completed': step1Preconditions.requirementUploaded}">
                    <el-icon v-if="step1Preconditions.requirementUploaded" class="check-icon"><circle-check-filled /></el-icon>
                    <el-icon v-else class="pending-icon"><circle /></el-icon>
                    <span class="precondition-text">需要：需求文档已上传</span>
                  </div>
                  <div class="precondition-item" :class="{'completed': step1Preconditions.basicInfoComplete}">
                    <el-icon v-if="step1Preconditions.basicInfoComplete" class="check-icon"><circle-check-filled /></el-icon>
                    <el-icon v-else class="pending-icon"><circle /></el-icon>
                    <span class="precondition-text">需要：基本信息填写完整</span>
                  </div>
                </div>
                
                <!-- 开始生成按钮 -->
          <el-button 
                  size="small"
                  type="primary" 
                  @click="generateStep1"
                  :disabled="!canStartStep1">
                  <el-icon><caret-right /></el-icon>
                  开始生成
                </el-button>
              </div>
            </div>
          </el-card>

          <!-- 步骤2: 策划表与问题单 -->
          <el-card class="step-card" :class="{'step-completed': step2State.completed, 'step-running': step2State.running}" :body-style="{ padding: '12px' }">
            <div class="step-header">
              <div class="step-number">
                <el-icon v-if="step2State.completed" class="step-icon success"><circle-check-filled /></el-icon>
                <el-icon v-else-if="step2State.running" class="step-icon running"><loading /></el-icon>
                <span v-else class="step-num">2</span>
              </div>
              <div class="step-title-area">
                <h4>生成策划表与问题单</h4>
                <p class="step-subtitle">项目策划表 + 问题报告单</p>
              </div>
            </div>
            
            <div class="step-body">
              <!-- 已完成状态 -->
              <div v-if="step2State.completed" class="step-result">
                <p class="result-text">✓ 已完成 ({{ step2State.files.length }} 个文件)</p>
                <ul class="file-list">
                  <li v-for="file in step2State.files" :key="file">
                    <span>{{ file }}</span>
                    <el-button 
                      size="default" 
                      type="primary" 
                      @click="downloadFile(file)">
                      <el-icon><download /></el-icon>
                      下载
                    </el-button>
                  </li>
                </ul>
                <p class="completion-time">{{ step2State.completedAt }}</p>
              </div>
              
              <!-- 生成中状态 -->
              <div v-else-if="step2State.running" class="step-progress">
                <el-progress :percentage="step2State.progress" :status="''" />
                <p class="progress-msg">{{ step2State.message }}</p>
              </div>
              
              <!-- 已上传但未生成状态 -->
              <div v-else-if="step2State.uploaded" class="step-action">
                <p class="upload-success">
                  <el-icon><circle-check /></el-icon>
                  已上传: {{ step2State.uploadedFile }}
                </p>
                
                <!-- 前置条件列表 -->
                <div class="precondition-list" v-if="!canStartStep2">
                  <div class="precondition-item" :class="{'completed': step1State.completed}">
                    <el-icon v-if="step1State.completed" class="check-icon"><circle-check-filled /></el-icon>
                    <el-icon v-else class="pending-icon"><circle /></el-icon>
                    <span class="precondition-text">需要：步骤1已完成</span>
                  </div>
                  <div class="precondition-item" :class="{'completed': catalogExtraction.status === 'confirmed'}">
                    <el-icon v-if="catalogExtraction.status === 'confirmed'" class="check-icon"><circle-check-filled /></el-icon>
                    <el-icon v-else class="pending-icon"><circle /></el-icon>
                    <span class="precondition-text">需要：需求已确认</span>
                  </div>
                </div>
                
                <el-button 
                  size="small"
                  type="primary" 
                  :disabled="!canStartStep2"
                  @click="generateStep2">
                  <el-icon><caret-right /></el-icon>
                  开始生成
                </el-button>
              </div>
              
              <!-- 等待上传状态 -->
              <div v-else-if="step1State.completed" class="step-upload">
                <!-- 前置条件列表 -->
                <div class="precondition-list">
                  <div class="precondition-item" :class="{'completed': step1State.completed}">
                    <el-icon v-if="step1State.completed" class="check-icon"><circle-check-filled /></el-icon>
                    <el-icon v-else class="pending-icon"><circle /></el-icon>
                    <span class="precondition-text">步骤1已完成</span>
                  </div>
                  <div class="precondition-item" :class="{'completed': catalogExtraction.status === 'confirmed'}">
                    <el-icon v-if="catalogExtraction.status === 'confirmed'" class="check-icon"><circle-check-filled /></el-icon>
                    <el-icon v-else class="pending-icon"><circle /></el-icon>
                    <span class="precondition-text">需求已确认</span>
                  </div>
                </div>
                
                <p class="upload-tip">
                  <el-icon><warning-filled /></el-icon>
                  请上传步骤1生成的项目信息表（可在下载后修改）
                </p>
                <el-upload
                  :action="''"
                  :auto-upload="false"
                  :on-change="handleStep2FileChange"
                  :show-file-list="false"
                  accept=".xlsx">
                  <el-button type="primary">
                    <el-icon><upload-filled /></el-icon>
                    上传项目信息表
                  </el-button>
                </el-upload>
              </div>
              
              <!-- 未完成步骤1状态 -->
              <div v-else class="step-action">
                <!-- 前置条件列表 -->
                <div class="precondition-list">
                  <div class="precondition-item" :class="{'completed': step1State.completed}">
                    <el-icon v-if="step1State.completed" class="check-icon"><circle-check-filled /></el-icon>
                    <el-icon v-else class="pending-icon"><circle /></el-icon>
                    <span class="precondition-text">需要：步骤1已完成</span>
                  </div>
                  <div class="precondition-item" :class="{'completed': catalogExtraction.status === 'confirmed'}">
                    <el-icon v-if="catalogExtraction.status === 'confirmed'" class="check-icon"><circle-check-filled /></el-icon>
                    <el-icon v-else class="pending-icon"><circle /></el-icon>
                    <span class="precondition-text">需要：需求已确认</span>
                  </div>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 步骤3: 需求分析表（包含3a和3b两个子阶段） -->
          <el-card class="step-card" :class="{'step-completed': step3State.completed, 'step-running': step3State.running}" :body-style="{ padding: '12px' }">
            <div class="step-header">
              <div class="step-number">
                <el-icon v-if="step3State.completed" class="step-icon success"><circle-check-filled /></el-icon>
                <el-icon v-else-if="step3State.running" class="step-icon running"><loading /></el-icon>
                <span v-else class="step-num">3</span>
              </div>
              <div class="step-title-area">
                <h4>生成需求分析表</h4>
                <p class="step-subtitle">分两阶段：基础信息 + 测试项</p>
              </div>
            </div>
            
            <div class="step-body">
              <!-- 两个子阶段 -->
              <div class="sub-steps">
                <!-- 步骤3a: 生成基础信息 -->
                <div class="sub-step" :class="{'sub-step-completed': step3State.step3a.completed, 'sub-step-running': step3State.step3a.running}">
                  <div class="sub-step-title">
                    <el-icon v-if="step3State.step3a.completed"><circle-check-filled /></el-icon>
                    <el-icon v-else-if="step3State.step3a.running"><loading /></el-icon>
                    <span v-else>○</span>
                    <span class="sub-step-text">3a. 生成基础信息</span>
                  </div>
                  
                  <!-- 3a 已完成 -->
                  <div v-if="step3State.step3a.completed" class="sub-step-content">
                    <ul class="file-list">
                      <li v-for="file in step3State.step3a.files" :key="file">
                        <span>{{ file }}</span>
                        <el-button size="small" type="primary" @click="downloadFile(file)">
                          <el-icon><download /></el-icon> 下载
                        </el-button>
                      </li>
                    </ul>
                  </div>
                  
                  <!-- 3a 生成中 -->
                  <div v-else-if="step3State.step3a.running" class="sub-step-content">
                    <el-progress :percentage="step3State.step3a.progress" :status="''" :stroke-width="6" />
                    <p class="sub-progress-msg">{{ step3State.step3a.message }}</p>
                  </div>
                  
                  <!-- 3a 已上传待生成 -->
                  <div v-else-if="step3State.step3a.uploaded" class="sub-step-content">
                    <p class="upload-success-small">✓ 已上传: {{ step3State.step3a.uploadedFile }}</p>
                    <el-button size="small" type="primary" @click="generateStep3a">
                      <el-icon><caret-right /></el-icon> 开始生成
                    </el-button>
                  </div>
                  
                  <!-- 3a 等待上传 -->
                  <div v-else-if="step2State.completed" class="sub-step-content">
                    <p class="upload-tip-small">请上传步骤2生成的表单</p>
                    <el-upload
                      :action="''"
                      :auto-upload="false"
                      :on-change="handleStep3FileChange"
                      :show-file-list="false"
                      accept=".xlsx">
                      <el-button size="small">
                        <el-icon><upload-filled /></el-icon> 上传
                      </el-button>
                    </el-upload>
                  </div>
                  
                  <!-- 3a 未完成前置步骤 -->
                  <div v-else class="sub-step-content">
                    <p class="step-tip-small">
                      <el-icon><warning-filled /></el-icon>
                      需要: 完成步骤2
                    </p>
                  </div>
                </div>
                
                <!-- 步骤3b: 完善测试项 -->
                <div class="sub-step" :class="{'sub-step-completed': step3State.step3b.completed, 'sub-step-running': step3State.step3b.running}">
                  <div class="sub-step-title">
                    <el-icon v-if="step3State.step3b.completed"><circle-check-filled /></el-icon>
                    <el-icon v-else-if="step3State.step3b.running"><loading /></el-icon>
                    <span v-else>○</span>
                    <span class="sub-step-text">3b. 完善测试项</span>
                  </div>
                  
                  <!-- 3b 已完成 -->
                  <div v-if="step3State.step3b.completed" class="sub-step-content">
                    <ul class="file-list">
                      <li v-for="file in step3State.step3b.files" :key="file">
                        <span>{{ file }}</span>
                        <el-button size="small" type="primary" @click="downloadFile(file)">
                          <el-icon><download /></el-icon> 下载
                        </el-button>
                      </li>
                    </ul>
                  </div>
                  
                  <!-- 3b 生成中 -->
                  <div v-else-if="step3State.step3b.running" class="sub-step-content">
                    <el-progress :percentage="step3State.step3b.progress" :status="''" :stroke-width="6" />
                    <p class="sub-progress-msg">{{ step3State.step3b.message }}</p>
                  </div>
                  
                  <!-- 3b 已上传待生成 -->
                  <div v-else-if="step3State.step3b.uploaded" class="sub-step-content">
                    <p class="upload-success-small">✓ 已上传: {{ step3State.step3b.uploadedFile }}</p>
                    <el-button size="small" type="primary" @click="generateStep3b">
                      <el-icon><caret-right /></el-icon> 开始生成
                    </el-button>
                  </div>
                  
                  <!-- 3b 等待上传 -->
                  <div v-else-if="step3State.step3a.completed" class="sub-step-content">
                    <p class="upload-tip-small">请上传步骤3a生成的基础版表单</p>
                    <el-upload
                      :action="''"
                      :auto-upload="false"
                      :on-change="handleStep3aFileChange"
                      :show-file-list="false"
                      accept=".xlsx">
                      <el-button size="small">
                        <el-icon><upload-filled /></el-icon> 上传
                      </el-button>
                    </el-upload>
                  </div>
                  
                  <!-- 3b 未完成前置步骤 -->
                  <div v-else class="sub-step-content">
                    <p class="step-tip-small">
                      <el-icon><warning-filled /></el-icon>
                      需要: 完成步骤3a
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 步骤4: 测试用例单 -->
          <el-card class="step-card" :class="{'step-completed': step4State.completed, 'step-running': step4State.running}" :body-style="{ padding: '12px' }">
            <div class="step-header">
              <div class="step-number">
                <el-icon v-if="step4State.completed" class="step-icon success"><circle-check-filled /></el-icon>
                <el-icon v-else-if="step4State.running" class="step-icon running"><loading /></el-icon>
                <span v-else class="step-num">4</span>
              </div>
              <div class="step-title-area">
                <h4>生成测试用例单</h4>
                <p class="step-subtitle">基于需求分析表生成</p>
              </div>
            </div>
            
            <div class="step-body">
              <!-- 已完成状态 -->
              <div v-if="step4State.completed" class="step-result">
                <p class="result-text">✓ 已完成 ({{ step4State.files.length }} 个文件)</p>
                <ul class="file-list">
                  <li v-for="file in step4State.files" :key="file">
                    <span>{{ file }}</span>
                    <el-button 
                      size="default" 
                      type="primary" 
                      @click="downloadFile(file)">
                      <el-icon><download /></el-icon>
                      下载
                    </el-button>
                  </li>
                </ul>
                <p class="completion-time">{{ step4State.completedAt }}</p>
              </div>
              
              <!-- 生成中状态 -->
              <div v-else-if="step4State.running" class="step-progress">
                <el-progress :percentage="step4State.progress" :status="''" />
                <p class="progress-msg">{{ step4State.message }}</p>
              </div>
              
              <!-- 已上传但未生成状态 -->
              <div v-else-if="step4State.uploaded" class="step-action">
                <p class="upload-success">
                  <el-icon><circle-check /></el-icon>
                  已上传: {{ step4State.uploadedFile }}
                </p>
                <el-button 
                  size="small"
                  type="primary" 
                  @click="generateStep4">
                  <el-icon><caret-right /></el-icon>
                  开始生成
                </el-button>
              </div>
              
              <!-- 等待上传状态 -->
              <div v-else-if="step3State.completed" class="step-upload">
                <p class="upload-tip">
                  <el-icon><warning-filled /></el-icon>
                  请上传步骤3生成的表单（可在下载后修改）
                </p>
                <el-upload
                  :action="''"
                  :auto-upload="false"
                  :on-change="handleStep4FileChange"
                  :show-file-list="false"
                  accept=".xlsx">
                  <el-button type="primary">
                    <el-icon><upload-filled /></el-icon>
                    上传表单
                  </el-button>
                </el-upload>
              </div>
              
              <!-- 未完成步骤3状态 -->
              <div v-else class="step-action">
                <p class="step-tip">
                  <el-icon><warning-filled /></el-icon>
                  需要: 完成步骤3
                </p>
              </div>
            </div>
          </el-card>
        </div>

        <!-- 全部下载按钮 -->
        <div v-if="allStepsCompleted" class="download-all-section">
          <el-button 
            type="success" 
            size="large"
            @click="downloadAllFiles"
            :loading="downloadingAll">
            <el-icon><download /></el-icon>
            下载所有生成的表单
          </el-button>
        </div>
      </div>
    </el-card>


  </div>
</template>

<style scoped>
.configuration-test-container {
  padding: 20px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  width: 100%;
}

.main-card {
  background: #fff;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 8px 32px rgba(32, 101, 209, 0.08);
  width: 100%;
  max-width: 95%;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h2 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.description {
  color: #7f8c8d;
  font-size: 14px;
}



.basic-info-form {
  margin-bottom: 15px;
}

.basic-info-form h3 {
  color: #2c3e50;
  margin-top: 0;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid #3498db;
  font-size: 16px;
}

/* 检测仪标识：单选横向排列（避免换行到下一行） */
.detector-flag-radio {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: nowrap;
}

.upload-section {
  margin-bottom: 0;
}

.upload-section.no-title h3 {
  display: none;
}

.upload-section h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid #3498db;
  font-size: 16px;
}

/* 第一行上传区域和智能表单高度对齐 */
.top-row {
  margin-bottom: 8px;
}

.top-row .upload-section .upload-demo {
  height: 100%;
  min-height: 0;
}

.top-row .upload-section .el-upload-dragger {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.upload-demo {
  margin-bottom: 0;
}

.upload-demo.compact {
  margin-bottom: 0;
}

.upload-demo.compact :deep(.el-upload-dragger) {
  width: 100%;
  height: 112px;
  padding: 12px;
}

/* 可选信息 - 代码上传紧凑布局（与下拉框同高） */
.code-upload-compact-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.code-upload-compact {
  flex: 1;
}

.code-upload-compact :deep(.el-upload) {
  width: 100%;
  display: block;
}

.code-upload-compact-btn,
.code-upload-compact-action {
  height: 32px;
  padding: 0 12px;
}

.upload-demo.compact :deep(.el-icon--upload) {
  font-size: 40px;
  margin-bottom: 8px;
}

.upload-demo.compact :deep(.el-upload__text) {
  font-size: 13px;
  line-height: 1.4;
  margin-bottom: 6px;
}

.upload-demo.compact :deep(.el-upload__tip) {
  font-size: 11px;
  margin-top: 5px;
}

.upload-demo.compact :deep(.el-upload__tip-inline) {
  font-size: 11px;
  color: #909399;
  margin-top: 6px;
  line-height: 1.3;
}

.upload-demo.compact :deep(.el-upload__success-inline) {
  margin-top: 8px;
  width: 100%;
  color: #67c23a;
}

.upload-demo.compact :deep(.el-upload__success-inline .success-file) {
  font-size: 12px;
  color: #303133;
  margin-bottom: 4px;
  word-break: break-all;
}

.upload-demo.compact :deep(.el-upload__success-inline .success-meta) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: #67c23a;
}

.upload-demo.compact :deep(.el-upload__success-inline .file-size) {
  color: #909399;
}

/* upload-status 已迁移到组件内部展示（el-upload__success-inline），保留通用类仅供内部使用 */
.status-icon {
  font-size: 14px;
}

.file-size {
  color: #909399;
  font-size: 11px;
}

.generation-section {
  margin-top: 20px;
}

.generation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.generation-header-left {
  min-width: 0;
}

.generation-header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 18px;
  flex-wrap: wrap;
  margin-right: 100px;
}

.generation-meta-item {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
}

.generation-meta-label {
  color: #606266;
  font-size: 14px;
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
  .configuration-test-container {
    padding: 8px;
  }

  .main-card {
    max-width: 100%;
    padding: 15px;
  }

  .main-layout {
    flex-direction: column;
  }

  .left-section {
    padding-right: 0;
    border-right: none;
    border-bottom: 1px solid #e6e6e6;
    padding-bottom: 20px;
    margin-bottom: 20px;
  }

  .right-section {
    padding-left: 0;
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

    /* 测试需求提取相关样式 */
.catalog-extraction-section {
  background-color: #f8f9fa;
  border: 2px dashed #d1ecf1;
  border-radius: 12px;
  padding: 20px;
  /* 右侧内容撑满高度，便于与左侧（可选信息底部）对齐 */
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

.section-header h4 {
  color: #2c3e50;
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 500;
}

.section-description {
  color: #606266;
  font-size: 14px;
  margin: 0 0 20px 0;
}

.catalog-preview {
  background-color: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 15px;
}

.catalog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.catalog-actions {
  display: flex;
  gap: 8px;
}

.catalog-preview-content {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 10px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  color: #495057;
  max-height: 150px;
  overflow-y: auto;
}

.catalog-preview-colored,
.catalog-confirmed-colored {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 10px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.8;
  max-height: 400px;
  overflow-y: auto;
}

.catalog-item {
  color: #000;
  font-weight: 500;
  padding: 2px 0;
  transition: background-color 0.2s;
}

.catalog-item:hover {
  background-color: #e9ecef;
}

.catalog-item.filtered-out {
  color: #999;
  font-weight: normal;
}

.color-legend {
  display: flex;
  gap: 20px;
  margin: 10px 0;
  padding: 8px 12px;
  background-color: #f0f7ff;
  border: 1px solid #d0e4ff;
  border-radius: 4px;
  font-size: 13px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  font-size: 16px;
}

.edit-tip {
  margin-left: auto;
  color: #e6a23c;
  font-weight: 500;
}

.catalog-edit-colored {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 10px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.8;
  max-height: 400px;
  overflow-y: auto;
}

.catalog-item-editable {
  color: #000;
  font-weight: 500;
  padding: 4px 6px;
  margin: 2px 0;
  border-radius: 3px;
  transition: all 0.2s;
  cursor: text;
  min-height: 24px;
  outline: none;
}

.catalog-item-editable:hover {
  background-color: #e9ecef;
}

.catalog-item-editable:focus {
  background-color: #fff3cd;
  border: 1px solid #ffc107;
  box-shadow: 0 0 0 2px rgba(255, 193, 7, 0.2);
}

.catalog-item-editable.filtered-out {
  color: #999;
  font-weight: normal;
}

/* 级别选择器样式 */
.level-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 0;
  padding: 8px 12px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  font-size: 13px;
}

.level-label {
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}

.level-description {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}

.catalog-confirmed {
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 8px;
  padding: 15px;
}

.status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.catalog-error {
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  padding: 15px;
}

.error-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.error-text {
  flex: 1;
  color: #721c24;
  font-size: 14px;
}

.catalog-waiting {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 0;
  padding: 16px;
}

.waiting-content {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #909399;
  border-radius: 12px;
  border: 1px solid rgba(64, 158, 255, 0.18);
  background: linear-gradient(180deg, #ffffff 0%, #f6f9ff 100%);
  box-shadow:
    0 10px 28px rgba(31, 45, 61, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.waiting-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.waiting-text {
  font-size: 16px;
}

.status-icon.success {
  color: #28a745;
  font-size: 18px;
  margin-right: 8px;
}

.status-icon.error {
  color: #dc3545;
  font-size: 18px;
  margin-right: 8px;
}

.status-text {
  color: #495057;
  font-size: 14px;
  font-weight: 500;
}

    /* 测试需求弹窗样式 */
.catalog-dialog-content {
  max-height: 70vh;
  overflow-y: auto;
}

.dialog-header {
  margin-bottom: 20px;
}

.dialog-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 15px;
}

/* 格式示例已移除 */

.validation-result {
  margin-top: 15px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.validation-errors h4 {
  color: #dc3545;
  font-size: 14px;
  margin: 0 0 8px 0;
}

.validation-warnings h4 {
  color: #ffc107;
  font-size: 14px;
  margin: 0 0 8px 0;
}

.validation-errors ul,
.validation-warnings ul {
  margin: 0;
  padding-left: 20px;
}

.error-item {
  color: #dc3545;
  font-size: 13px;
  margin-bottom: 4px;
}

.warning-item {
  color: #856404;
  font-size: 13px;
  margin-bottom: 4px;
}

/* 两列布局样式 */
.main-layout {
  min-height: 600px;
  width: 100%;
  align-items: stretch;
}

.left-section {
  padding-right: 20px;
  border-right: 1px solid #e6e6e6;
  display: flex;
  flex-direction: column;
}

.right-section {
  padding-left: 20px;
  display: flex;
  flex-direction: column;
}

.requirement-catalog-section {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.upload-section h3 {
  margin-top: 0;
}

    /* 测试需求编辑相关样式 */
.catalog-editing {
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 8px;
  padding: 15px;
  margin-top: 20px;
}

/* 编辑模式的格式示例已移除 */

.catalog-confirmed-content {
  margin-top: 10px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 15px;
}

.catalog-confirmed-content pre {
  margin: 0;
  font-family: monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 大屏幕优化 */
@media (min-width: 1200px) {
  .main-card {
    max-width: 1400px;
  }
  
  .left-section {
    padding-right: 30px;
  }
  
  .right-section {
    padding-left: 30px;
  }
}

@media (min-width: 1600px) {
  .main-card {
    max-width: 1600px;
  }
}
</style>

<script>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, MagicStick, Document, Download, Refresh, CircleCheck, CircleCheckFilled, Loading, CircleClose, Edit, InfoFilled, Search, CaretRight, WarningFilled } from '@element-plus/icons-vue'
import { configurationItemService } from '@/services/configurationItemService'
import OCRImageUpload from '@/components/OCRImageUpload.vue'

export default {
  name: 'ConfigurationTestView',
  components: {
    UploadFilled,
    MagicStick,
    Document,
    Download,
    Refresh,
    CircleCheck,
    CircleCheckFilled,
    CircleClose,
    Edit,
    OCRImageUpload,
    Loading,
    InfoFilled,
    Search,
    CaretRight,
    WarningFilled
  },
  setup() {
    const basicInfoForm = ref(null)
    const requirementUpload = ref(null)
    
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
        productType: '',
        detectorFlag: '有检测仪',
        aiAnalysis: true,
        deepAnalysis: true
    })

    // 检测仪标识：用开关展示，但底层仍保持“有检测仪/无检测仪”字符串
    const hasDetector = computed({
      get: () => basicInfo.detectorFlag === '有检测仪',
      set: (val) => {
        basicInfo.detectorFlag = val ? '有检测仪' : '无检测仪'
      }
    })

    // 可选信息
    const optionalInfo = reactive({
        aircraftModel: '',
        projectDirector: '',
        developmentDepartment: '',
        chiefDesigner: '',
        projectManager: ''
    })

    // 折叠面板状态（默认展开“可选信息”）
    const activeCollapse = ref(['optional'])
    
    // 上传信息
    const uploadInfo = reactive({
      requirementFile: null,
      requirementUploaded: false
    })

          // 测试需求提取信息
    const catalogExtraction = reactive({
      status: 'waiting', // waiting, extracting, extracted, confirmed, failed
      extracting: false,  // 🔧 新增：分析状态标志
      formattedCatalog: '',
      catalogItems: [],
      totalItems: 0,
      error: null,
      // 🔧 新增：计时功能
      startTime: null,
      endTime: null,
      duration: 0 // 分析耗时（毫秒）
    })

          // 测试需求编辑数据
    const catalogDialog = reactive({
      content: '',
      validation: null
    })

          // 测试需求级别过滤
    const catalogLevelFilter = ref('all')
    
    // 可编辑的需求列表（用于编辑状态）
    const editableCatalogItems = ref([])
    
    // 文件列表
    const requirementFileList = ref([])
    
    // 生成状态 (保留旧的变量用于兼容)
    const isGenerating = ref(false)
    const generationProgress = ref(0)
    const generationStatus = ref('')
    const generationMessage = ref('')
    const generationComplete = ref(false)
    
    // 轮询定时器管理
    let pollTimer = null
    let currentTaskId = null
    
    // 🚀 新增：分步生成状态管理
    const step1State = reactive({
      completed: false,
      running: false,
      progress: 0,
      message: '',
      files: [],
      taskId: null,
      completedAt: ''
    })
    
    const step2State = reactive({
      completed: false,
      running: false,
      uploaded: false,       // ✅ 新增：是否已上传步骤1结果
      uploadedFile: '',      // ✅ 新增：上传的文件名
      progress: 0,
      message: '',
      files: [],
      taskId: null,
      completedAt: ''
    })
    
    // 步骤3拆分为3a和3b两个子阶段
    const step3State = reactive({
      // 步骤3a: 生成基础信息
      step3a: {
        completed: false,
        running: false,
        uploaded: false,      // 是否已上传步骤2结果
        uploadedFile: '',
        progress: 0,
        message: '',
        files: [],
        taskId: null,
        completedAt: ''
      },
      // 步骤3b: 完善测试项
      step3b: {
        completed: false,
        running: false,
        uploaded: false,      // 是否已上传步骤3a结果
        uploadedFile: '',
        progress: 0,
        message: '',
        files: [],
        taskId: null,
        completedAt: ''
      },
      // 整体状态
      completed: false,
      running: false,
      progress: 0,
      message: '',
      files: [],
      taskId: null,
      completedAt: ''
    })
    
    const step4State = reactive({
      completed: false,
      running: false,
      uploaded: false,       // ✅ 新增：是否已上传步骤3结果
      uploadedFile: '',      // ✅ 新增：上传的文件名
      progress: 0,
      message: '',
      files: [],
      taskId: null,
      completedAt: ''
    })
    
    // 步骤轮询定时器
    const stepPollTimers = {
      step1: null,
      step2: null,
      step3a: null,
      step3b: null,
      step3: null,
      step4: null
    }
    
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
    const projectManagers = ref([])

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
      productType: [{ required: true, message: '请选择产品类型', trigger: 'change' }],
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
                           basicInfo.productType && 
                           basicInfo.domain;
      
      const hasRequirementFile = uploadInfo.requirementUploaded;
      
              // 需要测试需求已确认才能生成
      const hasCatalog = catalogExtraction.status === 'confirmed';
      
      console.log('按钮状态检查:', {
        hasBasicInfo,
        hasRequirementFile,
        hasCatalog,
        catalogStatus: catalogExtraction.status
      });
      
      return hasBasicInfo && hasRequirementFile && hasCatalog;
    })
    
    // ✨ 新增：步骤1前置条件状态计算属性
    const step1Preconditions = computed(() => {
      return {
        requirementUploaded: uploadInfo.requirementUploaded,
        basicInfoComplete: basicInfo.testManager && 
                          basicInfo.testPersonnel && 
                          basicInfo.developer && 
                          basicInfo.softwareName && 
                          basicInfo.softwareVersion && 
                          basicInfo.softwareId && 
                          basicInfo.productType && 
                          basicInfo.domain
      }
    })
    
    // 🚀 新增：步骤启动条件计算属性
    const canStartStep1 = computed(() => {
      const conditions = step1Preconditions.value
      return conditions.requirementUploaded && 
             conditions.basicInfoComplete && 
             !step1State.running && 
             !step1State.completed
    })
    
    const canStartStep2 = computed(() => {
      return step1State.completed && 
             catalogExtraction.status === 'confirmed' && 
             !step2State.running && 
             !step2State.completed
    })
    
    const canStartStep3 = computed(() => {
      return step2State.completed && !step3State.running && !step3State.completed
    })
    
    const canStartStep4 = computed(() => {
      return step3State.completed && !step4State.running && !step4State.completed
    })
    
    const allStepsCompleted = computed(() => {
      return step1State.completed && step2State.completed && step3State.completed && step4State.completed
    })

          // 检查某个测试需求项是否有子章节
    const hasSubItems = (item, allItems) => {
      // 🔧 修复：使用正确的字段名 number 而不是 numbering
      const currentNumber = item.number || item.numbering || ''
      if (!currentNumber) return false
      
      return allItems.some(otherItem => {
        const otherNumber = otherItem.number || otherItem.numbering || ''
        return otherNumber !== currentNumber && 
               otherNumber.startsWith(currentNumber + '.')
      })
    }

          // 根据级别过滤测试需求项（智能层级过滤）
    const filteredCatalogItems = computed(() => {
      if (!catalogExtraction.catalogItems || catalogExtraction.catalogItems.length === 0) {
        return []
      }
      
      const allItems = catalogExtraction.catalogItems
      
      // 处理"全部"选项：显示所有级别，但依然只显示叶子节点（没有子章节的需求项）
      if (catalogLevelFilter.value === 'all') {
        return allItems.filter(item => {
          // 检查是否有子章节
          const hasChildren = hasSubItems(item, allItems)
          // 只显示没有子章节的叶子节点
          return !hasChildren
        })
      }
      
      const targetLevel = parseInt(catalogLevelFilter.value)
      
      return allItems.filter(item => {
        // 级别高于目标级别的不显示
        if (item.level > targetLevel) {
          return false
        }
        
        // 特殊处理：选择3级时，显示所有3级需求（不管是否有子章节）
        if (targetLevel === 3) {
          return item.level === 3
        }
        
        // 选择4级及以上时：隐藏有子章节的需求，只显示叶子节点
        const hasChildren = hasSubItems(item, allItems)
        if (hasChildren) {
          return false
        }
        
        // 只显示没有子章节的叶子节点
        return true
      })
    })

    // 生成显示的测试需求文本
    const displayedCatalog = computed(() => {
      if (!filteredCatalogItems.value || filteredCatalogItems.value.length === 0) {
        return '暂无测试需求项'
      }
      
      return filteredCatalogItems.value
        .map(item => {
          const indent = '  '.repeat(Math.max(0, item.level - 3))
          // 🔧 修复：使用后端生成的 full_text 或 text，避免前端拼接导致重复
          // 后端已经正确处理了编号和标题的组合，直接使用即可
          const displayText = item.full_text || item.text || `${item.number || item.numbering || ''} ${item.title}`
          return `${indent}${displayText}`
        })
        .join('\n')
    })

    // 生成带过滤状态的需求列表（用于彩色显示）
    const catalogItemsWithFilterStatus = computed(() => {
      if (!catalogExtraction.catalogItems || catalogExtraction.catalogItems.length === 0) {
        return []
      }
      
      const allItems = catalogExtraction.catalogItems
      const filteredIds = new Set(filteredCatalogItems.value.map(item => 
        item.number || item.numbering || item.id
      ))
      
      return allItems.map(item => {
        const itemId = item.number || item.numbering || item.id
        const isFiltered = !filteredIds.has(itemId)
        const indent = Math.max(0, item.level - 3)
        const displayText = item.full_text || item.text || `${item.number || item.numbering || ''} ${item.title}`
        
        return {
          ...item,
          isFiltered,
          indent,
          displayText
        }
      })
    })

    // 获取过滤描述文本
    const getFilterDescription = () => {
      const total = catalogExtraction.catalogItems?.length || 0
      const filtered = filteredCatalogItems.value?.length || 0
      const excluded = total - filtered
      
      if (catalogLevelFilter.value === 'all') {
        return `显示全部叶子节点：${filtered}项，已过滤${excluded}项（有子章节）`
      } else if (catalogLevelFilter.value === '3') {
        return `显示所有3级需求：${filtered}项，已过滤${excluded}项`
      } else {
        return `显示≤${catalogLevelFilter.value}级叶子节点：${filtered}项，已过滤${excluded}项（有子章节）`
      }
    }

    // 文件上传处理
    const handleRequirementUpload = async (file) => {
      console.log('开始上传需求文档:', file.name, '大小:', file.size)
      console.log('文件对象:', file)
      
      // 🔧 修复：立即设置上传状态和分析状态
      uploadInfo.requirementUploaded = true  // 立即设置为已上传，显示分析界面
      catalogExtraction.status = 'extracting'
      catalogExtraction.extracting = true
      
      // 🔧 新增：记录开始时间
      catalogExtraction.startTime = Date.now()
      catalogExtraction.endTime = null
      catalogExtraction.duration = 0
      
      try {
        const response = await configurationItemService.uploadRequirement(file)
        console.log('上传响应:', response)
        console.log('响应数据:', response.data)
        
        const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

        // 轮询：软件信息
        const pollSoftwareInfo = async () => {
          const maxAttempts = 60
          for (let i = 0; i < maxAttempts; i++) {
            try {
              const res = await configurationItemService.getSoftwareInfo(sessionId.value)
              const data = res?.data
              if (data?.status === 'success' && data?.software_info) {
                const info = data.software_info
                if (info.software_name) basicInfo.softwareName = info.software_name
                if (info.software_version) basicInfo.softwareVersion = info.software_version
                if (info.software_id) basicInfo.softwareId = info.software_id
                return true
              }
            } catch (e) {
              // ignore and retry
            }
            await sleep(800)
          }
          return false
        }

        // 轮询：目录/测试需求
        const pollCatalog = async () => {
          const maxAttempts = 90
          for (let i = 0; i < maxAttempts; i++) {
            try {
              const res = await configurationItemService.getCatalogExtraction(sessionId.value)
              const data = res?.data
              const catalogResult = data?.catalog_extraction
              if (data?.status === 'success' && catalogResult && catalogResult.status === 'success') {
                catalogExtraction.endTime = Date.now()
                catalogExtraction.duration = catalogExtraction.endTime - catalogExtraction.startTime
                catalogExtraction.status = 'extracted'
                catalogExtraction.extracting = false
                catalogExtraction.catalogItems = catalogResult.filtered_items || []
                catalogExtraction.totalItems = catalogResult.filtered_count || 0
                catalogExtraction.error = null
                catalogExtraction.formattedCatalog = (catalogExtraction.catalogItems || [])
                  .map(item => item.full_text || item.text || `${item.number} ${item.title}`)
                  .join('\n')
                catalogLevelFilter.value = 'all'
                return true
              }
              if (data?.status === 'error' || catalogResult?.status === 'error') {
                catalogExtraction.status = 'failed'
                catalogExtraction.extracting = false
                catalogExtraction.error = catalogResult?.message || data?.message || '测试需求提取失败'
                return false
              }
            } catch (e) {
              // ignore and retry
            }
            await sleep(800)
          }
          return false
        }

        // 检查响应状态
        if (response && response.data && response.data.status === 'success') {
          // 🔧 修复：创建符合ElementPlus规范的文件信息对象
          const fileInfo = {
            name: file.name,
            size: file.size,
            type: file.type,
            uid: file.uid || Date.now(), // 使用原文件的uid或生成新的
            status: 'success',
            percentage: 100,
            raw: file // 保留原始文件引用
          }
          
          // 立即更新状态
          sessionId.value = response.data.session_id
          uploadInfo.requirementFile = fileInfo
          uploadInfo.requirementUploaded = true
          
          // 🔧 修复：确保文件列表包含正确的文件对象
          requirementFileList.value = [fileInfo]
          
          // ✅ 改为：上传秒回后并行轮询（谁先好谁先填）
          const [softwareOk, catalogOk] = await Promise.all([pollSoftwareInfo(), pollCatalog()])

          if (!softwareOk) {
            ElMessage.info('软件信息仍在提取中或提取失败，请稍后重试或手动填写')
          } else {
            ElMessage.success('软件信息已自动填充到表单中')
          }
          if (!catalogOk) {
            // catalogOk=false 代表超时或失败，poll里已设置failed则给error
            if (catalogExtraction.status !== 'failed') {
              ElMessage.info('测试需求仍在提取中，请稍后查看')
            }
          }
          
          console.log('状态更新完成:')
          console.log('- sessionId:', sessionId.value)
          console.log('- requirementFile:', uploadInfo.requirementFile)
          console.log('- requirementUploaded:', uploadInfo.requirementUploaded)
          console.log('- catalogExtraction:', catalogExtraction)
          
          ElMessage.success(`需求文档 "${file.name}" 上传成功`)
          
          // 强制触发响应式更新（如果需要）
          await nextTick()
          
          // 🚀 新增：加载生成状态（用于断点续传）
          await loadGenerationState()
          
        } else {
          console.error('上传响应格式错误:', response)
          
          // 🔧 修复：响应格式错误时重置状态
          uploadInfo.requirementUploaded = false
          catalogExtraction.status = 'waiting'
          catalogExtraction.extracting = false
          
          ElMessage.error('上传响应格式错误')
        }
      } catch (error) {
        console.error('需求文档上传失败:', error)
        console.error('错误详情:', error.response)
        
        // 🔧 修复：上传失败时重置状态
        uploadInfo.requirementUploaded = false
        catalogExtraction.status = 'waiting'
        catalogExtraction.extracting = false
        
        ElMessage.error('需求文档上传失败: ' + (error.response?.data?.detail || error.message))
      }
      
      return false // 阻止Element Plus的自动上传
    }
    

    
    
    // 文件删除处理
    const handleRequirementRemove = (file, fileList) => {
      console.log('移除需求文档:', file)
      console.log('当前状态:', catalogExtraction.status)
      
      // 🔧 修复：如果正在处理或已完成处理，不要自动移除
      if (catalogExtraction.status === 'extracting' || catalogExtraction.status === 'extracted') {
        console.log('🔧 跳过自动移除，因为正在处理或已完成')
        return false // 阻止移除
      }
      
      uploadInfo.requirementFile = null
      uploadInfo.requirementUploaded = false
      requirementFileList.value = []
      // 重置会话和测试需求状态
      sessionId.value = null
      catalogExtraction.status = 'waiting'
      catalogExtraction.extracting = false
      catalogExtraction.formattedCatalog = ''
      catalogExtraction.catalogItems = []
      catalogExtraction.totalItems = 0
      catalogExtraction.error = null
      // 重置级别过滤器
      catalogLevelFilter.value = 'all'
      
      ElMessage.success('需求文档已移除')
    }
    
          // 启用测试需求编辑模式
    const enableCatalogEdit = () => {
      catalogExtraction.status = 'editing'
      catalogDialog.content = catalogExtraction.formattedCatalog || ''
      catalogDialog.validation = null
      
      // 初始化可编辑列表（深拷贝）
      editableCatalogItems.value = JSON.parse(JSON.stringify(
        catalogItemsWithFilterStatus.value
      ))
    }
    
    // 更新单个需求项的文本
    const updateCatalogItemText = (index, event) => {
      const newText = event.target.innerText.trim()
      if (editableCatalogItems.value[index]) {
        editableCatalogItems.value[index].displayText = newText
      }
    }
    
    // 处理回车键（换行）
    const handleEnterKey = (index, event) => {
      // 阻止默认换行，但允许Shift+Enter换行
      if (!event.shiftKey) {
        event.preventDefault()
        // 可以在这里添加插入新行的逻辑
      }
    }

          // 取消测试需求编辑
    const cancelCatalogEdit = () => {
      catalogExtraction.status = catalogExtraction.totalItems > 0 ? 'extracted' : 'waiting'
      catalogDialog.content = ''
      catalogDialog.validation = null
    }

          // 快速确认测试需求（不编辑）
    const quickConfirmCatalog = async () => {
      try {
        const response = await configurationItemService.confirmCatalog(
          sessionId.value, 
          displayedCatalog.value
        )
        
                  console.log('快速确认测试需求响应:', response)
          
          if (response.data && response.data.status === 'success') {
            // 更新测试需求状态
            catalogExtraction.status = 'confirmed'
            // 更新存储的测试需求内容为当前显示的过滤内容
          catalogExtraction.formattedCatalog = displayedCatalog.value
                        ElMessage.success('测试需求确认成功！现在可以开始生成测试表单了')
                  } else {
            ElMessage.error(response.data?.message || '测试需求确认失败')
          }
        } catch (error) {
          console.error('确认测试需求失败:', error)
          ElMessage.error('确认测试需求失败：' + (error.response?.data?.message || error.message))
      }
    }

    // 更新测试需求显示（级别过滤变化时）
    const updateCatalogDisplay = () => {
      const targetLevel = catalogLevelFilter.value
      const displayInfo = targetLevel === 'all' 
        ? '全部级别' 
        : targetLevel === '3'
          ? '所有3级需求'
          : `≤${targetLevel}级叶子节点（智能过滤）`
      console.log('测试需求级别过滤变更为:', displayInfo)
      console.log('过滤后的需求项数量:', filteredCatalogItems.value.length)
      
      // 调试信息：显示过滤逻辑
      if (targetLevel !== 'all') {
        console.log('过滤逻辑:')
        if (targetLevel === '3') {
          console.log('- 显示所有3级需求（包括有子章节的）')
        } else {
          console.log(`- 显示${targetLevel}级及以下的需求`)
          console.log('- 隐藏所有有子章节的需求（4级及以上适用）')
          console.log('- 只保留叶子节点需求')
        }
      }
    }

          // 确认测试需求编辑
    const confirmCatalogEdit = async () => {
      // 从可编辑列表重建内容字符串
      const editedContent = editableCatalogItems.value
        .map(item => {
          const indent = '  '.repeat(item.indent)
          return `${indent}${item.displayText}`
        })
        .join('\n')
      
      if (!editedContent.trim()) {
        ElMessage.error('测试需求内容不能为空')
        return
      }

      try {
        const response = await configurationItemService.confirmCatalog(
          sessionId.value, 
          editedContent
        )
        
        console.log('确认测试需求响应:', response)
          
        if (response.data && response.data.status === 'success') {
          // 更新测试需求状态
          catalogExtraction.status = 'confirmed'
          catalogExtraction.formattedCatalog = editedContent
          catalogExtraction.totalItems = response.data.validation?.catalog_items?.length || 0
          
          // 更新原始数据
          if (response.data.validation?.catalog_items) {
            catalogExtraction.catalogItems = response.data.validation.catalog_items
          }
          
          catalogDialog.validation = null
          
          ElMessage.success('测试需求确认成功')
        } else if (response.data && response.data.validation) {
          // 显示验证结果
          catalogDialog.validation = response.data.validation
          
          if (response.data.validation.errors.length === 0) {
            ElMessage.success('测试需求验证通过')
          } else {
            ElMessage.warning('测试需求格式有误，请检查')
          }
        } else {
          throw new Error('测试需求确认响应格式错误')
        }
        
      } catch (error) {
        console.error('测试需求确认失败:', error)
        catalogDialog.validation = null
        ElMessage.error('测试需求确认失败: ' + error.message)
      }
    }
    
          // 重新提取测试需求
    const reExtractCatalog = async () => {
      if (!sessionId.value) {
        ElMessage.error('请先上传需求文档')
        return
      }
      
      try {
        const response = await configurationItemService.reExtractCatalog(sessionId.value)
                  console.log('重新提取测试需求响应:', response)
        
        if (response && response.data && response.data.status === 'success') {
          const catalogResult = response.data.catalog_extraction
          if (catalogResult && catalogResult.success) {
            catalogExtraction.status = 'extracted'
            
            // 兼容后端返回的字段名称
            catalogExtraction.formattedCatalog = catalogResult.formatted_catalog || catalogResult.catalog_content || ''
            catalogExtraction.catalogItems = catalogResult.catalog_items || []
            catalogExtraction.totalItems = catalogResult.total_items || catalogResult.total_count || 0
            catalogExtraction.error = null
            
            // 如果没有formatted_catalog，根据catalog_items生成格式化字符串
            if (!catalogExtraction.formattedCatalog && catalogExtraction.catalogItems.length > 0) {
              catalogExtraction.formattedCatalog = catalogExtraction.catalogItems
                .map(item => item.full_text || `${item.numbering} ${item.title}`)
                .join('\n')
            }
            
            // 重置级别过滤器
            catalogLevelFilter.value = 'all'
            
            console.log('重新提取测试需求成功，数量:', catalogExtraction.totalItems)
            console.log('重新提取的需求项目:', catalogExtraction.catalogItems)
            
            ElMessage.success('测试需求重新提取成功')
          } else {
            catalogExtraction.status = 'failed'
            catalogExtraction.error = catalogResult?.error || '测试需求提取失败'
            ElMessage.error('测试需求提取失败: ' + catalogExtraction.error)
          }
        } else {
          throw new Error('重新提取测试需求响应格式错误')
        }
        
      } catch (error) {
        console.error('重新提取测试需求失败:', error)
        catalogExtraction.status = 'failed'
        catalogExtraction.error = error.message
        ElMessage.error('重新提取测试需求失败: ' + error.message)
      }
    }

    // 开始生成
    const startGeneration = async () => {
      try {
        console.log('开始生成测试表单...')
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
          ElMessage.error('请先上传需求文档')
          return
        }
        
        // 清理之前的轮询（如果存在）
        if (pollTimer) {
          clearTimeout(pollTimer)
          pollTimer = null
        }
        
        isGenerating.value = true
        generationProgress.value = 0
        generationStatus.value = 'active'
        generationMessage.value = '正在准备生成...'
        generationComplete.value = false
        
        // 调用生成API启动异步任务
        const codeLines = codeAnalysis.value.hasResult ? codeAnalysis.value.result.total_lines : null
        const response = await configurationItemService.generateForms(sessionId.value, {
          ...basicInfo
        }, optionalInfo, codeLines)
        
        console.log('任务启动响应:', response.data)
        
        if (response.data.status === 'success') {
          const taskId = response.data.task_id
          console.log('任务ID:', taskId)
          
          // 清理之前的轮询（如果存在）
          if (pollTimer) {
            clearTimeout(pollTimer)
            pollTimer = null
          }
          
          // 设置当前任务ID
          currentTaskId = taskId
          
          // 开始轮询任务状态
          const pollTaskStatus = async () => {
            try {
              const statusResponse = await configurationItemService.getTaskStatus(taskId)
              const taskStatus = statusResponse.data.task_status
              
              console.log('任务状态:', taskStatus)
              
              // 更新进度
              generationProgress.value = taskStatus.progress || 0
              generationMessage.value = taskStatus.message || '处理中...'
              
              if (taskStatus.status === 'completed') {
                // 任务完成
                generationProgress.value = 100
                generationStatus.value = 'success'
                generationMessage.value = '测试表单生成成功！'
                generationComplete.value = true
                isGenerating.value = false
                
                // 获取生成的文件列表
                downloadFiles.value = taskStatus.generated_files || []
                
                // 清理轮询
                pollTimer = null
                currentTaskId = null
                
                ElMessage.success('测试表单生成成功！')
                
              } else if (taskStatus.status === 'failed') {
                // 任务失败
                isGenerating.value = false
                
                // 清理轮询
                pollTimer = null
                currentTaskId = null
                
                throw new Error(taskStatus.error || '任务执行失败')
                
              } else if (taskStatus.status === 'running') {
                // 任务仍在运行，继续轮询
                pollTimer = setTimeout(pollTaskStatus, 2000) // 2秒后再次检查
                
              } else if (taskStatus.status === 'not_found') {
                // 任务不存在，停止轮询
                console.warn('任务不存在，停止轮询')
                isGenerating.value = false
                generationMessage.value = '任务不存在'
                pollTimer = null
                currentTaskId = null
                
              } else {
                // 其他未知状态，继续轮询
                pollTimer = setTimeout(pollTaskStatus, 2000)
              }
              
            } catch (error) {
              console.error('获取任务状态失败:', error)
              // 继续轮询，避免因网络问题中断
              pollTimer = setTimeout(pollTaskStatus, 3000)
            }
          }
          
          // 开始轮询
          pollTimer = setTimeout(pollTaskStatus, 1000) // 1秒后开始第一次检查
          
        } else {
          throw new Error(response.data.message || '任务启动失败')
        }
        
      } catch (error) {
        console.error('生成失败:', error)
        
        // 清理轮询
        if (pollTimer) {
          clearTimeout(pollTimer)
          pollTimer = null
        }
        
        generationProgress.value = 0
        generationStatus.value = 'exception'
        generationMessage.value = '生成失败: ' + error.message
        isGenerating.value = false
        ElMessage.error('生成失败: ' + error.message)
      }
    }
    
    // 下载文件
    const downloadFile = async (file) => {
      try {
        if (!sessionId.value) {
          ElMessage.error('会话不存在')
          return
        }
        
        const filename = typeof file === 'string' ? file : file.name
        
        // 添加到下载中列表
        downloadingFiles.value.push(filename)
        
        const response = await configurationItemService.downloadFile(sessionId.value, filename)
        
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
        const filename = typeof file === 'string' ? file : file.name
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
        
        // 🚀 修改：收集所有步骤生成的文件
        const allFiles = [
          ...step1State.files,
          ...step2State.files,
          ...step3State.files,
          ...step4State.files
        ]
        
        if (allFiles.length === 0) {
          ElMessage.warning('没有可下载的文件')
          return
        }
        
        for (const file of allFiles) {
          await downloadFile(file)
          // 添加延迟避免并发问题
          await new Promise(resolve => setTimeout(resolve, 500))
        }
        
        ElMessage.success(`所有文件下载完成 (${allFiles.length} 个文件)`)
      } catch (error) {
        console.error('批量下载失败:', error)
        ElMessage.error('批量下载失败: ' + error.message)
      } finally {
        downloadingAll.value = false
      }
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
        }
        
        // 填充可选信息
        if (extractedData.optional_info) {
          const optionalData = extractedData.optional_info
          
          if (optionalData.aircraft_model) optionalInfo.aircraftModel = optionalData.aircraft_model
          if (optionalData.project_director) optionalInfo.projectDirector = optionalData.project_director
          if (optionalData.development_department) optionalInfo.developmentDepartment = optionalData.development_department
          if (optionalData.chief_designer) optionalInfo.chiefDesigner = optionalData.chief_designer
          if (optionalData.project_manager) optionalInfo.projectManager = optionalData.project_manager
          
          // ✅ OCR识别的组件字段填充到productType
          if (optionalData.component) basicInfo.productType = optionalData.component
        }
        
        ElMessage.success('OCR数据已自动填入表单')
        
      } catch (error) {
        console.error('处理OCR数据失败:', error)
        ElMessage.error('处理OCR数据失败')
      }
    }

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
        chiefDesigner: '',
        projectManager: ''
      })

      // 重置折叠状态
      activeCollapse.value = []
      
      // 重置上传信息
      Object.assign(uploadInfo, {
        requirementFile: null,
        catalogFile: null,
        requirementUploaded: false,
        catalogUploaded: false
      })
      
      // 清空文件列表
      requirementFileList.value = []
      catalogFileList.value = []
      
      // 重置生成状态
      isGenerating.value = false
      generationProgress.value = 0
      generationStatus.value = ''
      generationMessage.value = ''
      generationComplete.value = false
      
      // 清空下载文件
      downloadFiles.value = []
      
      ElMessage.success('表单已重置')
    }

    // 加载下拉数据
    const loadDropdownData = async () => {
      try {
        // 并行加载所有下拉数据
        const [domainsRes, managersRes, personnelRes, developersRes] = await Promise.all([
          configurationItemService.getDomains(),
          configurationItemService.getTestManagers(),
          configurationItemService.getTestPersonnel(),
          configurationItemService.getDevelopers()
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
        const [modelsRes, directorsRes, departmentsRes, designersRes, managersRes] = await Promise.all([
          configurationItemService.getAircraftModels(),
          configurationItemService.getProjectDirectors(), 
          configurationItemService.getDevelopmentDepartments(),
          configurationItemService.getChiefDesigners(),
          configurationItemService.getProjectManagers()
        ])

        aircraftModels.value = modelsRes.data.data || []
        projectDirectors.value = directorsRes.data.data || []
        developmentDepartments.value = departmentsRes.data.data || []
        chiefDesigners.value = designersRes.data.data || []
        projectManagers.value = managersRes.data.data || []
      } catch (error) {
        console.error('加载可选信息下拉数据失败:', error)
        ElMessage.error('加载可选信息下拉数据失败')
      }
    }

    // 处理领域变化
    const handleDomainChange = async (value) => {
      if (value && !domains.value.find(item => item.value === value)) {
        try {
          await configurationItemService.addDomain(value)
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
          await configurationItemService.addTestManager(value)
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
          await configurationItemService.addTestPersonnel(value)
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

    // 处理产品类型变化
    const handleProductTypeChange = (value) => {
      console.log('产品类型变化:', value)
      // 产品类型是固定选项，不需要添加到数据库
    }

    // 处理开发人员变化
    const handleDeveloperChange = async (value) => {
      if (value && !developers.value.find(item => item.value === value)) {
        try {
          await configurationItemService.addDeveloper(value)
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
    
    // 格式化文件大小
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    // 可选信息字段处理函数
    const handleAircraftModelChange = async (value) => {
      if (value && !aircraftModels.value.find(item => item.value === value)) {
        try {
          await configurationItemService.addAircraftModel(value)
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
          await configurationItemService.addProjectDirector(value)
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
          await configurationItemService.addDevelopmentDepartment(value)
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
          await configurationItemService.addChiefDesigner(value)
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

    const handleProjectManagerChange = async (value) => {
      if (value && !projectManagers.value.find(item => item.value === value)) {
        try {
          await configurationItemService.addProjectManager(value)
          await loadOptionalDropdownData()
          ElMessage.success('新项目主管添加成功')
        } catch (error) {
          console.error('添加项目主管失败:', error)
          if (error.response?.status === 400) {
            ElMessage.warning('该项目主管已存在')
          } else {
            ElMessage.error('添加项目主管失败')
          }
        }
      }
    }

    // ========================= 代码分析相关方法 =========================
    
    // 处理代码文件上传
    const handleCodeUpload = async (file) => {
      try {
        codeAnalysis.value.isUploading = true
        
        const response = await configurationItemService.uploadCodeForAnalysis(file)
        
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
          await configurationItemService.deleteCodeAnalysis(codeAnalysis.value.taskId)
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

    // 🚀 新增：加载生成状态
    const loadGenerationState = async () => {
      if (!sessionId.value) return
      
      try {
        const response = await configurationItemService.getGenerationState(sessionId.value)
        
        if (response.data && response.data.status === 'success') {
          const state = response.data.state
          
          if (state && state.completed_steps) {
            // ✅ 恢复需求确认状态（用于步骤2前置条件）
            const catalogConfirmed = state.catalog_confirmed === true
            if (catalogConfirmed) {
              catalogExtraction.status = 'confirmed'
              catalogExtraction.extracting = false
            } else if (Array.isArray(state.catalog_items) && state.catalog_items.length > 0) {
              // 有提取结果但未确认
              if (catalogExtraction.status !== 'editing') {
                catalogExtraction.status = 'extracted'
              }
            }

            // 更新步骤1状态
            if (state.completed_steps.step1_project_info) {
              const step1 = state.completed_steps.step1_project_info
              step1State.completed = step1.completed || false
              step1State.files = step1.output_files || []
              step1State.completedAt = step1.completed_at || ''
            }
            
            // 更新步骤2状态
            if (state.completed_steps.step2_test_issue) {
              const step2 = state.completed_steps.step2_test_issue
              step2State.completed = step2.completed || false
              step2State.files = step2.output_files || []
              step2State.completedAt = step2.completed_at || ''
            }
            
            // ✅ 更新步骤2上传状态
            if (state.step2_uploaded_file) {
              step2State.uploaded = true
              step2State.uploadedFile = state.step2_uploaded_file.split(/[/\\]/).pop() // 提取文件名
            }
            
            // 更新步骤3a状态
            if (state.completed_steps.step3a_requirement_basic) {
              const step3a = state.completed_steps.step3a_requirement_basic
              step3State.step3a.completed = step3a.completed || false
              step3State.step3a.files = step3a.output_files || []
              step3State.step3a.completedAt = step3a.completed_at || ''
            }
            
            // ✅ 更新步骤3a上传状态（步骤2的结果）
            if (state.step3_uploaded_file) {
              step3State.step3a.uploaded = true
              step3State.step3a.uploadedFile = state.step3_uploaded_file.split(/[/\\]/).pop()
            }
            
            // 更新步骤3b状态
            if (state.completed_steps.step3b_test_items) {
              const step3b = state.completed_steps.step3b_test_items
              step3State.step3b.completed = step3b.completed || false
              step3State.step3b.files = step3b.output_files || []
              step3State.step3b.completedAt = step3b.completed_at || ''
            }
            
            // ✅ 更新步骤3b上传状态（步骤3a的结果）
            if (state.step3b_uploaded_file) {
              step3State.step3b.uploaded = true
              step3State.step3b.uploadedFile = state.step3b_uploaded_file.split(/[/\\]/).pop()
            }
            
            // ✅ 更新步骤3整体状态（兼容旧逻辑）
            if (state.completed_steps.step3_requirement_analysis) {
              const step3 = state.completed_steps.step3_requirement_analysis
              step3State.completed = step3.completed || false
              step3State.files = step3.output_files || []
              step3State.completedAt = step3.completed_at || ''
            }
            
            // 更新步骤4状态
            if (state.completed_steps.step4_test_case) {
              const step4 = state.completed_steps.step4_test_case
              step4State.completed = step4.completed || false
              step4State.files = step4.output_files || []
              step4State.completedAt = step4.completed_at || ''
            }
            
            // ✅ 更新步骤4上传状态
            if (state.step4_uploaded_file) {
              step4State.uploaded = true
              step4State.uploadedFile = state.step4_uploaded_file.split(/[/\\]/).pop() // 提取文件名
            }
            
            console.log('生成状态加载成功:', state)
          }
        }
      } catch (error) {
        console.error('加载生成状态失败:', error)
      }
    }
    
    // 🚀 新增：轮询步骤状态
    const pollStepStatus = (stepName, stepState) => {
      if (!stepState.taskId) return
      
      const pollFunction = async () => {
        try {
          const response = await configurationItemService.getTaskStatus(stepState.taskId)
          const taskStatus = response.data.task_status
          
          stepState.progress = taskStatus.progress || 0
          stepState.message = taskStatus.message || '处理中...'
          
          if (taskStatus.status === 'completed') {
            stepState.running = false
            stepState.completed = true
            stepState.files = taskStatus.generated_files || []
            stepState.completedAt = new Date().toLocaleString()
            
            // ✅ 特殊处理步骤3的子步骤
            if (stepName === 'step3a') {
              step3State.running = false
              ElMessage.success('步骤3a 完成！请下载并上传修改后的文件')
            } else if (stepName === 'step3b') {
              step3State.running = false
              step3State.completed = true
              step3State.files = taskStatus.generated_files || []
              step3State.completedAt = new Date().toLocaleString()
              ElMessage.success('步骤3b 完成！整个步骤3已完成')
            } else {
              ElMessage.success(`${stepName} 完成！`)
            }
            
            // 停止轮询
            if (stepPollTimers[stepName]) {
              clearTimeout(stepPollTimers[stepName])
              stepPollTimers[stepName] = null
            }
            
            // 重新加载完整状态
            await loadGenerationState()
            
          } else if (taskStatus.status === 'failed') {
            stepState.running = false
            stepState.completed = false
            
            // 停止轮询
            if (stepPollTimers[stepName]) {
              clearTimeout(stepPollTimers[stepName])
              stepPollTimers[stepName] = null
            }
            
            ElMessage.error(`${stepName} 失败: ${taskStatus.error}`)
            
          } else if (taskStatus.status === 'running') {
            // 继续轮询
            stepPollTimers[stepName] = setTimeout(pollFunction, 2000)
          }
        } catch (error) {
          console.error(`轮询${stepName}状态失败:`, error)
          // 继续轮询
          stepPollTimers[stepName] = setTimeout(pollFunction, 3000)
        }
      }
      
      // 开始轮询
      stepPollTimers[stepName] = setTimeout(pollFunction, 1000)
    }
    
    // 🚀 新增：步骤1生成方法
    const generateStep1 = async () => {
      try {
        if (!sessionId.value) {
          ElMessage.error('请先上传需求文档')
          return
        }
        
        // 验证基本信息
        const isValid = await basicInfoForm.value.validate()
        if (!isValid) {
          ElMessage.error('请完善基本信息')
          return
        }
        
        step1State.running = true
        step1State.progress = 0
        step1State.message = '正在启动生成...'
        
        const codeLines = codeAnalysis.value.hasResult ? codeAnalysis.value.result.total_lines : null
        const response = await configurationItemService.generateProjectInfo(
          sessionId.value,
          basicInfo,
          optionalInfo,
          codeLines
        )
        
        if (response.data.status === 'success') {
          step1State.taskId = response.data.task_id
          pollStepStatus('step1', step1State)
        } else {
          step1State.running = false
          ElMessage.error(response.data.message || '启动失败')
        }
      } catch (error) {
        console.error('步骤1启动失败:', error)
        step1State.running = false
        ElMessage.error('启动失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // 🚀 新增：步骤2生成方法
    // 🚀 新增：步骤2文件上传处理
    const handleStep2FileChange = async (file) => {
      try {
        if (!sessionId.value) {
          ElMessage.error('会话不存在')
          return
        }
        
        const formData = new FormData()
        formData.append('file', file.raw)
        formData.append('session_id', sessionId.value)
        
        ElMessage.info('正在上传文件...')
        
        const response = await configurationItemService.uploadStep1Result(formData)
        
        if (response.data.status === 'success') {
          step2State.uploaded = true
          step2State.uploadedFile = file.name
          ElMessage.success('上传成功！可以开始生成步骤2')
        } else {
          ElMessage.error(response.data.message || '上传失败')
        }
      } catch (error) {
        console.error('步骤2文件上传失败:', error)
        ElMessage.error('上传失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    const generateStep2 = async () => {
      try {
        if (!sessionId.value) {
          ElMessage.error('会话不存在')
          return
        }
        
        if (!step2State.uploaded) {
          ElMessage.error('请先上传步骤1的结果文件')
          return
        }
        
        step2State.running = true
        step2State.progress = 0
        step2State.message = '正在启动生成...'
        
        const response = await configurationItemService.generateTestIssue(sessionId.value)
        
        if (response.data.status === 'success') {
          step2State.taskId = response.data.task_id
          pollStepStatus('step2', step2State)
        } else {
          step2State.running = false
          ElMessage.error(response.data.message || '启动失败')
        }
      } catch (error) {
        console.error('步骤2启动失败:', error)
        step2State.running = false
        ElMessage.error('启动失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // 🚀 新增：步骤3生成方法
    // 🚀 步骤3文件上传处理（步骤2的结果，用于3a）
    const handleStep3FileChange = async (file) => {
      try {
        if (!sessionId.value) {
          ElMessage.error('会话不存在')
          return
        }
        
        const formData = new FormData()
        formData.append('file', file.raw)
        formData.append('session_id', sessionId.value)
        
        ElMessage.info('正在上传文件...')
        
        const response = await configurationItemService.uploadStep2Result(formData)
        
        if (response.data.status === 'success') {
          step3State.step3a.uploaded = true
          step3State.step3a.uploadedFile = file.name
          ElMessage.success('上传成功！可以开始生成步骤3a')
        } else {
          ElMessage.error(response.data.message || '上传失败')
        }
      } catch (error) {
        console.error('步骤3文件上传失败:', error)
        ElMessage.error('上传失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // 🚀 步骤3a结果上传处理（用于3b）
    const handleStep3aFileChange = async (file) => {
      try {
        if (!sessionId.value) {
          ElMessage.error('会话不存在')
          return
        }
        
        const formData = new FormData()
        formData.append('file', file.raw)
        formData.append('session_id', sessionId.value)
        
        ElMessage.info('正在上传文件...')
        
        const response = await configurationItemService.uploadStep3aResult(formData)
        
        if (response.data.status === 'success') {
          step3State.step3b.uploaded = true
          step3State.step3b.uploadedFile = file.name
          ElMessage.success('上传成功！可以开始生成步骤3b')
        } else {
          ElMessage.error(response.data.message || '上传失败')
        }
      } catch (error) {
        console.error('步骤3a结果上传失败:', error)
        ElMessage.error('上传失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // 🚀 新增：步骤4文件上传处理
    const handleStep4FileChange = async (file) => {
      try {
        if (!sessionId.value) {
          ElMessage.error('会话不存在')
          return
        }
        
        const formData = new FormData()
        formData.append('file', file.raw)
        formData.append('session_id', sessionId.value)
        
        ElMessage.info('正在上传文件...')
        
        const response = await configurationItemService.uploadStep3Result(formData)
        
        if (response.data.status === 'success') {
          step4State.uploaded = true
          step4State.uploadedFile = file.name
          ElMessage.success('上传成功！可以开始生成步骤4')
        } else {
          ElMessage.error(response.data.message || '上传失败')
        }
      } catch (error) {
        console.error('步骤4文件上传失败:', error)
        ElMessage.error('上传失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // 🚀 步骤3a生成方法
    const generateStep3a = async () => {
      try {
        if (!sessionId.value) {
          ElMessage.error('会话不存在')
          return
        }
        
        if (!step3State.step3a.uploaded) {
          ElMessage.error('请先上传步骤2的结果文件')
          return
        }
        
        step3State.step3a.running = true
        step3State.running = true
        step3State.step3a.progress = 0
        step3State.step3a.message = '正在启动生成...'
        
        const response = await configurationItemService.generateRequirementBasic(
          sessionId.value,
          basicInfo.aiAnalysis !== false,
          basicInfo.deepAnalysis !== false
        )
        
        if (response.data.status === 'success') {
          step3State.step3a.taskId = response.data.task_id
          pollStepStatus('step3a', step3State.step3a)
        } else {
          step3State.step3a.running = false
          step3State.running = false
          ElMessage.error(response.data.message || '启动失败')
        }
      } catch (error) {
        console.error('步骤3a启动失败:', error)
        step3State.step3a.running = false
        step3State.running = false
        ElMessage.error('启动失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // 🚀 步骤3b生成方法
    const generateStep3b = async () => {
      try {
        if (!sessionId.value) {
          ElMessage.error('会话不存在')
          return
        }
        
        if (!step3State.step3b.uploaded) {
          ElMessage.error('请先上传步骤3a的结果文件')
          return
        }
        
        step3State.step3b.running = true
        step3State.running = true
        step3State.step3b.progress = 0
        step3State.step3b.message = '正在启动生成...'
        
        const response = await configurationItemService.generateTestItems(
          sessionId.value,
          basicInfo.aiAnalysis !== false
        )
        
        if (response.data.status === 'success') {
          step3State.step3b.taskId = response.data.task_id
          pollStepStatus('step3b', step3State.step3b)
        } else {
          step3State.step3b.running = false
          step3State.running = false
          ElMessage.error(response.data.message || '启动失败')
        }
      } catch (error) {
        console.error('步骤3b启动失败:', error)
        step3State.step3b.running = false
        step3State.running = false
        ElMessage.error('启动失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // 🚀 新增：步骤4生成方法
    const generateStep4 = async () => {
      try {
        if (!sessionId.value) {
          ElMessage.error('会话不存在')
          return
        }
        
        if (!step4State.uploaded) {
          ElMessage.error('请先上传步骤3的结果文件')
          return
        }
        
        step4State.running = true
        step4State.progress = 0
        step4State.message = '正在启动生成...'
        
        const response = await configurationItemService.generateTestCase(
          sessionId.value,
          basicInfo.aiAnalysis !== false
        )
        
        if (response.data.status === 'success') {
          step4State.taskId = response.data.task_id
          pollStepStatus('step4', step4State)
        } else {
          step4State.running = false
          ElMessage.error(response.data.message || '启动失败')
        }
      } catch (error) {
        console.error('步骤4启动失败:', error)
        step4State.running = false
        ElMessage.error('启动失败: ' + (error.response?.data?.detail || error.message))
      }
    }

    // 组件挂载时加载下拉数据
    onMounted(() => {
      loadDropdownData()
      loadOptionalDropdownData()
    })

    // 组件销毁时清理轮询
    onUnmounted(() => {
      if (pollTimer) {
        clearTimeout(pollTimer)
        pollTimer = null
      }
      
      // 清理所有步骤轮询定时器
      Object.values(stepPollTimers).forEach(timer => {
        if (timer) {
          clearTimeout(timer)
        }
      })
    })

    return {
      basicInfoForm,
      requirementUpload,
      sessionId,
      basicInfo,
      hasDetector,
      uploadInfo,
      catalogExtraction,
      catalogDialog,
      requirementFileList,
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
      catalogLevelFilter,
      filteredCatalogItems,
      displayedCatalog,
      catalogItemsWithFilterStatus,
      editableCatalogItems,
      getFilterDescription,
      updateCatalogDisplay,
      updateCatalogItemText,
      handleEnterKey,
      handleRequirementUpload,
      handleRequirementRemove,
      quickConfirmCatalog,
      enableCatalogEdit,
      cancelCatalogEdit,
      confirmCatalogEdit,
      reExtractCatalog,
      startGeneration,
      downloadFile,
      downloadAllFiles,
      resetForm,
      formatFileSize,
      loadDropdownData,
      handleDomainChange,
      handleTestManagerChange,
      handleTestPersonnelChange,
      handleProductTypeChange,
      handleDeveloperChange,
      // 可选信息相关
      optionalInfo,
      activeCollapse,
      aircraftModels,
      projectDirectors,
      developmentDepartments,
      chiefDesigners,
      projectManagers,
      loadOptionalDropdownData,
      handleAircraftModelChange,
      handleProjectDirectorChange,
      handleDevelopmentDepartmentChange,
      handleChiefDesignerChange,
      handleProjectManagerChange,
      // OCR相关
      handleOCRDataExtracted,
      configurationItemService,
      // 代码分析相关
      codeFileList,
      codeAnalysis,
      handleCodeUpload,
      handleCodeRemove,
      clearCodeAnalysis,
      showCodeAnalysisDetails,
      // 🚀 新增：分步生成相关
      step1State,
      step2State,
      step3State,
      step4State,
      step1Preconditions,
      canStartStep1,
      canStartStep2,
      canStartStep3,
      canStartStep4,
      allStepsCompleted,
      generateStep1,
      handleStep2FileChange,
      generateStep2,
      generateStep3a,
      handleStep3FileChange,
      generateStep3b,
      handleStep3aFileChange,
      generateStep4,
      handleStep4FileChange,
      loadGenerationState
    }
  }
}
</script>

<style scoped>
/* 用户说明样式 */
.user-tips {
  display: flex;
  align-items: flex-start;
  margin: 10px 0;
  padding: 12px;
  background-color: #f0f9ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  color: #1e40af;
  font-size: 13px;
  line-height: 1.5;
}

.tip-icon {
  margin-right: 8px;
  margin-top: 2px;
  color: #3b82f6;
  flex-shrink: 0;
}

.tip-text {
  flex: 1;
}

.tip-text strong {
  color: #1e40af;
  font-weight: 600;
}

/* 级别选择器样式 */
.level-selector {
  margin: 10px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.level-description {
  font-size: 12px;
  color: #6b7280;
  margin-left: 8px;
}

/* 🔧 新增：正在分析状态样式 */
.catalog-extracting {
  padding: 20px;
  text-align: center;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin: 10px 0;
}

.extracting-content {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
}

.extracting-icon {
  font-size: 20px;
  color: #3b82f6;
  margin-right: 10px;
}

.extracting-text {
  font-size: 16px;
  color: #374151;
  font-weight: 500;
}

.extracting-progress {
  margin-top: 10px;
}

.progress-text {
  font-size: 12px;
  color: #6b7280;
  margin-top: 8px;
  display: block;
}

/* 🔧 新增：耗时信息样式 */
.duration-info {
  font-size: 12px;
  color: #67c23a;
  font-weight: normal;
  margin-left: 8px;
}

/* 旋转动画 */
.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 🚀 新增：分步生成样式 */
.generation-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.generation-description {
  color: #606266;
  font-size: 14px;
  margin: 0;
}

.step-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.step-card {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.step-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.step-card.step-completed {
  border-color: #67c23a;
  background-color: #f0f9ff;
}

.step-card.step-running {
  border-color: #409eff;
  background-color: #f0f8ff;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.step-number {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  font-size: 18px;
  font-weight: bold;
  color: #909399;
}

.step-number .step-num {
  font-size: 18px;
  font-weight: bold;
  color: #909399;
}

.step-icon.success {
  font-size: 36px;
  color: #67c23a;
}

.step-icon.running {
  font-size: 36px;
  color: #409eff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.step-title-area h4 {
  margin: 0 0 3px 0;
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
}

.step-subtitle {
  margin: 0;
  font-size: 11px;
  color: #909399;
  line-height: 1.3;
}

.step-body {
  min-height: 60px;
}

.step-result {
  padding: 10px;
  background-color: #f0f9ff;
  border-radius: 6px;
}

.result-text {
  margin: 0 0 6px 0;
  font-size: 12px;
  font-weight: 500;
  color: #67c23a;
}

.file-list {
  list-style: none;
  padding: 0;
  margin: 0 0 6px 0;
}

.file-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 3px 0;
  font-size: 11px;
  color: #606266;
  border-bottom: 1px dashed #e4e7ed;
}

.file-list li:last-child {
  border-bottom: none;
}

.file-list li span {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 8px;
}

.completion-time {
  margin: 0;
  font-size: 10px;
  color: #909399;
  text-align: right;
}

.step-progress {
  padding: 8px;
}

.progress-msg {
  margin: 8px 0 0 0;
  font-size: 11px;
  color: #606266;
  text-align: center;
}

.step-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

/* ✨ 新增：前置条件列表样式 */
.precondition-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 4px;
}

.precondition-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #e6a23c;
  padding: 4px 8px;
  border-radius: 4px;
  background-color: #f5f7fa;
  transition: all 0.3s;
}

.precondition-item.completed {
  color: #67c23a;
  background-color: #f0f9ff;
}

.precondition-item .check-icon {
  color: #67c23a;
  font-size: 14px;
  flex-shrink: 0;
}

.precondition-item .pending-icon {
  color: #dcdfe6;
  font-size: 14px;
  flex-shrink: 0;
}

.precondition-text {
  flex: 1;
  line-height: 1.4;
  color: #e6a23c;
}

.precondition-item.completed .precondition-text {
  color: #67c23a;
}

.step-tip {
  margin: 0;
  font-size: 13px;
  color: #e6a23c;
  text-align: center;
  line-height: 1.3;
}

/* 🚀 新增：步骤2上传区域样式 */
.step-upload {
  text-align: center;
  padding: 10px 0;
}

.upload-tip {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #e6a23c;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.upload-success {
  margin: 0 0 8px 0;
  font-size: 11px;
  color: #67c23a;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

/* 🚀 子步骤样式 */
.sub-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sub-step {
  padding: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background-color: #fafafa;
  transition: all 0.3s;
}

.sub-step-completed {
  border-color: #67c23a;
  background-color: #f0f9ff;
}

.sub-step-running {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.sub-step-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.sub-step-title .el-icon {
  font-size: 14px;
}

.sub-step-text {
  font-weight: 600;
}

.sub-step-content {
  padding-left: 20px;
}

.sub-progress-msg {
  font-size: 10px;
  color: #909399;
  margin-top: 4px;
  text-align: center;
}

.upload-success-small, .upload-tip-small, .step-tip-small {
  font-size: 14px;
  margin: 4px 0;
}

.upload-success-small {
  color: #67c23a;
}

.upload-tip-small {
  color: #e6a23c;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  background-color: #f5f7fa;
}

.step-tip-small {
  color: #e6a23c;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  background-color: #f5f7fa;
}

.download-all-section {
  text-align: center;
  margin-top: 30px;
  padding: 20px;
  background-color: #f0f9ff;
  border-radius: 8px;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .step-cards {
    grid-template-columns: 1fr;
  }
}
</style> 