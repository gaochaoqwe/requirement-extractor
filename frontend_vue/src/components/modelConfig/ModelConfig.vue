<template>
  <div class="model-config-container">
    <h2>模型配置</h2>
    
    <div v-if="loading" class="loading-spinner">
      <div class="spinner"></div>
      <p>加载配置中...</p>
    </div>
    
    <div v-else class="config-form">
      <div class="form-section">
        <h3>模型提供商</h3>
        <div class="provider-selection">
          <label>
            <input type="radio" v-model="config.provider" value="openai" @change="updateProviderFields">
            OpenAI 兼容服务
          </label>
          <label>
            <input type="radio" v-model="config.provider" value="ollama" @change="updateProviderFields">
            Ollama 本地服务
          </label>
        </div>
      </div>
      
      <!-- OpenAI 配置部分 -->
      <div v-if="config.provider === 'openai'" class="form-section">
        <h3>OpenAI 配置</h3>
        
        <div class="form-group">
          <label for="openai-api-key">API 密钥</label>
          <input 
            type="text" 
            id="openai-api-key" 
            v-model="config.openai.api_key" 
            placeholder="sk-..." 
            autocomplete="new-password"
            autocorrect="off"
            autocapitalize="off"
            spellcheck="false"
          />
        </div>
        
        <div class="form-group">
          <label for="openai-base-url">API 基础 URL</label>
          <input 
            type="text" 
            id="openai-base-url" 
            v-model="config.openai.base_url" 
            placeholder="https://api.openai.com/v1" 
          />
        </div>
        
        <div class="form-group">
          <label for="openai-model-name">模型名称</label>
          <input 
            type="text" 
            id="openai-model-name" 
            v-model="config.openai.model_name" 
            placeholder="例如：gpt-4o, gpt-4-turbo, glm-4, qwen-max 等"
          />
          <small class="form-hint">常用模型: gpt-4o, gpt-4-turbo, gpt-3.5-turbo, glm-4, qwen-max, ernie-bot-4</small>
        </div>
      </div>
      
      <!-- Ollama 配置部分 -->
      <div v-if="config.provider === 'ollama'" class="form-section">
        <h3>Ollama 配置</h3>
        
        <div class="form-group">
          <label for="ollama-base-url">服务地址</label>
          <input 
            type="text" 
            id="ollama-base-url" 
            v-model="config.ollama.base_url" 
            placeholder="http://localhost:11434" 
          />
        </div>
        
        <div class="form-group">
          <label for="ollama-model-name">模型名称</label>
          <input 
            type="text" 
            id="ollama-model-name" 
            v-model="config.ollama.model_name"
            placeholder="例如：llama3, mistral, mixtral 等"
          />
          <small class="form-hint">常用模型: llama3, llama3:8b, mistral, mixtral, gemma, qwen</small>
        </div>
      </div>
      
      <!-- 模型参数配置 -->
      <div class="form-section">
        <h3>模型参数</h3>
        
        <div class="form-group">
          <label for="temperature">Temperature</label>
          <div class="slider-container">
            <input 
              type="range" 
              id="temperature" 
              v-model.number="config.model_params.temperature" 
              min="0" 
              max="1" 
              step="0.1" 
            />
            <span>{{ config.model_params.temperature }}</span>
          </div>
        </div>
        
        <div class="form-group">
          <label for="max-tokens">最大令牌数</label>
          <input 
            type="number" 
            id="max-tokens" 
            v-model.number="config.model_params.max_tokens" 
            min="100" 
            max="8000" 
          />
        </div>
      </div>
      
      <div class="action-buttons">
        <button class="btn primary-btn" @click="saveConfig" :disabled="isSaving || isValidating">
          {{ isSaving ? '保存中...' : '保存配置' }}
        </button>
        <button class="btn validate-btn" @click="validateModel" :disabled="isSaving || isValidating">
          {{ isValidating ? '验证中...' : '验证模型' }}
        </button>
        <button class="btn secondary-btn" @click="resetConfig" :disabled="isSaving || isValidating">
          重置配置
        </button>
      </div>
      
      <div v-if="validationResult" :class="['validation-result', validationSuccess ? 'success' : 'error']">
        <h4>{{ validationSuccess ? '验证成功' : '验证失败' }}</h4>
        <p v-if="validationSuccess">模型响应: {{ validationResponse }}</p>
        <p v-else>错误信息: {{ validationError }}</p>
      </div>
      
      <div v-if="statusMessage" :class="['status-message', statusType]">
        {{ statusMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';

const API_BASE_URL = 'http://localhost:5002/api';
const defaultConfig = {
  provider: 'openai',
  openai: {
    api_key: '',
    base_url: 'https://api.openai.com/v1',
    model_name: 'gpt-4o'
  },
  ollama: {
    base_url: 'http://localhost:11434',
    model_name: 'llama3'
  },
  model_params: {
    temperature: 0.1,
    max_tokens: 2000
  }
};

// 状态变量
const config = reactive(JSON.parse(JSON.stringify(defaultConfig)));
const loading = ref(true);
const isSaving = ref(false);
const isValidating = ref(false);
const statusMessage = ref('');
const statusType = ref('');
const originalConfig = ref(null);

// 验证结果
const validationResult = ref(false);
const validationSuccess = ref(false);
const validationResponse = ref('');
const validationError = ref('');

// 生命周期钩子
onMounted(async () => {
  await fetchConfig();
});

// 获取当前配置
async function fetchConfig() {
  loading.value = true;
  try {
    const response = await fetch(`${API_BASE_URL}/model_config`);
    const data = await response.json();
    
    if (data.success && data.config) {
      // 复制配置到响应式对象
      Object.assign(config, data.config);
      // 保存原始配置用于重置
      originalConfig.value = JSON.parse(JSON.stringify(data.config));
    } else {
      showStatus('获取配置失败: ' + (data.error || '未知错误'), 'error');
    }
  } catch (error) {
    console.error('获取配置出错:', error);
    showStatus('获取配置时发生错误: ' + error.message, 'error');
  } finally {
    loading.value = false;
  }
}

// 保存配置
async function saveConfig() {
  isSaving.value = true;
  statusMessage.value = '';
  
  try {
    const response = await fetch(`${API_BASE_URL}/model_config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config)
    });
    
    const data = await response.json();
    
    if (data.success) {
      showStatus('配置保存成功', 'success');
      // 更新原始配置
      originalConfig.value = JSON.parse(JSON.stringify(config));
    } else {
      showStatus('保存配置失败: ' + (data.error || '未知错误'), 'error');
    }
  } catch (error) {
    console.error('保存配置出错:', error);
    showStatus('保存配置时发生错误: ' + error.message, 'error');
  } finally {
    isSaving.value = false;
  }
}

// 重置配置
function resetConfig() {
  if (originalConfig.value) {
    // 重置为原始配置
    Object.assign(config, JSON.parse(JSON.stringify(originalConfig.value)));
    showStatus('配置已重置', 'info');
  } else {
    // 如果没有原始配置，则恢复默认
    Object.assign(config, JSON.parse(JSON.stringify(defaultConfig)));
    showStatus('已恢复默认配置', 'info');
  }
}

// 验证模型
async function validateModel() {
  isValidating.value = true;
  validationResult.value = false;
  
  try {
    // 首先保存当前配置
    await saveConfig();
    
    // 然后验证模型 - 不再嵌套config对象
    const response = await fetch(`${API_BASE_URL}/validate_model`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({})
    });
    
    const data = await response.json();
    
    validationResult.value = true;
    
    if (data.success) {
      validationSuccess.value = true;
      validationResponse.value = data.response;
      validationError.value = '';
      showStatus('模型验证成功', 'success');
    } else {
      validationSuccess.value = false;
      validationResponse.value = '';
      validationError.value = data.error || '未知错误';
      showStatus('模型验证失败', 'error');
    }
  } catch (error) {
    console.error('验证模型出错:', error);
    validationResult.value = true;
    validationSuccess.value = false;
    validationResponse.value = '';
    validationError.value = error.message || '请求验证服务失败';
    showStatus('验证模型时发生错误', 'error');
  } finally {
    isValidating.value = false;
  }
}

// 更新提供商相关字段
function updateProviderFields() {
  // 可以在这里添加切换提供商时的特殊处理逻辑
  showStatus(`已切换到 ${config.provider === 'openai' ? 'OpenAI' : 'Ollama'} 模式`, 'info');
}

// 显示状态消息
function showStatus(message, type = 'info') {
  statusMessage.value = message;
  statusType.value = type;
  
  // 自动清除成功和信息消息
  if (type === 'success' || type === 'info') {
    setTimeout(() => {
      if (statusMessage.value === message) {
        statusMessage.value = '';
      }
    }, 3000);
  }
}
</script>

<style scoped>
.model-config-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid #3498db;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.config-form {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.form-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.form-section h3 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #333;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.provider-selection {
  display: flex;
  gap: 20px;
}

.provider-selection label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

input[type="text"],
input[type="password"],
input[type="number"],
select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.slider-container input[type="range"] {
  flex: 1;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.status-message {
  margin-top: 16px;
  padding: 10px;
  border-radius: 4px;
}

.success {
  background-color: #d4edda;
  color: #155724;
}

.error {
  background-color: #f8d7da;
  color: #721c24;
}

.info {
  background-color: #d1ecf1;
  color: #0c5460;
}

.form-hint {
  display: block;
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

/* 按钮样式 */
.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.primary-btn {
  background-color: #4CAF50;
  color: white;
}

.primary-btn:hover:not(:disabled) {
  background-color: #45a049;
}

.secondary-btn {
  background-color: #f1f1f1;
  color: #333;
}

.secondary-btn:hover:not(:disabled) {
  background-color: #e7e7e7;
}

.validate-btn {
  background-color: #3498db;
  color: white;
}

.validate-btn:hover:not(:disabled) {
  background-color: #2980b9;
}

.validation-result {
  margin-top: 20px;
  padding: 15px;
  border-radius: 4px;
}

.validation-result h4 {
  margin-top: 0;
  margin-bottom: 10px;
}
</style>
