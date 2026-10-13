<template>
  <div class="static-analysis-filter">
    <div class="header">
      <h2>🚀 静态分析问题智能过滤工具</h2>
      <p class="description">上传静态分析结果和代码库，基于GJB8114规则和CEW规则智能过滤并生成格式化问题单</p>
    </div>

    <!-- 文件上传和规则选择区域 -->
    <div v-if="!processing && !completed" class="main-content">
      <!-- 文件上传区域 -->
      <div class="upload-container">
        <!-- Excel文件上传 -->
        <div class="upload-item">
          <div class="upload-header">
            <h3>📊 静态分析结果文件</h3>
            <el-tag :type="selectedExcelFile ? 'success' : 'info'" size="small">
              {{ selectedExcelFile ? '已选择' : '必需' }}
            </el-tag>
          </div>
          <el-upload
            ref="excelUploadRef"
            class="upload-dragger compact"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".xlsx"
            :on-change="handleExcelFileChange"
            :file-list="excelFileList"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .xlsx 格式
              </div>
            </template>
          </el-upload>
        </div>

        <!-- 代码库上传 -->
        <div class="upload-item">
          <div class="upload-header">
            <h3>📁 代码库文件</h3>
            <el-tag :type="selectedCodebaseFile ? 'success' : 'warning'" size="small">
              {{ selectedCodebaseFile ? '已选择' : '必需' }}
            </el-tag>
          </div>
          <el-upload
            ref="codebaseUploadRef"
            class="upload-dragger compact"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".zip"
            :on-change="handleCodebaseFileChange"
            :file-list="codebaseFileList"
          >
            <el-icon class="el-icon--upload"><folder-add /></el-icon>
            <div class="el-upload__text">
              拖拽或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .zip 格式
              </div>
            </template>
          </el-upload>
        </div>
      </div>

      <!-- 规则选择区域 - 支持Tab切换 -->
      <div class="rules-section">
        <el-tabs v-model="activeRuleType" @tab-change="handleRuleTypeChange">
          <!-- GJB8114规则Tab -->
          <el-tab-pane label="GJB8114规则" name="gjb">
            <div class="rules-header">
              <div class="rules-title">
                <h3>🎯 选择要应用的GJB8114规则</h3>
                <div class="rules-summary">
                  <span class="selected-count">已选择 {{ selectedRules.length }}/{{ totalRulesCount }} 规则</span>
                </div>
              </div>
              <div class="rules-actions">
                <el-button size="small" @click="selectAllRules">全选</el-button>
                <el-button size="small" @click="deselectAllRules">全不选</el-button>
                <el-button size="small" @click="selectAccurateOnly">仅选确定规则</el-button>
                <el-button size="small" @click="selectUncertainOnly">仅选不确定规则</el-button>
                <el-button size="small" type="warning" @click="showSaveConfigDialog">
                  <el-icon><Lock /></el-icon>
                  保存为默认配置
                </el-button>
              </div>
            </div>

            <div class="rules-container">
              <!-- 确定规则列表 -->
              <div class="rules-column accurate-column">
                <div class="column-header">
                  <div class="header-content">
                    <h4>✅ 确定规则</h4>
                    <div class="rule-count">{{ accurateRules.length }} 条</div>
                  </div>
                  <p class="header-desc">语法分析即可准确识别</p>
                </div>
                <div class="rules-list">
                  <el-checkbox-group v-model="selectedRules">
                    <div v-for="rule in accurateRules" :key="rule.rule_code" class="rule-item" :class="{'rule-modified': isRuleModified('gjb', rule.rule_code)}">
                      <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                        <div class="rule-content">
                          <div class="rule-name">{{ rule.rule_code }}</div>
                          <div class="rule-description">{{ rule.rule_description }}</div>
                          <div class="rule-meta">
                            <el-tag size="small" type="success">{{ rule.category }}</el-tag>
                            <el-tag size="small" plain>{{ rule.detection_method }}</el-tag>
                          </div>
                        </div>
                      </el-checkbox>
                      <el-button
                        size="small"
                        type="warning"
                        plain
                        @click="moveRuleToUncertain('gjb', rule.rule_code)"
                        class="move-rule-btn"
                        title="移动到不确定规则"
                      >
                        <el-icon><Bottom /></el-icon>
                        移至不确定
                      </el-button>
                    </div>
                  </el-checkbox-group>
                </div>
              </div>

              <!-- 不确定规则列表 -->
              <div class="rules-column uncertain-column">
                <div class="column-header">
                  <div class="header-content">
                    <h4>⚠️ 不确定规则</h4>
                    <div class="rule-count">{{ uncertainRules.length }} 条</div>
                  </div>
                  <p class="header-desc">需AI分析代码上下文</p>
                </div>
                <div class="rules-list">
                  <el-checkbox-group v-model="selectedRules">
                    <div v-for="rule in uncertainRules" :key="rule.rule_code" class="rule-item" :class="{'rule-modified': isRuleModified('gjb', rule.rule_code)}">
                      <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                        <div class="rule-content">
                          <div class="rule-name">{{ rule.rule_code }}</div>
                          <div class="rule-description">{{ rule.rule_description }}</div>
                          <div class="rule-meta">
                            <el-tag size="small" type="warning">{{ rule.category }}</el-tag>
                            <el-tag size="small" plain>{{ rule.analysis_complexity }}</el-tag>
                          </div>
                        </div>
                      </el-checkbox>
                      <el-button
                        size="small"
                        type="success"
                        plain
                        @click="moveRuleToAccurate('gjb', rule.rule_code)"
                        class="move-rule-btn"
                        title="移动到确定规则"
                      >
                        <el-icon><Top /></el-icon>
                        移至确定
                      </el-button>
                    </div>
                  </el-checkbox-group>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- CWE规则Tab -->
          <el-tab-pane label="CWE规则" name="cwe">
            <div class="rules-header">
              <div class="rules-title">
                <h3>🛡️ 选择要应用的CWE规则</h3>
                <div class="rules-summary">
                  <span class="selected-count">
                    已选择 {{ selectedCweAccurateRules.length + selectedCweUncertainRules.length }}/{{ cweAccurateRules.length + cweUncertainRules.length }} 规则
                  </span>
                </div>
              </div>
              <div class="rules-actions">
                <el-button size="small" @click="selectAllCweRules">全选</el-button>
                <el-button size="small" @click="deselectAllCweRules">全不选</el-button>
                <el-button size="small" @click="selectCweAccurateOnly">仅选确定规则</el-button>
                <el-button size="small" @click="selectCweUncertainOnly">仅选不确定规则</el-button>
                <el-button size="small" type="warning" @click="showSaveConfigDialog">
                  <el-icon><Lock /></el-icon>
                  保存为默认配置
                </el-button>
              </div>
            </div>

            <div class="rules-container">
              <!-- CWE确定规则列表 -->
              <div class="rules-column accurate-column">
                <div class="column-header">
                  <div class="header-content">
                    <h4>✅ 确定规则</h4>
                    <div class="rule-count">{{ cweAccurateRules.length }} 条</div>
                  </div>
                  <p class="header-desc">语法分析即可准确识别</p>
                </div>
                <div class="rules-list">
                  <el-checkbox-group v-model="selectedCweAccurateRules">
                    <div v-for="rule in cweAccurateRules" :key="rule.rule_code" class="rule-item" :class="{'rule-modified': isRuleModified('cwe', rule.rule_code)}">
                      <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                        <div class="rule-content">
                          <div class="rule-name">{{ rule.rule_code }}</div>
                          <div class="rule-description">{{ rule.rule_name }}</div>
                          <div class="rule-meta">
                            <el-tag size="small" type="success">CWE</el-tag>
                            <span v-if="rule.description" class="meta-desc">{{ rule.description }}</span>
                          </div>
                        </div>
                      </el-checkbox>
                      <el-button
                        size="small"
                        type="warning"
                        plain
                        @click="moveRuleToUncertain('cwe', rule.rule_code)"
                        class="move-rule-btn"
                        title="移动到不确定规则"
                      >
                        <el-icon><Bottom /></el-icon>
                        移至不确定
                      </el-button>
                    </div>
                  </el-checkbox-group>
                </div>
              </div>

              <!-- CWE不确定规则列表 -->
              <div class="rules-column uncertain-column">
                <div class="column-header">
                  <div class="header-content">
                    <h4>⚠️ 不确定规则</h4>
                    <div class="rule-count">{{ cweUncertainRules.length }} 条</div>
                  </div>
                  <p class="header-desc">需AI分析代码上下文</p>
                </div>
                <div class="rules-list">
                  <el-checkbox-group v-model="selectedCweUncertainRules">
                    <div v-for="rule in cweUncertainRules" :key="rule.rule_code" class="rule-item" :class="{'rule-modified': isRuleModified('cwe', rule.rule_code)}">
                      <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                        <div class="rule-content">
                          <div class="rule-name">{{ rule.rule_code }}</div>
                          <div class="rule-description">{{ rule.rule_name }}</div>
                          <div class="rule-meta">
                            <el-tag size="small" type="warning">CWE</el-tag>
                            <span v-if="rule.description" class="meta-desc">{{ rule.description }}</span>
                          </div>
                        </div>
                      </el-checkbox>
                      <el-button
                        size="small"
                        type="success"
                        plain
                        @click="moveRuleToAccurate('cwe', rule.rule_code)"
                        class="move-rule-btn"
                        title="移动到确定规则"
                      >
                        <el-icon><Top /></el-icon>
                        移至确定
                      </el-button>
                    </div>
                  </el-checkbox-group>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 开始处理按钮 -->
      <div class="start-processing">
        <div class="processing-info">
          <div class="info-item">
            <el-icon><document /></el-icon>
            <span>Excel文件: {{ selectedExcelFile ? '✅' : '❌' }}</span>
          </div>
          <div class="info-item">
            <el-icon><folder /></el-icon>
            <span>代码库: {{ selectedCodebaseFile ? '✅' : '❌' }}</span>
          </div>
          <div class="info-item">
            <el-icon><check /></el-icon>
            <span>规则: {{ selectedRules.length }} 条</span>
          </div>
        </div>
        <el-button 
          type="primary" 
          size="large"
          :disabled="!canStartProcessing"
          @click="startProcessing"
          class="start-btn"
        >
          <el-icon><caret-right /></el-icon>
          开始智能过滤处理
        </el-button>
      </div>
    </div>

    <!-- 双进度显示区域（GJB + CWE） -->
    <div v-if="processing || completed" class="dual-progress-container">
      <!-- GJB8114进度卡片 -->
      <div class="progress-card gjb-progress-card">
        <div class="card-header-banner gjb-banner">
          <h3>🔍 GJB8114规则审查进度</h3>
          <el-tag :type="getStatusTagType(gjbProgress.status)" size="large">
            {{ getStatusText(gjbProgress.status) }}
          </el-tag>
        </div>
        
        <div class="card-content">
          <el-progress 
            :percentage="gjbProgress.progress" 
            :stroke-width="12"
            :status="getProgressStatusByState(gjbProgress.status)"
            class="main-progress"
          >
            <span class="progress-text">{{ gjbProgress.aiProcessedIssues }}/{{ gjbProgress.aiProcessingTotal }}</span>
          </el-progress>

          <!-- 当前分析信息 -->
          <div v-if="gjbProgress.status === 'processing' && gjbProgress.currentAnalyzingIssue" class="current-analysis-info gjb-analysis">
            <div class="analysis-header">
              <span class="analysis-icon">🔬</span>
              <span class="analysis-title">正在分析</span>
            </div>
            <div class="analysis-content">
              <div class="issue-name">{{ gjbProgress.currentAnalyzingIssue }}</div>
              <div class="tool-calls">已调用工具 {{ gjbProgress.toolCallsCount }} 次</div>
            </div>
          </div>

          <!-- 详细统计信息 -->
          <div class="detailed-stats">
            <div class="stats-row">
              <div class="stat-item-detail">
                <span class="stat-label">📊 总问题数</span>
                <span class="stat-value primary">{{ gjbProgress.totalIssues }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">✅ 确定规则</span>
                <span class="stat-value success">{{ gjbProgress.accurateIssues }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">⚠️ 不确定规则</span>
                <span class="stat-value warning">{{ gjbProgress.uncertainIssues }}</span>
              </div>
            </div>
            <div class="stats-row">
              <div class="stat-item-detail">
                <span class="stat-label">🔬 不确定（已勾选）</span>
                <span class="stat-value info">{{ gjbProgress.aiProcessedIssues }}/{{ gjbProgress.aiProcessingTotal }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">🗑️ 过滤掉</span>
                <span class="stat-value danger">{{ gjbProgress.filteredIssues }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">✨ 最终保留</span>
                <span class="stat-value primary-bold">{{ gjbProgress.retainedIssues }}</span>
              </div>
            </div>
          </div>

          <!-- 后台整理提示 -->
          <div v-if="processing && !gjbProgress.accurate_ready" class="preparing-hint preparing-hint-gjb">
            <div class="preparing-hint-icon">🗂️</div>
            <div class="preparing-hint-content">
              <div class="preparing-hint-title">后台正在整理 GJB 数据</div>
              <div class="preparing-hint-text">系统正在汇总问题并生成“未经AI过滤”问题单，请稍候，文件准备完成后会自动出现下载按钮。</div>
            </div>
          </div>

          <!-- GJB下载按钮区域 -->
          <div v-if="gjbProgress.accurate_ready || gjbProgress.status === 'completed'" class="download-buttons">
            <!-- 合并下载按钮（四个Sheet） - accurate_ready 时显示 -->
            <el-button 
              v-if="gjbProgress.accurate_ready"
              type="primary" 
              size="default"
              :loading="downloadingGjbAllSplit"
              @click="downloadGjbAllSplit"
              class="download-btn-compact download-btn-wide"
            >
              <el-icon><download /></el-icon>
              下载GJB全部问题单（未经AI过滤）
            </el-button>
            <!-- 完整问题单 - 只在所有处理完成后显示 -->
            <el-button 
              v-if="gjbProgress.status === 'completed' && gjbProgress.aiProcessingTotal > 0"
              type="primary" 
              size="default"
              :loading="downloadingGjbFull"
              @click="downloadGjbFull"
              class="download-btn-compact download-btn-full-wide-gjb"
            >
              <el-icon><download /></el-icon>
              下载GJB完整问题单（AI过滤后）
            </el-button>
            <!-- 代码视图 - 在所有处理完成后显示 -->
            <el-button 
              v-if="gjbProgress.status === 'completed'"
              type="success" 
              size="default"
              @click="openCodeView('gjb')"
              class="download-btn-compact"
            >
              <el-icon><View /></el-icon>
              AI分析结果代码视图
            </el-button>
          </div>
        </div>
      </div>

      <!-- CWE规则进度卡片 -->
      <div class="progress-card cwe-progress-card">
        <div class="card-header-banner cwe-banner">
          <h3>🛡️ CWE规则审查进度</h3>
          <el-tag :type="getStatusTagType(cweProgress.status)" size="large">
            {{ getStatusText(cweProgress.status) }}
          </el-tag>
        </div>
        
        <div class="card-content">
          <el-progress 
            :percentage="cweProgress.progress" 
            :stroke-width="12"
            :status="getProgressStatusByState(cweProgress.status)"
            class="main-progress"
          >
            <span class="progress-text">{{ cweProgress.aiProcessedIssues }}/{{ cweProgress.aiProcessingTotal }}</span>
          </el-progress>

          <!-- 当前分析信息 -->
          <div v-if="cweProgress.status === 'processing' && cweProgress.currentAnalyzingIssue" class="current-analysis-info cwe-analysis">
            <div class="analysis-header">
              <span class="analysis-icon">🔬</span>
              <span class="analysis-title">正在分析</span>
            </div>
            <div class="analysis-content">
              <div class="issue-name">{{ cweProgress.currentAnalyzingIssue }}</div>
              <div class="tool-calls">已调用工具 {{ cweProgress.toolCallsCount }} 次</div>
            </div>
          </div>

          <!-- 详细统计信息 -->
          <div class="detailed-stats">
            <div class="stats-row">
              <div class="stat-item-detail">
                <span class="stat-label">📊 总问题数</span>
                <span class="stat-value primary">{{ cweProgress.totalIssues }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">✅ 确定规则</span>
                <span class="stat-value success">{{ cweProgress.accurateIssues }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">⚠️ 不确定规则</span>
                <span class="stat-value warning">{{ cweProgress.uncertainIssues }}</span>
              </div>
            </div>
            <div class="stats-row">
              <div class="stat-item-detail">
                <span class="stat-label">🔬 不确定（已勾选）</span>
                <span class="stat-value info">{{ cweProgress.aiProcessedIssues }}/{{ cweProgress.aiProcessingTotal }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">🗑️ 过滤掉</span>
                <span class="stat-value danger">{{ cweProgress.filteredIssues }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">✨ 最终保留</span>
                <span class="stat-value primary-bold">{{ cweProgress.retainedIssues }}</span>
              </div>
            </div>
          </div>

          <!-- 后台整理提示 -->
          <div v-if="processing && !cweProgress.accurate_ready" class="preparing-hint preparing-hint-cwe">
            <div class="preparing-hint-icon">🗂️</div>
            <div class="preparing-hint-content">
              <div class="preparing-hint-title">后台正在整理 CWE 数据</div>
              <div class="preparing-hint-text">系统正在汇总问题并生成“未经AI过滤”问题单，请稍候，文件准备完成后会自动出现下载按钮。</div>
            </div>
          </div>

          <!-- CWE下载按钮区域 -->
          <div v-if="cweProgress.accurate_ready || cweProgress.status === 'completed'" class="download-buttons">
            <!-- 合并下载按钮（四个Sheet） - accurate_ready 时显示 -->
            <el-button 
              v-if="cweProgress.accurate_ready"
              type="primary" 
              size="default"
              :loading="downloadingCweAllSplit"
              @click="downloadCweAllSplit"
              class="download-btn-compact download-btn-wide download-btn-wide-cwe"
            >
              <el-icon><download /></el-icon>
              下载CWE全部问题单（未经AI过滤）
            </el-button>
            <!-- 完整问题单 - 只在所有处理完成后显示 -->
            <el-button 
              v-if="cweProgress.status === 'completed' && cweProgress.aiProcessingTotal > 0"
              type="primary" 
              size="default"
              :loading="downloadingCweFull"
              @click="downloadCweFull"
              class="download-btn-compact download-btn-full-wide-cwe"
            >
              <el-icon><download /></el-icon>
              下载CWE完整问题单（AI过滤后）
            </el-button>
            <!-- 代码视图 - 在所有处理完成后显示 -->
            <el-button 
              v-if="cweProgress.status === 'completed'"
              type="success" 
              size="default"
              @click="openCodeView('cwe')"
              class="download-btn-compact"
            >
              <el-icon><View /></el-icon>
              AI分析结果代码视图
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 重新开始按钮（完成后显示） -->
    <div v-if="completed" class="restart-section-bottom">
      <el-button @click="resetForm" size="large" plain>
        <el-icon><refresh /></el-icon>
        重新开始
      </el-button>
    </div>

    <!-- 保存配置对话框 -->
    <el-dialog
      v-model="saveConfigDialogVisible"
      title="保存默认规则配置"
      width="450px"
      :close-on-click-modal="false"
    >
      <el-form :model="saveConfigForm" label-width="110px">
        <el-collapse v-model="activeCollapseItems" style="margin-bottom: 15px;">
          <el-collapse-item title="🎯 高级过滤配置（可选）" name="customFilters">
            <el-alert type="info" :closable="false" style="margin-bottom: 15px;">
              <p style="margin: 0;">为特定规则配置关键词过滤：问题描述需<strong>同时包含所有关键词</strong>才会被过滤</p>
            </el-alert>
            
            <div v-for="(filter, index) in customFilterList" :key="index" class="filter-item">
              <el-select 
                v-model="filter.ruleCode" 
                placeholder="选择规则"
                filterable
                style="width: 200px;"
              >
                <el-option-group label="GJB8114规则">
                  <el-option 
                    v-for="rule in selectedRules" 
                    :key="rule" 
                    :label="rule" 
                    :value="rule"
                  />
                </el-option-group>
                <el-option-group label="CWE规则">
                  <el-option 
                    v-for="rule in [...selectedCweAccurateRules, ...selectedCweUncertainRules]" 
                    :key="rule" 
                    :label="rule" 
                    :value="rule"
                  />
                </el-option-group>
              </el-select>
              
              <el-input
                v-model="filter.keywords"
                placeholder="输入关键词，多个用逗号分隔"
                style="width: 300px; margin: 0 10px;"
              />
              
              <el-button 
                type="danger" 
                size="small" 
                plain
                @click="removeCustomFilter(index)"
              >
                删除
              </el-button>
            </div>
            
            <el-button 
              type="primary" 
              size="small" 
              plain
              @click="addCustomFilter"
              style="margin-top: 10px;"
            >
              <el-icon><Plus /></el-icon>
              添加过滤规则
            </el-button>
          </el-collapse-item>
          
          <el-collapse-item title="⚙️ 问题数量限制（可选）" name="maxIssues">
            <el-alert type="info" :closable="false" style="margin-bottom: 15px;">
              <p style="margin: 0;">为每个规则设置最多保留的问题数量，超出部分将通过<strong>均匀分布采样</strong>删除</p>
              <p style="margin: 5px 0 0 0; font-size: 12px; color: #909399;">设置为 0 表示不限制问题数量</p>
            </el-alert>
            
            <el-input-number
              v-model="saveConfigForm.maxIssuesPerRule"
              :min="0"
              :max="1000"
              :step="10"
              controls-position="right"
              style="width: 100%;"
            />
          </el-collapse-item>
        </el-collapse>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="saveConfigDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmSaveConfig" :loading="savingConfig">
            确认保存
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 导入配置对话框 -->
    <el-dialog
      v-model="importConfigDialogVisible"
      title="导入规则配置"
      width="450px"
      :close-on-click-modal="false"
    >
      <el-form :model="importConfigForm" label-width="110px">
        <el-form-item label="配置文件">
          <el-upload
            ref="configUploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".json"
            :on-change="handleConfigFileChange"
            :on-remove="handleConfigFileRemove"
          >
            <template #trigger>
              <el-button type="primary" plain>
                <el-icon><Upload /></el-icon>
                选择配置文件
              </el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                请选择之前导出的 JSON 格式配置文件
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importConfigDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="confirmImportConfig" 
            :loading="importingConfig"
            :disabled="!selectedConfigFile"
          >
            确认导入
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox, ElNotification, ElUpload } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { 
  UploadFilled, 
  FolderAdd, 
  Check, 
  Download, 
  Loading, 
  Clock,
  Document,
  Folder,
  CaretRight,
  CircleCheck,
  Refresh,
  Lock,
  View,
  Top,
  Bottom,
  Upload,
  Warning,
  Plus
} from '@element-plus/icons-vue'
import staticAnalysisFilterService from '@/services/staticAnalysisFilterService'

// 响应式数据
const authStore = useAuthStore()
const router = useRouter()
const excelUploadRef = ref()
const codebaseUploadRef = ref()
const selectedExcelFile = ref(null)
const selectedCodebaseFile = ref(null)
const excelFileList = ref([])
const codebaseFileList = ref([])
const sessionId = ref('')
const processing = ref(false)
const completed = ref(false)
const downloadingFirst = ref(false)
const downloadingFinal = ref(false)
const downloadingGjbAccurate = ref(false)
const downloadingGjbUncertainRaw = ref(false)
const downloadingGjbFull = ref(false)
const downloadingCweAccurate = ref(false)
const downloadingCweUncertainRaw = ref(false)
const downloadingCweFull = ref(false)
// 新增：合并导出（四个Sheet）下载loading
const downloadingGjbAllSplit = ref(false)
const downloadingCweAllSplit = ref(false)

// 规则相关 - GJB8114
const accurateRules = ref([])
const uncertainRules = ref([])
const selectedRules = ref([])
const rulesLoaded = ref(false)

// CWE规则
const cweAccurateRules = ref([])
const cweUncertainRules = ref([])
const selectedCweAccurateRules = ref([])

// 规则分类覆盖（用于移动规则）
const ruleOverrides = ref({
  gjb: {}, // { "GJB_R_01_07_11": "uncertain" }
  cwe: {}  // { "S_01_01": "accurate" }
})
const selectedCweUncertainRules = ref([])
const cweRulesLoaded = ref(false)

// 下载选项：是否包含未勾选条目
const includeGjbUnselected = ref(false)
const includeCweUnselected = ref(false)

// 规则类型切换
const activeRuleType = ref('gjb') // 'gjb' 或 'cwe'

// 保存配置相关
const saveConfigDialogVisible = ref(false)
const savingConfig = ref(false)
const saveConfigForm = reactive({
})

// 导入配置相关
const importConfigDialogVisible = ref(false)
const importingConfig = ref(false)
const configUploadRef = ref()
const selectedConfigFile = ref(null)
const configFileList = ref([])
const importPreview = ref(null)
const importConfigForm = reactive({
})

// 自定义过滤配置
const activeCollapseItems = ref([])
const customFilterList = ref([])  // [{ruleCode: 'GJB_R_01_01_01', keywords: 'kw1,kw2'}]

// 问题数量限制配置
const maxIssuesPerRule = ref(0) // 0表示不限制

// 进度数据
const totalIssues = ref(0)
const processedIssues = ref(0)
const filteredIssues = ref(0)
const aiAnalyzedIssues = ref(0)
const accurateIssues = ref(0)
const uncertainIssues = ref(0)
const currentStatus = ref('pending')
const showFirstDownload = ref(false)

// AI分析进度详情
const currentAnalyzingIssue = ref('')
const currentIssueIndex = ref(0)
const totalUncertainIssues = ref(0)
const toolCallsCount = ref(0)

// 双进度跟踪（GJB和CWE）
const gjbProgress = reactive({
  totalIssues: 0,
  accurateIssues: 0,
  uncertainIssues: 0,
  filteredIssues: 0,
  retainedIssues: 0,
  aiProcessingTotal: 0,
  aiProcessedIssues: 0,
  processedIssues: 0,
  currentAnalyzingIssue: '',
  toolCallsCount: 0,
  progress: 0,
  status: 'pending',
  accurate_ready: false  // 新增：确定规则是否已就绪
})

const cweProgress = reactive({
  totalIssues: 0,
  accurateIssues: 0,
  uncertainIssues: 0,
  filteredIssues: 0,
  retainedIssues: 0,
  aiProcessingTotal: 0,
  aiProcessedIssues: 0,
  processedIssues: 0,
  currentAnalyzingIssue: '',
  toolCallsCount: 0,
  progress: 0,
  status: 'pending',
  accurate_ready: false  // 新增：确定规则是否已就绪
})

// 计算属性
const progressPercentage = computed(() => {
  if (totalIssues.value === 0) return 0
  return Math.round((processedIssues.value / totalIssues.value) * 100)
})

const retainedIssues = computed(() => {
  return processedIssues.value - filteredIssues.value
})

const totalRulesCount = computed(() => {
  return accurateRules.value.length + uncertainRules.value.length
})

const canStartProcessing = computed(() => {
  return selectedExcelFile.value && 
         selectedCodebaseFile.value && 
         selectedRules.value.length > 0
})

// 轮询相关
let pollInterval = null

// 组件挂载时加载规则
onMounted(async () => {
  await loadRules()
  // 同时加载CWE规则，确保默认配置正确加载
  await loadCWERules()
})

// 加载GJB8114规则列表
const loadRules = async () => {
  try {
    const [accurateResponse, uncertainResponse] = await Promise.all([
      staticAnalysisFilterService.getRulesByType('accurate'),
      staticAnalysisFilterService.getRulesByType('uncertain')
    ])

    if (accurateResponse.success) {
      accurateRules.value = accurateResponse.rules
    }

    if (uncertainResponse.success) {
      uncertainRules.value = uncertainResponse.rules
    }

    // 尝试加载默认配置
    try {
      const defaultConfig = await staticAnalysisFilterService.loadDefaultRulesConfig()
      if (defaultConfig.success && defaultConfig.has_config && defaultConfig.gjb_rules.length > 0) {
        // 使用默认配置
        const allGjbRules = [
          ...accurateRules.value.map(r => r.rule_code),
          ...uncertainRules.value.map(r => r.rule_code)
        ]
        
        // 只选择配置中存在且在规则列表中的规则
        const validGjbRules = defaultConfig.gjb_rules.filter(code => allGjbRules.includes(code))
        selectedRules.value = validGjbRules
        
        // 加载自定义过滤规则
        if (defaultConfig.custom_filters) {
          loadCustomFilters(defaultConfig.custom_filters)
          console.log('[DEBUG] 已加载自定义过滤规则:', Object.keys(defaultConfig.custom_filters).length, '条')
        }
        
        // 加载问题数量限制配置
        if (defaultConfig.max_issues_per_rule !== undefined) {
          maxIssuesPerRule.value = defaultConfig.max_issues_per_rule
          console.log('[DEBUG] 已加载问题数量限制配置:', defaultConfig.max_issues_per_rule)
        }
        
        console.log('[DEBUG] 已加载GJB默认配置:', validGjbRules.length, '个规则')
      } else {
        // 没有默认配置，全选所有规则
        selectedRules.value = [
          ...accurateRules.value.map(rule => rule.rule_code),
          ...uncertainRules.value.map(rule => rule.rule_code)
        ]
      }
    } catch (configError) {
      // 加载默认配置失败，全选所有规则
      selectedRules.value = [
        ...accurateRules.value.map(rule => rule.rule_code),
        ...uncertainRules.value.map(rule => rule.rule_code)
      ]
    }

    rulesLoaded.value = true
  } catch (error) {
    ElMessage.error('加载GJB规则列表失败: ' + error.message)
  }
}

// 下载GJB全部问题单（四个Sheet）
const downloadGjbAllSplit = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }
  try {
    downloadingGjbAllSplit.value = true
    await downloadWithGeneratingHint({
      ruleType: 'gjb',
      contentType: 'all',
      includeUnselected: false,
      split: true,
      highlightAi: false,
      downloadPrefix: 'GJB全部问题单',
      successMessage: 'GJB全部问题单下载成功（四个Sheet）'
    })
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingGjbAllSplit.value = false
  }
}

// 下载CWE全部问题单（四个Sheet）
const downloadCweAllSplit = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }
  try {
    downloadingCweAllSplit.value = true
    await downloadWithGeneratingHint({
      ruleType: 'cwe',
      contentType: 'all',
      includeUnselected: false,
      split: true,
      highlightAi: false,
      downloadPrefix: 'CWE全部问题单',
      successMessage: 'CWE全部问题单下载成功（四个Sheet）'
    })
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingCweAllSplit.value = false
  }
}

// 下载通用封装：点击下载时若文件生成耗时，弹出提示并轮询等待
const downloadWithGeneratingHint = async ({
  ruleType,
  contentType,
  includeUnselected = false,
  split = false,
  highlightAi = false,
  downloadPrefix,
  successMessage,
}) => {
  if (!sessionId.value) {
    throw new Error('会话ID不存在')
  }

  const doGenerateOnce = async () => {
    return staticAnalysisFilterService.generateOutputFile(
      sessionId.value,
      ruleType,
      contentType,
      includeUnselected,
      split,
      highlightAi
    )
  }

  const triggerDownload = (filename) => {
    const downloadUrl = staticAnalysisFilterService.getDownloadUrl(sessionId.value, filename)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `${downloadPrefix}_${filename}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // 1) 先快速尝试一次：如果已生成则直接下载，不弹窗
  try {
    const firstResp = await doGenerateOnce()
    if (firstResp && firstResp.success && firstResp.filename) {
      triggerDownload(firstResp.filename)
      ElMessage.success(successMessage)
      return
    }
  } catch (_) {
    // 忽略，进入“生成中等待”流程
  }

  // 2) 需要等待时再弹窗（用户可取消）
  let cancelled = false
  let boxVisible = false
  try {
    boxVisible = true
    ElMessageBox.confirm(
      '问题单文件正在生成中，请稍候…（生成完成后会自动开始下载）',
      '正在生成问题单',
      {
        confirmButtonText: '继续等待',
        cancelButtonText: '取消',
        showCancelButton: true,
        closeOnClickModal: false,
        closeOnPressEscape: false,
        type: 'info'
      }
    ).catch(() => {
      cancelled = true
    })

    // 最长等待 10 分钟，每 2 秒尝试一次生成
    const maxWaitMs = 10 * 60 * 1000
    const intervalMs = 2000
    const start = Date.now()
    let lastError = null

    while (!cancelled && Date.now() - start < maxWaitMs) {
      try {
        const resp = await doGenerateOnce()
        if (resp && resp.success && resp.filename) {
          if (boxVisible) {
            ElMessageBox.close()
            boxVisible = false
          }
          triggerDownload(resp.filename)
          ElMessage.success(successMessage)
          return
        }
        lastError = new Error(resp?.error || resp?.message || '生成文件失败')
      } catch (e) {
        lastError = e
      }

      await new Promise(resolve => setTimeout(resolve, intervalMs))
    }

    if (cancelled) {
      throw new Error('已取消等待生成')
    }
    throw lastError || new Error('生成超时，请稍后再试')
  } finally {
    if (boxVisible) {
      ElMessageBox.close()
    }
  }
}

// 加载CWE规则列表
const loadCWERules = async () => {
  try {
    const [accurateResponse, uncertainResponse] = await Promise.all([
      staticAnalysisFilterService.getCWERules('accurate'),
      staticAnalysisFilterService.getCWERules('uncertain')
    ])

    if (accurateResponse.success) {
      cweAccurateRules.value = accurateResponse.rules
    }

    if (uncertainResponse.success) {
      cweUncertainRules.value = uncertainResponse.rules
    }

    // 尝试加载默认配置
    try {
      const defaultConfig = await staticAnalysisFilterService.loadDefaultRulesConfig()
      if (defaultConfig.success && defaultConfig.has_config && defaultConfig.cwe_rules.length > 0) {
        // 使用默认配置
        const allCweRules = [
          ...cweAccurateRules.value.map(r => r.rule_code),
          ...cweUncertainRules.value.map(r => r.rule_code)
        ]
        
        // 只选择配置中存在且在规则列表中的规则
        const validCweRules = defaultConfig.cwe_rules.filter(code => allCweRules.includes(code))
        
        // 分离确定和不确定规则
        selectedCweAccurateRules.value = validCweRules.filter(code => 
          cweAccurateRules.value.some(r => r.rule_code === code)
        )
        selectedCweUncertainRules.value = validCweRules.filter(code => 
          cweUncertainRules.value.some(r => r.rule_code === code)
        )
        
        console.log('[DEBUG] 已加载CWE默认配置:', validCweRules.length, '个规则')
      } else {
        // 没有默认配置，全选所有CWE规则
        selectedCweAccurateRules.value = cweAccurateRules.value.map(rule => rule.rule_code)
        selectedCweUncertainRules.value = cweUncertainRules.value.map(rule => rule.rule_code)
      }
    } catch (configError) {
      // 加载默认配置失败，全选所有CWE规则
      selectedCweAccurateRules.value = cweAccurateRules.value.map(rule => rule.rule_code)
      selectedCweUncertainRules.value = cweUncertainRules.value.map(rule => rule.rule_code)
    }

    cweRulesLoaded.value = true
    console.log(`✅ CWE规则加载成功: 确定${cweAccurateRules.value.length}条, 不确定${cweUncertainRules.value.length}条`)
  } catch (error) {
    ElMessage.error('加载CWE规则列表失败: ' + error.message)
  }
}

// 规则类型切换处理
const handleRuleTypeChange = (tabName) => {
  console.log('[DEBUG] 切换规则类型:', tabName)
  activeRuleType.value = tabName
  
  // 如果切换到CWE并且还未加载，则加载CWE规则
  if (tabName === 'cwe' && !cweRulesLoaded.value) {
    loadCWERules()
  }
}

// 文件选择处理
const handleExcelFileChange = (file) => {
  selectedExcelFile.value = file
  excelFileList.value = [file]
}

const handleCodebaseFileChange = (file) => {
  selectedCodebaseFile.value = file
  codebaseFileList.value = [file]
}

// 规则选择操作
const selectAllRules = () => {
  selectedRules.value = [
    ...accurateRules.value.map(rule => rule.rule_code),
    ...uncertainRules.value.map(rule => rule.rule_code)
  ]
}

const deselectAllRules = () => {
  selectedRules.value = []
}

const selectAccurateOnly = () => {
  selectedRules.value = accurateRules.value.map(rule => rule.rule_code)
}

const selectUncertainOnly = () => {
  selectedRules.value = uncertainRules.value.map(rule => rule.rule_code)
}

// CWE规则选择方法
const selectAllCweRules = () => {
  selectedCweAccurateRules.value = cweAccurateRules.value.map(rule => rule.rule_code)
  selectedCweUncertainRules.value = cweUncertainRules.value.map(rule => rule.rule_code)
}

const deselectAllCweRules = () => {
  selectedCweAccurateRules.value = []
  selectedCweUncertainRules.value = []
}

const selectCweAccurateOnly = () => {
  selectedCweAccurateRules.value = cweAccurateRules.value.map(rule => rule.rule_code)
  selectedCweUncertainRules.value = []
}

const selectCweUncertainOnly = () => {
  selectedCweAccurateRules.value = []
  selectedCweUncertainRules.value = cweUncertainRules.value.map(rule => rule.rule_code)
}

// 移动规则到不确定
const moveRuleToUncertain = (ruleType, ruleCode) => {
  if (!ruleOverrides.value[ruleType]) {
    ruleOverrides.value[ruleType] = {}
  }
  ruleOverrides.value[ruleType][ruleCode] = 'uncertain'
  
  ElMessage.success(`规则 ${ruleCode} 已标记为"不确定"，点击"保存为默认配置"以永久生效`)
}

// 移动规则到确定
const moveRuleToAccurate = (ruleType, ruleCode) => {
  if (!ruleOverrides.value[ruleType]) {
    ruleOverrides.value[ruleType] = {}
  }
  ruleOverrides.value[ruleType][ruleCode] = 'accurate'
  
  ElMessage.success(`规则 ${ruleCode} 已标记为"确定"，点击"保存为默认配置"以永久生效`)
}

// 判断规则是否被修改
const isRuleModified = (ruleType, ruleCode) => {
  return ruleOverrides.value[ruleType] && ruleOverrides.value[ruleType][ruleCode]
}

// 添加自定义过滤
const addCustomFilter = () => {
  customFilterList.value.push({
    ruleCode: '',
    keywords: ''
  })
}

// 删除自定义过滤
const removeCustomFilter = (index) => {
  customFilterList.value.splice(index, 1)
}

// 将customFilterList转换为对象格式
const getCustomFiltersObject = () => {
  const filters = {}
  customFilterList.value.forEach(filter => {
    if (filter.ruleCode && filter.keywords) {
      const keywords = filter.keywords.split(',').map(k => k.trim()).filter(k => k)
      if (keywords.length > 0) {
        filters[filter.ruleCode] = keywords
      }
    }
  })
  return filters
}

// 从对象格式加载到customFilterList
const loadCustomFilters = (customFilters) => {
  customFilterList.value = Object.entries(customFilters || {}).map(([ruleCode, keywords]) => ({
    ruleCode,
    keywords: Array.isArray(keywords) ? keywords.join(',') : keywords
  }))
}

// 显示保存配置对话框
const showSaveConfigDialog = () => {
  saveConfigDialogVisible.value = true
}

// 导出配置
const exportConfig = () => {
  try {
    // 构建配置对象
    const config = {
      gjb_rules: selectedRules.value,
      cwe_rules: [...selectedCweAccurateRules.value, ...selectedCweUncertainRules.value],
      rule_overrides: ruleOverrides.value,
      custom_filters: getCustomFiltersObject(),
      max_issues_per_rule: maxIssuesPerRule.value,
      version: "1.0",
      exported_at: new Date().toISOString(),
      exported_by: "静态分析过滤工具"
    }
    
    // 转换为JSON字符串
    const jsonStr = JSON.stringify(config, null, 2)
    
    // 创建Blob对象
    const blob = new Blob([jsonStr], { type: 'application/json' })
    
    // 创建下载链接
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 生成文件名（包含时间戳）
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
    link.download = `rules_config_${timestamp}.json`
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 释放URL对象
    URL.revokeObjectURL(url)
    
    ElMessage.success({
      message: `配置已导出：${link.download}`,
      duration: 3000
    })
    
  } catch (error) {
    ElMessage.error('导出配置失败: ' + error.message)
  }
}

// 显示导入配置对话框
const showImportConfigDialog = () => {
  importConfigForm.password = ''
  selectedConfigFile.value = null
  configFileList.value = []
  importPreview.value = null
  importConfigDialogVisible.value = true
}

// 处理配置文件选择
const handleConfigFileChange = (file) => {
  selectedConfigFile.value = file.raw
  configFileList.value = [file]
  
  // 读取文件内容并预览
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const config = JSON.parse(e.target.result)
      
      // 验证配置格式
      if (!config.gjb_rules || !config.cwe_rules) {
        throw new Error('配置文件格式不正确，缺少必要字段')
      }
      
      // 生成预览信息
      const gjbOverrides = config.rule_overrides?.gjb || {}
      const cweOverrides = config.rule_overrides?.cwe || {}
      const overrideCount = Object.keys(gjbOverrides).length + Object.keys(cweOverrides).length
      
      importPreview.value = {
        gjb_count: config.gjb_rules.length,
        cwe_count: config.cwe_rules.length,
        has_overrides: overrideCount > 0,
        override_count: overrideCount,
        max_issues_per_rule: config.max_issues_per_rule || 0,
        config: config
      }
      
    } catch (error) {
      ElMessage.error('解析配置文件失败: ' + error.message)
      selectedConfigFile.value = null
      configFileList.value = []
      importPreview.value = null
    }
  }
  reader.readAsText(file.raw)
}

// 确认导入配置
const confirmImportConfig = async () => {
  if (!importConfigForm.password) {
    ElMessage.error('请输入管理员密码')
    return
  }
  
  if (!importPreview.value) {
    ElMessage.error('请先选择配置文件')
    return
  }
  
  try {
    importingConfig.value = true
    
    const config = importPreview.value.config
    
    // 调用保存配置API
    const response = await staticAnalysisFilterService.saveDefaultRulesConfig(
      importConfigForm.password,
      config.gjb_rules,
      config.cwe_rules,
      config.rule_overrides || { gjb: {}, cwe: {} },
      config.custom_filters || {},
      config.max_issues_per_rule || 0
    )
    
    if (response.success) {
      ElMessage.success('配置导入成功！')
      importConfigDialogVisible.value = false
      
      // 应用导入的配置到前端
      selectedRules.value = config.gjb_rules.filter(code => {
        const allGjbRules = [
          ...accurateRules.value.map(r => r.rule_code),
          ...uncertainRules.value.map(r => r.rule_code)
        ]
        return allGjbRules.includes(code)
      })
      
      selectedCweAccurateRules.value = config.cwe_rules.filter(code => {
        return cweAccurateRules.value.some(r => r.rule_code === code)
      })
      
      selectedCweUncertainRules.value = config.cwe_rules.filter(code => {
        return cweUncertainRules.value.some(r => r.rule_code === code)
      })
      
      // 如果有规则覆盖，更新ruleOverrides
      if (config.rule_overrides) {
        ruleOverrides.value = config.rule_overrides
      }
      
      // 加载自定义过滤规则
      if (config.custom_filters) {
        loadCustomFilters(config.custom_filters)
      }
      
      // 加载问题数量限制配置
      maxIssuesPerRule.value = config.max_issues_per_rule || 0
      
      // 重新加载规则（因为可能有规则分类变更）
      await loadRules()
      await loadCWERules()
      
      // 清空规则覆盖（因为已经应用到数据库了）
      ruleOverrides.value = { gjb: {}, cwe: {} }
      
      ElMessage.success({
        message: `已导入 ${config.gjb_rules.length} 条GJB规则和 ${config.cwe_rules.length} 条CWE规则`,
        duration: 3000
      })
    }
  } catch (error) {
    if (error.response && error.response.status === 403) {
      ElMessage.error('管理员密码错误')
    } else {
      ElMessage.error('导入配置失败: ' + error.message)
    }
  } finally {
    importingConfig.value = false
  }
}

// 确认保存配置
const confirmSaveConfig = async () => {
  try {
    savingConfig.value = true

    // 收集所有选中的规则
    const gjbRules = selectedRules.value
    const cweRules = [...selectedCweAccurateRules.value, ...selectedCweUncertainRules.value]

    // 统计规则覆盖信息
    const gjbOverrideCount = Object.keys(ruleOverrides.value.gjb || {}).length
    const cweOverrideCount = Object.keys(ruleOverrides.value.cwe || {}).length
    const hasOverrides = gjbOverrideCount > 0 || cweOverrideCount > 0

    // 获取自定义过滤规则
    const customFilters = getCustomFiltersObject()

    const response = await staticAnalysisFilterService.saveDefaultRulesConfig(
      gjbRules,
      cweRules,
      ruleOverrides.value,
      customFilters,
      maxIssuesPerRule.value
    )

    if (response.success) {
      let message = '默认规则配置已保存！'
      if (hasOverrides) {
        message += `\n已将 ${gjbOverrideCount} 条GJB规则和 ${cweOverrideCount} 条CWE规则的分类永久更新到数据库`
      }
      ElMessage.success(message)
      saveConfigDialogVisible.value = false
      
      // 清空规则覆盖记录
      ruleOverrides.value = { gjb: {}, cwe: {} }
      
      // 重新加载规则（从数据库获取最新分类）
      await loadRules()
      await loadCWERules()
    }
  } catch (error) {
    if (error.response && error.response.status === 403) {
      ElMessage.error('管理员密码错误')
    } else {
      ElMessage.error('保存配置失败: ' + error.message)
    }
  } finally {
    savingConfig.value = false
  }
}

// 开始处理
const startProcessing = async () => {
  console.log('[DEBUG] startProcessing 被调用')
  
  // 检查是否已登录
  if (!authStore.isAuthenticated || !authStore.user) {
    ElMessage.warning('请先登录后再进行静态分析')
    router.push('/login')
    return
  }
  
  if (!canStartProcessing.value) {
    console.log('[DEBUG] 检查失败，缺少必需文件或规则')
    ElMessage.error('请确保已上传所有必需文件并选择至少一个规则')
    return
  }

  try {
    console.log('[DEBUG] 开始上传文件...')
    processing.value = true
    
    // 合并GJB和CWE规则
    const allSelectedRules = [
      ...selectedRules.value,  // GJB规则
      ...selectedCweAccurateRules.value,  // CWE确定规则
      ...selectedCweUncertainRules.value  // CWE不确定规则
    ]
    console.log('[DEBUG] 合并后的规则数:', allSelectedRules.length, '(GJB:', selectedRules.value.length, ', CWE:', selectedCweAccurateRules.value.length + selectedCweUncertainRules.value.length, ')')
    
    // 获取自定义过滤规则
    const customFilters = getCustomFiltersObject()
    console.log('[DEBUG] 自定义过滤规则:', customFilters)
    console.log('[DEBUG] 问题数量限制:', maxIssuesPerRule.value)
    
    console.log('[DEBUG] 等待上传响应...')
    const response = await staticAnalysisFilterService.uploadEnhancedFiles(
      selectedExcelFile.value.raw,
      selectedCodebaseFile.value?.raw,
      allSelectedRules,
      customFilters,
      maxIssuesPerRule.value
    )
    console.log('[DEBUG] 收到上传响应:', response)
    console.log('[DEBUG] 响应类型:', typeof response)
    console.log('[DEBUG] 响应keys:', response ? Object.keys(response) : 'null')
    
    if (!response) {
      console.error('[ERROR] 服务器无响应')
      throw new Error('服务器无响应')
    }
    
    console.log('[DEBUG] response.success:', response.success)
    console.log('[DEBUG] response.session_id:', response.session_id)
    
    if (response.success) {
      sessionId.value = response.session_id
      console.log('[DEBUG] 上传成功! sessionId:', sessionId.value)
      if (response.ai_disabled) {
        // 并发过高：关闭AI审查，仅提供"未经AI过滤"下载
        ElMessageBox.alert(
          '当前使用人数过多，无法进行AI审查，请下载未经AI过滤的问题单',
          '⚠️ 受模型并发限制',
          {
            confirmButtonText: '我知道了',
            type: 'warning',
            center: true,
            showClose: false,
            customClass: 'centered-message-box'
          }
        )
        
        // [FIX] 设置进度条为完成状态
        gjbProgress.progress = 100
        gjbProgress.status = 'completed'
        gjbProgress.aiProcessedIssues = gjbProgress.aiProcessingTotal
        cweProgress.progress = 100
        cweProgress.status = 'completed'
        cweProgress.aiProcessedIssues = cweProgress.aiProcessingTotal
        
        // 直接允许下载"未经AI过滤"的四个Sheet
        gjbProgress.accurate_ready = true
        cweProgress.accurate_ready = true
        
        // 标记为已完成，显示下载按钮
        processing.value = false
        completed.value = true
        
        // 不启动轮询，停在当前页，等待用户手动下载
        return
      } else {
        ElMessage.success('文件上传成功，正在智能过滤处理中...')
      }
      
      // 获取task_id并显示两个代码视图地址通知（CWE和GJB8114）
      try {
        // 等待一下让后台处理创建数据库记录
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        const taskIdResponse = await staticAnalysisFilterService.getTaskIdBySession(sessionId.value)
        if (taskIdResponse && taskIdResponse.success) {
          const taskId = taskIdResponse.task_id
          const gjbCodeViewUrl = `http://172.16.32.81:8085/static-analysis/code-view/${taskId}?type=gjb`
          const cweCodeViewUrl = `http://172.16.32.81:8085/static-analysis/code-view/${taskId}?type=cwe`
          
          // 显示GJB8114代码视图通知
          ElNotification({
            title: '✅ GJB8114代码视图已就绪',
            message: `
              <div style="margin-top: 12px;">
                <div style="background: #f0f9ff; padding: 12px; border-radius: 6px; border-left: 3px solid #409EFF; margin-bottom: 12px;">
                  <div style="color: #606266; font-size: 13px; margin-bottom: 6px;">📍 GJB8114代码视图地址：</div>
                  <div style="color: #303133; font-size: 14px; font-family: monospace; word-break: break-all;">${gjbCodeViewUrl}</div>
                  <div style="color: #718096; font-size: 12px; margin-top: 4px;">任务ID: ${taskId}</div>
                </div>
                <a href="${gjbCodeViewUrl}" target="_blank" 
                   style="display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; 
                          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; text-decoration: none; border-radius: 6px; 
                          font-weight: 500; font-size: 14px; transition: all 0.3s; 
                          box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);"
                   onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)';"
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(102, 126, 234, 0.3)';">
                  🔗 查看GJB8114代码视图
                </a>
              </div>
            `,
            dangerouslyUseHTMLString: true,
            type: 'success',
            duration: 0,  // 不自动关闭
            position: 'top-right',
            showClose: true,
            offset: 80
          })
          
          // 显示CWE代码视图通知
          ElNotification({
            title: '✅ CWE代码视图已就绪',
            message: `
              <div style="margin-top: 12px;">
                <div style="background: #fff7e6; padding: 12px; border-radius: 6px; border-left: 3px solid #E6A23C; margin-bottom: 12px;">
                  <div style="color: #606266; font-size: 13px; margin-bottom: 6px;">📍 CWE代码视图地址：</div>
                  <div style="color: #303133; font-size: 14px; font-family: monospace; word-break: break-all;">${cweCodeViewUrl}</div>
                  <div style="color: #718096; font-size: 12px; margin-top: 4px;">任务ID: ${taskId}</div>
                </div>
                <a href="${cweCodeViewUrl}" target="_blank" 
                   style="display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; 
                          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                          color: white; text-decoration: none; border-radius: 6px; 
                          font-weight: 500; font-size: 14px; transition: all 0.3s; 
                          box-shadow: 0 2px 8px rgba(245, 87, 108, 0.3);"
                   onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(245, 87, 108, 0.4)';"
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(245, 87, 108, 0.3)';">
                  🔗 查看CWE代码视图
                </a>
              </div>
            `,
            dangerouslyUseHTMLString: true,
            type: 'warning',
            duration: 0,  // 不自动关闭
            position: 'top-right',
            showClose: true,
            offset: 380  // 第二个通知偏移更多，避免重叠
          })
          
          // 下载包含两个代码视图地址的txt文件
          const txtContent = `C/C++ 静态分析代码视图地址
===========================================

任务ID: ${taskId}
生成时间: ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}

GJB8114 代码视图:
${gjbCodeViewUrl}

CWE 代码视图:
${cweCodeViewUrl}

===========================================
说明: 请使用浏览器打开以上链接查看静态分析结果
`
          const blob = new Blob([txtContent], { type: 'text/plain;charset=utf-8' })
          const url = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = `代码视图地址_${taskId}_${new Date().getTime()}.txt`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          window.URL.revokeObjectURL(url)
          
          ElMessage.success('代码视图地址已下载到txt文件')
        } else {
          // 如果获取task_id失败，使用session_id作为后备
          const gjbCodeViewUrl = `http://172.16.32.81:8085/static-analysis/code-view/${sessionId.value}?type=gjb`
          const cweCodeViewUrl = `http://172.16.32.81:8085/static-analysis/code-view/${sessionId.value}?type=cwe`
          
          ElNotification({
            title: '✅ 代码视图已就绪',
            message: `
              <div style="margin-top: 8px;">
                <p>GJB8114: <a href="${gjbCodeViewUrl}" target="_blank" style="color: #409EFF;">${gjbCodeViewUrl}</a></p>
                <p>CWE: <a href="${cweCodeViewUrl}" target="_blank" style="color: #E6A23C;">${cweCodeViewUrl}</a></p>
              </div>
            `,
            dangerouslyUseHTMLString: true,
            type: 'success',
            duration: 0,
            position: 'top-right',
            showClose: true,
            offset: 80
          })
        }
      } catch (error) {
        console.error('[DEBUG] 获取task_id失败:', error)
        // 使用session_id作为后备
        const gjbCodeViewUrl = `http://172.16.32.81:8085/static-analysis/code-view/${sessionId.value}?type=gjb`
        const cweCodeViewUrl = `http://172.16.32.81:8085/static-analysis/code-view/${sessionId.value}?type=cwe`
        ElNotification({
          title: '✅ 智能过滤任务已启动',
          message: `GJB: ${gjbCodeViewUrl}<br>CWE: ${cweCodeViewUrl}`,
          dangerouslyUseHTMLString: true,
          type: 'success',
          duration: 8000,
          position: 'top-right'
        })
      }
      
      // 立即检查一次状态
      try {
        console.log('[DEBUG] 立即检查一次状态 (status-enhanced)... sessionId =', sessionId.value)
        const statusResponse = await staticAnalysisFilterService.getEnhancedSessionStatus(sessionId.value)
        console.log('[DEBUG] 初始状态响应 (status-enhanced):', statusResponse)
        if (statusResponse && statusResponse.data) {
          console.log('[DEBUG] 初始状态响应.data:', statusResponse.data)
        }
        
        // 注意：后端 status-enhanced 目前不带 success 字段，这里仅做调试用
        if (statusResponse && (statusResponse.success || (statusResponse.gjb && statusResponse.cwe))) {
          console.log('[DEBUG] 初始状态包含 GJB/CWE 字段，尝试更新进度')
          updateProgressData(statusResponse)
          
          if (statusResponse.status === 'completed') {
            console.log('[DEBUG] 任务已完成，跳过轮询')
            processing.value = false
            completed.value = true
            ElMessage.success('智能过滤处理完成！')
            return
          }
        }
      } catch (error) {
        console.log('[DEBUG] 初始状态检查失败:', error)
        // 初始状态检查失败，继续轮询
      }
      
      // 开始轮询状态
      console.log('[DEBUG] 准备启动状态轮询, sessionId:', sessionId.value)
      startStatusPolling()
      console.log('[DEBUG] 状态轮询已启动')
    } else {
      throw new Error(response.error || response.message || '上传失败')
    }
  } catch (error) {
    console.error('[ERROR] 上传过程发生错误:', error)
    console.error('[ERROR] 错误类型:', error.constructor.name)
    console.error('[ERROR] 错误消息:', error.message)
    console.error('[ERROR] 错误堆栈:', error.stack)
    if (error.response) {
      console.error('[ERROR] HTTP响应状态:', error.response.status)
      console.error('[ERROR] HTTP响应数据:', error.response.data)
    }
    
    let errorMessage = '上传失败'
    if (error.message) {
      errorMessage += ': ' + error.message
    }
    if (error.response?.data?.detail) {
      errorMessage += ' - ' + error.response.data.detail
    }
    ElMessage.error(errorMessage)
    processing.value = false
  }
}

// 更新进度数据
const updateProgressData = (statusData) => {
  console.log('[DEBUG] updateProgressData 被调用, 原始数据:', statusData)
  totalIssues.value = statusData.total_issues || 0
  processedIssues.value = statusData.processed_issues || 0
  filteredIssues.value = statusData.filtered_issues || 0
  aiAnalyzedIssues.value = statusData.ai_analyzed_issues || 0
  accurateIssues.value = statusData.accurate_issues || 0
  uncertainIssues.value = statusData.uncertain_issues || 0
  currentStatus.value = statusData.status || 'pending'

  // 判断是否显示第一阶段下载按钮
  if (currentStatus.value === 'ai_analyzing' || 
      (currentStatus.value === 'completed')) {
    showFirstDownload.value = true
  }
}

// 开始状态轮询
const startStatusPolling = () => {
  console.log('[DEBUG] startStatusPolling 被调用')
  console.log('[DEBUG] totalIssues:', totalIssues.value)
  
  checkStatus()
  
  // 根据问题数量调整轮询间隔
  let pollIntervalTime = 5000 // 默认5秒
  if (totalIssues.value > 3000) {
    pollIntervalTime = 10000 // 大于3000个问题时，改为10秒轮询
  } else if (totalIssues.value > 1000) {
    pollIntervalTime = 8000 // 大于1000个问题时，改为8秒轮询
  }
  
  console.log('[DEBUG] 轮询间隔:', pollIntervalTime, 'ms')
  
  pollInterval = setInterval(() => {
    console.log('[DEBUG] 轮询回调触发 - processing:', processing.value, 'completed:', completed.value)
    if (completed.value || !processing.value) {
      clearInterval(pollInterval)
      pollInterval = null
      return
    }
    checkStatus()
  }, pollIntervalTime)
  
  console.log('[DEBUG] setInterval 已设置, pollInterval:', pollInterval)
}

// 检查状态（使用详细状态API）
const checkStatus = async () => {
  console.log('[DEBUG] checkStatus 被调用, sessionId:', sessionId.value)
  if (!sessionId.value) {
    console.log('[DEBUG] sessionId 为空，跳过检查')
    return
  }

  try {
    console.log('[DEBUG] 开始请求详细状态 (status/{session}/detailed):', sessionId.value)
    const reqPath = `/staticAnalysis/filter/status/${sessionId.value}/detailed`
    const tsStart = new Date().toISOString()
    console.log('[DEBUG] 请求信息:', { tsStart, sessionId: sessionId.value, reqPath })
    const response = await staticAnalysisFilterService.getDetailedStatus(sessionId.value)
    console.log('[DEBUG] 详细状态响应 (getDetailedStatus 返回值):', response)
    if (response && response.data) {
      console.log('[DEBUG] 详细状态响应.data:', response.data)
    }
    
    if (!response || (!response.success && !response.data?.success)) {
      console.warn('[DEBUG] 详细状态响应不包含 success=true，跳过本次更新')
      return
    }
    const payload = response.success ? response : response.data
    const tsEnd = new Date().toISOString()
    console.log('[DEBUG] 详细状态payload简要:', {
      tsEnd,
      gjb: payload?.gjb ? {
        total_issues: payload.gjb.total_issues,
        accurate_issues: payload.gjb.accurate_issues,
        uncertain_issues: payload.gjb.uncertain_issues,
        ai_processing_total: payload.gjb.ai_processing_total,
        ai_processed_issues: payload.gjb.ai_processed_issues,
        progress: payload.gjb.progress,
        status: payload.gjb.status,
        accurate_ready: payload.gjb.accurate_ready,
      } : null,
      cwe: payload?.cwe ? {
        total_issues: payload.cwe.total_issues,
        accurate_issues: payload.cwe.accurate_issues,
        uncertain_issues: payload.cwe.uncertain_issues,
        ai_processing_total: payload.cwe.ai_processing_total,
        ai_processed_issues: payload.cwe.ai_processed_issues,
        progress: payload.cwe.progress,
        status: payload.cwe.status,
        accurate_ready: payload.cwe.accurate_ready,
      } : null,
    })
    
    // 更新GJB进度
    if (payload.gjb) {
      gjbProgress.totalIssues = payload.gjb.total_issues || 0
      gjbProgress.accurateIssues = payload.gjb.accurate_issues || 0
      gjbProgress.uncertainIssues = payload.gjb.uncertain_issues || 0
      gjbProgress.filteredIssues = payload.gjb.filtered_issues || 0
      gjbProgress.retainedIssues = payload.gjb.retained_issues || 0
      gjbProgress.aiProcessingTotal = payload.gjb.ai_processing_total || 0
      gjbProgress.aiProcessedIssues = payload.gjb.ai_processed_issues || 0
      gjbProgress.processedIssues = payload.gjb.ai_processed_issues || 0
      gjbProgress.currentAnalyzingIssue = payload.gjb.current_analyzing_issue || ''
      gjbProgress.toolCallsCount = payload.gjb.tool_calls_count || 0
      gjbProgress.progress = payload.gjb.progress || 0
      gjbProgress.status = payload.gjb.status || 'pending'
      gjbProgress.accurate_ready = payload.gjb.accurate_ready || false  // 新增：更新确定规则就绪状态
      
      console.log('[DEBUG] GJB状态更新:', {
        status: gjbProgress.status,
        progress: gjbProgress.progress,
        aiProcessed: gjbProgress.aiProcessedIssues,
        aiTotal: gjbProgress.aiProcessingTotal,
        accurate_ready: gjbProgress.accurate_ready
      })
      try { console.log('[DEBUG] GJB前端对象:', JSON.parse(JSON.stringify(gjbProgress))) } catch (_) {}
    }
    
    // 更新CWE进度
    if (payload.cwe) {
      cweProgress.totalIssues = payload.cwe.total_issues || 0
      cweProgress.accurateIssues = payload.cwe.accurate_issues || 0
      cweProgress.uncertainIssues = payload.cwe.uncertain_issues || 0
      cweProgress.filteredIssues = payload.cwe.filtered_issues || 0
      cweProgress.retainedIssues = payload.cwe.retained_issues || 0
      cweProgress.aiProcessingTotal = payload.cwe.ai_processing_total || 0
      cweProgress.aiProcessedIssues = payload.cwe.ai_processed_issues || 0
      cweProgress.processedIssues = payload.cwe.ai_processed_issues || 0
      cweProgress.currentAnalyzingIssue = payload.cwe.current_analyzing_issue || ''
      cweProgress.toolCallsCount = payload.cwe.tool_calls_count || 0
      cweProgress.progress = payload.cwe.progress || 0
      cweProgress.status = payload.cwe.status || 'pending'
      cweProgress.accurate_ready = payload.cwe.accurate_ready || false  // 新增：更新确定规则就绪状态
      
      console.log('[DEBUG] CWE状态更新:', {
        status: cweProgress.status,
        progress: cweProgress.progress,
        aiProcessed: cweProgress.aiProcessedIssues,
        aiTotal: cweProgress.aiProcessingTotal,
        accurate_ready: cweProgress.accurate_ready
      })
      try { console.log('[DEBUG] CWE前端对象:', JSON.parse(JSON.stringify(cweProgress))) } catch (_) {}
    }
    
    // 判断是否都完成
    console.log('[DEBUG] 检查完成状态:', {
      gjbStatus: gjbProgress.status,
      cweStatus: cweProgress.status,
      bothCompleted: gjbProgress.status === 'completed' && cweProgress.status === 'completed'
    })
    
    if (gjbProgress.status === 'completed' && cweProgress.status === 'completed') {
      console.log('[DEBUG] ✅ 两个任务都已完成，停止轮询')
      processing.value = false
      completed.value = true
      
      if (pollInterval) {
        clearInterval(pollInterval)
        pollInterval = null
      }
      
      ElMessage.success('智能过滤处理完成！')
    }
  } catch (error) {
    console.error('[ERROR] 获取详细状态失败:', error)
    // 单次查询失败不停止轮询
  }
}

// 进度相关方法
const getProgressTitle = () => {
  switch (currentStatus.value) {
    case 'processing':
      return '🔍 正在分析确定规则的问题...'
    case 'ai_analyzing':
      return '🤖 AI正在深度分析不确定规则的问题...'
    case 'completed':
      return '✅ 智能过滤处理完成！'
    default:
      return '⚡ 正在处理中...'
  }
}

const getStatusText = (status) => {
  // 如果没传status，使用currentStatus
  const statusToCheck = status || currentStatus.value
  switch (statusToCheck) {
    case 'processing':
      return 'AI分析中'
    case 'completed':
      return '已完成'
    case 'pending':
      return '等待中'
    case 'error':
      return '错误'
    default:
      return '处理中'
  }
}

const getProgressStatusByState = (status) => {
  if (status === 'completed') {
    return 'success'
  } else if (status === 'error') {
    return 'exception'
  }
  return undefined
}

const getStatusTagType = (status) => {
  // 如果没传status，使用currentStatus
  const statusToCheck = status || currentStatus.value
  switch (statusToCheck) {
    case 'processing':
      return 'primary'
    case 'ai_analyzing':
      return 'warning'
    case 'completed':
      return 'success'
    case 'error':
      return 'danger'
    default:
      return 'info'
  }
}

const getProgressStatus = () => {
  if (currentStatus.value === 'completed') {
    return 'success'
  } else {
    return 'active'
  }
}

const getPhaseClass = (phase) => {
  if (phase === 'processing') {
    if (currentStatus.value === 'processing') return 'active'
    if (currentStatus.value === 'ai_analyzing' || currentStatus.value === 'completed') return 'completed'
    return 'pending'
  } else if (phase === 'ai_analyzing') {
    if (currentStatus.value === 'ai_analyzing') return 'active'
    if (currentStatus.value === 'completed') return 'completed'
    return 'pending'
  }
  return 'pending'
}

// 下载第一阶段结果（确定规则问题单）
const downloadFirstResult = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    downloadingFirst.value = true
    
    // 先确保文件已生成
    const generateResponse = await staticAnalysisFilterService.generateOutputFile(sessionId.value)
    
    if (!generateResponse.success) {
      throw new Error(generateResponse.error || '生成文件失败')
    }
    
    // 下载文件
    const downloadUrl = staticAnalysisFilterService.getDownloadUrl(sessionId.value, generateResponse.filename)
    
    // 创建下载链接
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `确定规则问题单_${generateResponse.filename}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('确定规则问题单下载成功')
    
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingFirst.value = false
  }
}

// 下载最终结果（完整问题单）
const downloadFinalResult = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    downloadingFinal.value = true
    
    // 先确保文件已生成
    const generateResponse = await staticAnalysisFilterService.generateOutputFile(sessionId.value)
    
    if (!generateResponse.success) {
      throw new Error(generateResponse.error || '生成文件失败')
    }
    
    // 下载文件
    const downloadUrl = staticAnalysisFilterService.getDownloadUrl(sessionId.value, generateResponse.filename)
    
    // 创建下载链接
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `智能过滤问题单_${generateResponse.filename}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('完整问题单下载成功')
    
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingFinal.value = false
  }
}

// 下载GJB确定规则问题单
const downloadGjbAccurate = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    downloadingGjbAccurate.value = true
    
    console.log('[DEBUG] 开始下载GJB确定规则问题单, sessionId:', sessionId.value)
    
    // 先确保文件已生成（只生成GJB的确定规则）
    const generateResponse = await staticAnalysisFilterService.generateOutputFile(sessionId.value, 'gjb', 'accurate', includeGjbUnselected.value)
    
    console.log('[DEBUG] 生成文件响应:', generateResponse)
    
    if (!generateResponse.success) {
      throw new Error(generateResponse.error || '生成文件失败')
    }
    
    // 下载文件
    const downloadUrl = staticAnalysisFilterService.getDownloadUrl(sessionId.value, generateResponse.filename)
    
    console.log('[DEBUG] 下载URL:', downloadUrl)
    
    // 创建下载链接
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `GJB确定规则问题单_${generateResponse.filename}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('GJB确定规则问题单下载成功（当前包含所有GJB保留问题）')
    
  } catch (error) {
    console.error('[ERROR] 下载GJB确定规则问题单失败:', error)
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingGjbAccurate.value = false
  }
}

// 下载GJB完整问题单
const downloadGjbFull = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    downloadingGjbFull.value = true

    await downloadWithGeneratingHint({
      ruleType: 'gjb',
      contentType: 'all',
      includeUnselected: false,
      split: true,
      highlightAi: true,
      downloadPrefix: 'GJB完整问题单',
      successMessage: 'GJB完整问题单下载成功（四个Sheet，含AI确认高亮）'
    })
    
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingGjbFull.value = false
  }
}

// 下载GJB不确定规则问题单（未经AI过滤）
const downloadGjbUncertainRaw = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    downloadingGjbUncertainRaw.value = true
    console.log('[DEBUG] 开始下载GJB不确定规则问题单（未经AI过滤）', {
      sessionId: sessionId.value,
      ruleType: 'gjb',
      contentType: 'uncertain',
      includeUnselected: true
    })
    // 生成只包含不确定规则、且不受勾选与过滤限制的清单
    const generateResponse = await staticAnalysisFilterService.generateOutputFile(sessionId.value, 'gjb', 'uncertain', true)
    console.log('[DEBUG] GJB不确定（未经AI过滤）生成响应:', generateResponse)
    if (!generateResponse.success) {
      throw new Error(generateResponse.error || '生成文件失败')
    }
    const downloadUrl = staticAnalysisFilterService.getDownloadUrl(sessionId.value, generateResponse.filename)
    console.log('[DEBUG] GJB不确定（未经AI过滤）下载URL:', downloadUrl)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `GJB不确定规则问题单_${generateResponse.filename}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    ElMessage.success('GJB不确定规则问题单下载成功（未经AI过滤）')
  } catch (error) {
    console.error('[ERROR] 下载GJB不确定规则问题单（未经AI过滤）失败:', error)
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingGjbUncertainRaw.value = false
    console.log('[DEBUG] 结束下载GJB不确定规则问题单（未经AI过滤）')
  }
}

// 下载CWE确定规则问题单
const downloadCweAccurate = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    downloadingCweAccurate.value = true
    
    // 先确保文件已生成（只生成CWE的确定规则）
    const generateResponse = await staticAnalysisFilterService.generateOutputFile(sessionId.value, 'cwe', 'accurate', includeCweUnselected.value)
    
    if (!generateResponse.success) {
      throw new Error(generateResponse.error || '生成文件失败')
    }
    
    // 下载文件
    const downloadUrl = staticAnalysisFilterService.getDownloadUrl(sessionId.value, generateResponse.filename)
    
    // 创建下载链接
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `CWE确定规则问题单_${generateResponse.filename}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('CWE确定规则问题单下载成功')
    
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingCweAccurate.value = false
  }
}

// 下载CWE完整问题单
const downloadCweFull = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    downloadingCweFull.value = true

    await downloadWithGeneratingHint({
      ruleType: 'cwe',
      contentType: 'all',
      includeUnselected: false,
      split: true,
      highlightAi: true,
      downloadPrefix: 'CWE完整问题单',
      successMessage: 'CWE完整问题单下载成功（四个Sheet，含AI确认高亮）'
    })
    
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingCweFull.value = false
  }
}

// 下载CWE不确定规则问题单（未经AI过滤）
const downloadCweUncertainRaw = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    downloadingCweUncertainRaw.value = true
    console.log('[DEBUG] 开始下载CWE不确定规则问题单（未经AI过滤）', {
      sessionId: sessionId.value,
      ruleType: 'cwe',
      contentType: 'uncertain',
      includeUnselected: true
    })
    // 生成只包含不确定规则、且不受勾选与过滤限制的清单
    const generateResponse = await staticAnalysisFilterService.generateOutputFile(sessionId.value, 'cwe', 'uncertain', true)
    console.log('[DEBUG] CWE不确定（未经AI过滤）生成响应:', generateResponse)
    if (!generateResponse.success) {
      throw new Error(generateResponse.error || '生成文件失败')
    }
    const downloadUrl = staticAnalysisFilterService.getDownloadUrl(sessionId.value, generateResponse.filename)
    console.log('[DEBUG] CWE不确定（未经AI过滤）下载URL:', downloadUrl)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `CWE不确定规则问题单_${generateResponse.filename}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    ElMessage.success('CWE不确定规则问题单下载成功（未经AI过滤）')
  } catch (error) {
    console.error('[ERROR] 下载CWE不确定规则问题单（未经AI过滤）失败:', error)
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingCweUncertainRaw.value = false
    console.log('[DEBUG] 结束下载CWE不确定规则问题单（未经AI过滤）')
  }
}

// 打开代码视图（使用 task_id 而非 session_id）
const openCodeView = async (ruleType) => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    const resp = await staticAnalysisFilterService.getTaskIdBySession(sessionId.value)
    if (resp && resp.success && resp.task_id) {
      window.open(`/static-analysis/code-view/${resp.task_id}?type=${ruleType}`, '_blank')
    } else {
      ElMessage.error('未获取到任务ID，稍后重试')
    }
  } catch (e) {
    ElMessage.error('打开失败: ' + (e?.message || e))
  }
}

// 重置表单
const resetForm = () => {
  selectedExcelFile.value = null
  selectedCodebaseFile.value = null
  excelFileList.value = []
  codebaseFileList.value = []
  sessionId.value = ''
  processing.value = false
  completed.value = false
  downloadingFirst.value = false
  downloadingFinal.value = false
  showFirstDownload.value = false
  
  totalIssues.value = 0
  processedIssues.value = 0
  filteredIssues.value = 0
  aiAnalyzedIssues.value = 0
  accurateIssues.value = 0
  uncertainIssues.value = 0
  currentStatus.value = 'pending'
  
  // 重新选择所有规则
  selectedRules.value = [
    ...accurateRules.value.map(rule => rule.rule_code),
    ...uncertainRules.value.map(rule => rule.rule_code)
  ]
  
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
  
  // 清空上传组件
  if (excelUploadRef.value) {
    excelUploadRef.value.clearFiles()
  }
  if (codebaseUploadRef.value) {
    codebaseUploadRef.value.clearFiles()
  }
}

// 组件卸载时清理
onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
})
</script>

<style scoped>
.static-analysis-filter {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  background: #f8fafc;
  min-height: 100vh;
}

/* 头部样式 */
.header {
  text-align: center;
  /* 统一与下方内容的左右边界，对齐为同一内宽 */
  width: 100%;
  max-width: 1320px; /* 内容内宽：确保与下方模块保持完全一致 */
  margin: 0 auto 40px auto;
  padding: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.header h2 {
  margin: 0 0 10px 0;
  font-size: 28px;
  font-weight: bold;
}

.description {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

/* 主要内容区域 */
.main-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
  /* 与头部保持相同的内宽，左右边界严格对齐 */
  width: 100%;
  max-width: 1320px;
  margin: 0 auto;
}

/* 文件上传容器 */
.upload-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.upload-item {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: none;
  transition: all 0.3s ease;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}

.upload-item:hover {
  box-shadow: 0 8px 30px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.upload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.upload-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.upload-dragger.compact {
  width: 100%;
}

.upload-dragger.compact :deep(.el-upload-dragger) {
  height: 140px; /* 增加高度让组件更饱满 */
  border-radius: 8px;
  border: 2px dashed #d9d9d9;
  background: #fafafa;
  transition: all 0.3s ease;
}

.upload-dragger.compact :deep(.el-icon--upload) {
  font-size: 32px;
  margin-bottom: 8px;
}

.upload-dragger.compact :deep(.el-upload__text) {
  font-size: 14px;
}

.upload-dragger.compact :deep(.el-upload__tip) {
  font-size: 12px;
  margin-top: 8px;
}

/* 规则选择区域 */
.rules-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.rules-header {
  margin-bottom: 20px;
}

.rules-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.rules-title h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.selected-count {
  font-size: 14px;
  color: #409eff;
  font-weight: bold;
}

.rules-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.rules-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.rules-column {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}

.column-header {
  padding: 15px 20px;
  color: white;
  font-weight: bold;
}

.accurate-column .column-header {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.uncertain-column .column-header {
  background: linear-gradient(135deg, #e6a23c, #f0a020);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.header-content h4 {
  margin: 0;
  font-size: 16px;
}

.rule-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.header-desc {
  margin: 0;
  font-size: 12px;
  opacity: 0.9;
}

.rules-list {
  max-height: 350px;
  overflow-y: auto;
  padding: 15px;
  background: white;
}

.rule-item {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafafa;
  transition: all 0.3s;
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
}

.rule-item:hover {
  border-color: #409eff;
  background: #f0f9ff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

/* 被修改的规则高亮 */
.rule-item.rule-modified {
  border: 2px solid #f56c6c;
  background: #fff5f5;
}

.rule-item.rule-modified::before {
  content: '●';
  color: #f56c6c;
  position: absolute;
  left: -10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.rule-checkbox {
  flex: 1;
}

.rule-content {
  margin-left: 24px;
}

/* 移动规则按钮 */
.move-rule-btn {
  flex-shrink: 0;
  margin-left: auto;
  min-width: 100px;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.3s;
}

.rule-item:hover .move-rule-btn {
  opacity: 1;
}

.rule-item.rule-modified .move-rule-btn {
  opacity: 1;
}

.rule-name {
  font-weight: bold;
  color: #303133;
  margin-bottom: 6px;
  font-size: 13px;
  line-height: 1.4;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
}

.rule-description {
  color: #606266;
  font-size: 12px;
  margin-bottom: 8px;
  line-height: 1.4;
}

.rule-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* 开始处理区域 */
.start-processing {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.processing-info {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.start-btn {
  font-size: 16px;
  padding: 12px 30px;
  border-radius: 8px;
}

/* 双进度区域样式 */
.dual-progress-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1320px;
  margin: 0 auto;
}

.progress-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.progress-card:hover {
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.12);
}

.gjb-progress-card {
  border-left: 4px solid #409EFF;
}

.cwe-progress-card {
  border-left: 4px solid #67C23A;
}

.card-header-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  color: white;
}

.gjb-banner {
  background: linear-gradient(135deg, #409EFF 0%, #3a8ee6 100%);
}

.cwe-banner {
  background: linear-gradient(135deg, #67C23A 0%, #5daf34 100%);
}

.card-header-banner h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.card-content {
  padding: 25px 30px;
}

.stat-grid-compact {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-top: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-item .stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-item .stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.gjb-analysis {
  background: linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%);
  border-left: 3px solid #409EFF;
}

.cwe-analysis {
  background: linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%);
  border-left: 3px solid #67C23A;
}

/* 旧的进度区域样式（保留向后兼容） */
.progress-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.progress-header h3 {
  margin: 0;
  color: #303133;
  font-size: 20px;
}

.main-progress {
  margin-bottom: 30px;
}

.main-progress :deep(.el-progress-bar__outer) {
  border-radius: 8px;
}

.main-progress :deep(.el-progress-bar__inner) {
  border-radius: 8px;
}

.progress-text {
  font-size: 14px;
  font-weight: bold;
}

.current-analysis-info {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.analysis-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
}

.analysis-icon {
  font-size: 24px;
}

.analysis-title {
  flex: 1;
}

.analysis-progress {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
}

.analysis-content {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px 16px;
}

.issue-name {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 8px;
  line-height: 1.5;
}

.tool-calls {
  font-size: 13px;
  opacity: 0.9;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  background: #fafafa;
}

.stat-card.primary { border-left: 4px solid #409eff; }
.stat-card.success { border-left: 4px solid #67c23a; }
.stat-card.warning { border-left: 4px solid #e6a23c; }
.stat-card.info { border-left: 4px solid #909399; }
.stat-card.danger { border-left: 4px solid #f56c6c; }
.stat-card.purple { border-left: 4px solid #9c27b0; }

.stat-icon {
  font-size: 20px;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: #606266;
  margin-top: 2px;
}

/* 阶段指示器 */
/* 后台整理提示 */
.preparing-hint {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin: 18px 0 22px;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid rgba(64, 158, 255, 0.18);
  box-shadow: 0 8px 20px rgba(64, 158, 255, 0.08);
}

.preparing-hint-gjb {
  background: linear-gradient(135deg, rgba(230, 247, 255, 0.96) 0%, rgba(243, 249, 255, 0.98) 100%);
}

.preparing-hint-cwe {
  background: linear-gradient(135deg, rgba(246, 255, 237, 0.96) 0%, rgba(251, 255, 246, 0.98) 100%);
  border-color: rgba(103, 194, 58, 0.2);
  box-shadow: 0 8px 20px rgba(103, 194, 58, 0.08);
}

.preparing-hint-icon {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(64, 158, 255, 0.14);
  font-size: 18px;
}

.preparing-hint-cwe .preparing-hint-icon {
  background: rgba(103, 194, 58, 0.14);
}

.preparing-hint-content {
  min-width: 0;
}

.preparing-hint-title {
  margin-bottom: 6px;
  color: #1f2d3d;
  font-size: 15px;
  font-weight: 700;
}

.preparing-hint-text {
  color: #5c6b77;
  font-size: 13px;
  line-height: 1.7;
}

.phase-indicators {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 30px 0;
  gap: 20px;
}

.phase-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px 20px;
  border-radius: 8px;
  border: 2px solid #e4e7ed;
  background: #fafafa;
  transition: all 0.3s;
}

.phase-item.active {
  border-color: #409eff;
  background: #e6f7ff;
  color: #1890ff;
}

.phase-item.completed {
  border-color: #67c23a;
  background: #f6ffed;
  color: #52c41a;
}

.phase-item.pending {
  border-color: #d9d9d9;
  background: #f5f5f5;
  color: #8c8c8c;
}

.phase-icon {
  font-size: 18px;
}

.phase-title {
  font-weight: bold;
  font-size: 14px;
}

.phase-desc {
  font-size: 12px;
  opacity: 0.8;
}

.phase-divider {
  width: 30px;
  height: 2px;
  background: #e4e7ed;
  border-radius: 1px;
}

/* 后台整理提示 */
.preparing-hint {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin: 18px 0 22px;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid rgba(64, 158, 255, 0.18);
  box-shadow: 0 8px 20px rgba(64, 158, 255, 0.08);
}

.preparing-hint-gjb {
  background: linear-gradient(135deg, rgba(230, 247, 255, 0.96) 0%, rgba(243, 249, 255, 0.98) 100%);
}

.preparing-hint-cwe {
  background: linear-gradient(135deg, rgba(246, 255, 237, 0.96) 0%, rgba(251, 255, 246, 0.98) 100%);
  border-color: rgba(103, 194, 58, 0.2);
  box-shadow: 0 8px 20px rgba(103, 194, 58, 0.08);
}

.preparing-hint-icon {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(64, 158, 255, 0.14);
  font-size: 18px;
}

.preparing-hint-cwe .preparing-hint-icon {
  background: rgba(103, 194, 58, 0.14);
}

.preparing-hint-content {
  min-width: 0;
}

.preparing-hint-title {
  margin-bottom: 6px;
  color: #1f2d3d;
  font-size: 15px;
  font-weight: 700;
}

.preparing-hint-text {
  color: #5c6b77;
  font-size: 13px;
  line-height: 1.7;
}

/* 第一阶段下载 */
.first-download {
  text-align: center;
  margin-top: 25px;
}

.download-alert {
  margin-bottom: 15px;
}

.download-btn {
  font-size: 16px;
  padding: 12px 25px;
}

/* 结果区域样式 */
.result-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.success-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}

.success-icon {
  font-size: 48px;
  color: #67c23a;
}

.success-content h3 {
  margin: 0 0 8px 0;
  color: #67c23a;
  font-size: 24px;
}

.success-content p {
  margin: 0;
  color: #606266;
  font-size: 16px;
}

.result-summary {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin: 30px 0;
  flex-wrap: wrap;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.summary-item.highlight {
  padding: 15px 20px;
  background: linear-gradient(135deg, #f0f9ff, #e6f7ff);
  border-radius: 8px;
  border: 2px solid #409eff;
}

.summary-label {
  font-size: 14px;
  color: #606266;
}

.summary-item.highlight .summary-label {
  font-weight: bold;
  color: #409eff;
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
}

.summary-value.primary { color: #409eff; }
.summary-value.success { color: #67c23a; }
.summary-value.info { color: #409eff; }
.summary-value.warning { color: #e6a23c; }
.summary-value.purple { color: #9c27b0; }

/* 详细统计信息样式 */
.detailed-stats {
  margin-top: 20px;
  background: #f8fafc;
  border-radius: 8px;
  padding: 15px;
}

/* 下载按钮区域 */
.download-buttons {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  flex-wrap: nowrap; /* 不换行，保持同一行 */
  justify-content: center;
  overflow-x: auto;  /* 窄屏时允许横向滚动，避免掉行 */
  align-items: center; /* 垂直居中对齐 */
}

.download-btn-compact {
  flex: 0 0 auto;     /* 固定内容宽度，避免被压缩过小 */
  max-width: 220px;   /* 紧凑宽度 */
  font-size: 13px;    /* 略微缩小字号以容纳两行 */
  white-space: normal; /* 允许自动换行为两行 */
}

.download-btn-wide {
  flex: 0 0 auto;     /* 固定内容宽度，避免被压缩过小 */
  max-width: 300px;   /* 控制宽度，便于两行展示 */
  white-space: normal; /* 允许换行 */
}

/* 统一提高按钮高度，容纳两行文字 */
.download-btn-compact, .download-btn-wide {
  padding: 14px 22px; /* 增加上下内边距 */
  line-height: 1.3;   /* 两行更紧凑 */
  height: auto;       /* 自适应高度 */
}

/* 仅为CWE“不确定（未经AI过滤）”按钮略微加宽（约两个字符） */
.download-btn-wide-cwe { max-width: 320px; }

/* 左侧复选框微调下移，与按钮中心线对齐 */
.download-checkbox :deep(.el-checkbox__label) {
  display: inline-block;
  transform: translateY(2px);
}
.download-checkbox {
  padding-top: 2px; /* 细微下移 */
}

/* 完整问题单（AI过滤后）按钮宽度略短于“不确定（未经AI过滤）”按钮 */
.download-btn-full-wide-gjb { max-width: 292px; }
.download-btn-full-wide-cwe { max-width: 312px; }

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 12px;
}

.stats-row:last-child {
  margin-bottom: 0;
}

.stat-item-detail {
  background: white;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.stat-item-detail:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.stat-item-detail .stat-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
  text-align: center;
}

.stat-item-detail .stat-value {
  font-size: 22px;
  font-weight: bold;
  text-align: center;
}

.stat-item-detail .stat-value.primary { color: #409eff; }
.stat-item-detail .stat-value.primary-bold { color: #1890ff; font-size: 24px; }
.stat-item-detail .stat-value.success { color: #67c23a; }
.stat-item-detail .stat-value.info { color: #e6a23c; }
.stat-item-detail .stat-value.warning { color: #909399; }
.stat-item-detail .stat-value.danger { color: #f56c6c; }

.download-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin: 30px 0;
}

.download-card {
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
  background: #fafafa;
  transition: all 0.3s;
}

.download-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.download-card.featured {
  border-color: #409eff;
  background: linear-gradient(135deg, #f0f9ff, #e6f7ff);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
}

.card-icon.success { background: #67c23a; }
.card-icon.primary { background: #409eff; }

.card-title h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #303133;
}

.card-title p {
  margin: 0;
  font-size: 12px;
  color: #606266;
}

.card-btn {
  width: 100%;
  font-size: 14px;
}

.restart-section {
  margin-top: 30px;
}

.restart-section-bottom {
  margin-top: 30px;
  text-align: center;
  padding: 20px;
}

/* 配置对话框样式 */
.config-summary {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin: 10px 0;
}

.config-summary p {
  margin: 5px 0;
  color: #606266;
}

.config-summary strong {
  color: #303133;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .upload-container {
    grid-template-columns: 1fr;
  }
  
  .rules-container {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .static-analysis-filter {
    padding: 15px;
  }
  
  .header {
    padding: 20px;
  }
  
  .header h2 {
    font-size: 22px;
  }
  
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .phase-indicators {
    flex-direction: column;
    gap: 15px;
  }
  
  .phase-divider {
    width: 2px;
    height: 20px;
  }
  
  .processing-info {
    flex-direction: column;
    gap: 15px;
  }
  
  .result-summary {
    flex-direction: column;
    gap: 20px;
  }
  
  .download-cards {
    grid-template-columns: 1fr;
  }
}

/* 配置对话框样式 */
.config-summary {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 6px;
  font-size: 14px;
}

.config-summary p {
  margin: 8px 0;
}

.dialog-footer-with-extra {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.extra-actions {
  display: flex;
  gap: 8px;
}

.main-actions {
  display: flex;
  gap: 10px;
}

/* 导入预览样式 */
.import-preview {
  background: #f0f9ff;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #d9ecff;
}

.import-preview p {
  margin: 6px 0;
  font-size: 14px;
}

/* 自定义过滤配置样式 */
.filter-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.el-collapse {
  border: none;
}

.el-collapse-item {
  border-bottom: 1px solid #ebeef5;
}
</style>

<style>
/* 全局样式：让MessageBox弹窗居中显示（稍微向右偏移） */
.el-message-box__wrapper .centered-message-box {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.centered-message-box.el-message-box {
  position: relative !important;
  top: auto !important;
  left: auto !important;
  transform: translateX(50px) !important;
  margin: 0 auto !important;
}
</style>