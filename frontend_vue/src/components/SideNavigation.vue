<template>
  <div class="side-navigation">
    <nav class="side-nav">
      <div class="nav-header">
        <h1>AI测试工具（内部）</h1>
      </div>
      
      <!-- 用户信息区域 -->
      <div class="user-info" v-if="authStore.isAuthenticated">
        <div class="user-avatar">
          <i class="avatar-icon"></i>
        </div>
        <div class="user-details">
          <div class="user-name">{{ authStore.user?.display_name }}</div>
          <div class="user-username">@{{ authStore.user?.username }}</div>
        </div>
        <button class="logout-btn" @click="handleLogout" title="退出登录">
          <i class="logout-icon"></i>
        </button>
      </div>
      
      <ul class="nav-links">
        <!--
        <li>
          <router-link to="/project-management" :class="{ active: currentRoute.startsWith('/project-management') }">
            <i class="nav-icon project-icon"></i>
            <span>项目管理</span>
          </router-link>
        </li>
        -->
        <li v-if="deployConfig.nav.showDocumentReview" class="has-submenu">
          <div class="nav-item" :class="{ active: isDocumentReviewActive }" @click="toggleDocumentReviewSubmenu">
            <i class="nav-icon doc-icon"></i>
            <span>文档审查</span>
            <i class="dropdown-icon" :class="{ 'dropdown-open': isDocumentReviewExpanded }"></i>
          </div>
          <ul class="submenu" v-show="isDocumentReviewExpanded">
            <li>
              <router-link to="/document-review/configuration-item" 
                         :class="{ active: currentRoute === '/document-review/configuration-item' }">
                <span>配置项测试</span>
              </router-link>
            </li>
            <li>
              <router-link to="/document-review/regression"
                         :class="{ active: currentRoute === '/document-review/regression' }">
                <span>回归测试</span>
              </router-link>
            </li>
          </ul>
        </li>
        <li>
          <router-link to="/static-analysis" :class="{ active: currentRoute === '/static-analysis' }">
            <i class="nav-icon analysis-icon"></i>
            <span>静态分析</span>
          </router-link>
        </li>
        <li class="has-submenu">
          <div class="nav-item" :class="{ active: isCodeReviewActive }" @click="toggleCodeReviewSubmenu">
            <i class="nav-icon code-icon"></i>
            <span>代码审查</span>
            <i class="dropdown-icon" :class="{ 'dropdown-open': isCodeReviewExpanded }"></i>
          </div>
          <ul class="submenu" v-show="isCodeReviewExpanded">
            <li>
              <router-link to="/code-review/configuration-item" 
                         :class="{ active: currentRoute === '/code-review/configuration-item' }">
                <span>配置项测试</span>
              </router-link>
            </li>
            <li v-if="deployConfig.nav.showCodeReviewRegressionTest">
              <router-link to="/code-review/regression-test"
                         :class="{ active: currentRoute.startsWith('/code-review/regression-test') }">
                <span>新回归测试</span>
              </router-link>
            </li>
            <li v-if="showLegacyCodeReviewRegression">
              <router-link to="/code-review/regression"
                         :class="{ active: currentRoute === '/code-review/regression' }">
                <span>回归测试</span>
              </router-link>
            </li>
          </ul>
        </li>
        <li v-if="deployConfig.nav.showDynamicTest" class="has-submenu">
          <div class="nav-item" :class="{ active: isDynamicTestActive }" @click="toggleDynamicTestSubmenu">
            <i class="nav-icon dynamic-test-icon"></i>
            <span>动态测试</span>
            <i class="dropdown-icon" :class="{ 'dropdown-open': isDynamicTestExpanded }"></i>
          </div>
          <ul class="submenu" v-show="isDynamicTestExpanded">
            <li>
              <router-link to="/dynamic-test/configuration-item" 
                         :class="{ active: currentRoute === '/dynamic-test/configuration-item' }">
                <span>配置项表单生成</span>
              </router-link>
            </li>
            <li>
              <router-link to="/test-tools/test-case-assistant" 
                         :class="{ active: currentRoute === '/test-tools/test-case-assistant' }">
                <span>配置项表单编辑</span>
              </router-link>
            </li>
            <li>
              <router-link to="/dynamic-test/regression"
                         :class="{ active: currentRoute === '/dynamic-test/regression' }">
                <span>回归表单生成</span>
              </router-link>
            </li>
          </ul>
        </li>
        <li v-if="deployConfig.nav.showTestReport">
          <router-link to="/test-report" :class="{ active: currentRoute.startsWith('/test-report') }">
            <i class="nav-icon report-icon"></i>
            <span>测试报告</span>
          </router-link>
        </li>
        <li v-if="deployConfig.nav.showTestTools">
          <router-link to="/test-tools" :class="{ active: currentRoute.startsWith('/test-tools') }">
            <i class="nav-icon test-tools-icon"></i>
            <span>测试工具</span>
          </router-link>
        </li>
        <li v-if="deployConfig.nav.showAssetManage" class="has-submenu">
          <div class="nav-item" :class="{ active: isAssetManageActive }" @click="toggleAssetManageSubmenu">
            <i class="nav-icon asset-icon"></i>
            <span>资产管理</span>
            <i class="dropdown-icon" :class="{ 'dropdown-open': isAssetManageExpanded }"></i>
          </div>
          <ul class="submenu" v-show="isAssetManageExpanded">
            <li>
              <router-link to="/database-manage/dynamic"
                           :class="{ active: currentRoute === '/database-manage/dynamic' }">
                <span>动态资产</span>
              </router-link>
            </li>
            <li>
              <router-link to="/database-manage/static"
                           :class="{ active: currentRoute === '/database-manage/static' }">
                <span>静态资产</span>
              </router-link>
            </li>
            <li>
              <router-link to="/database-manage/opto-knowledge"
                           :class="{ active: currentRoute.startsWith('/database-manage/opto-knowledge') }">
                <span>光电知识系统</span>
              </router-link>
            </li>
            <li>
              <router-link to="/database-manage/automation-dashboard"
                           :class="{ active: currentRoute === '/database-manage/automation-dashboard' }">
                <span>自动化看板</span>
              </router-link>
            </li>
          </ul>
        </li>

        <li v-if="deployConfig.nav.showFeedback">
          <router-link to="/maintenance/feedback" :class="{ active: currentRoute.startsWith('/maintenance/feedback') }">
            <i class="nav-icon feedback-icon"></i>
            <span>用户反馈</span>
          </router-link>
        </li>

      </ul>
    </nav>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { ElMessage } from 'element-plus';
import { deployConfig } from '@/config/deployConfig';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const currentRoute = computed(() => route.path);

// 退出登录
const handleLogout = async () => {
  try {
    await authStore.logout();
    ElMessage.success('已退出登录');
    router.push('/login');
  } catch (error) {
    ElMessage.error('退出登录失败');
  }
};

// 兼容原有逻辑
const props = defineProps({
  activeTab: String
});

const emit = defineEmits(['update:activeTab']);

function setActiveTab(tab) {
  emit('update:activeTab', tab);
}

// 审查状态变量
const isDocumentReviewActive = computed(() => {
  return currentRoute.value.startsWith('/document-review');
});

// 默认展开文档审查菜单
const isDocumentReviewExpanded = ref(true);

function toggleDocumentReviewSubmenu() {
  isDocumentReviewExpanded.value = !isDocumentReviewExpanded.value;
}

// 动态测试状态变量
const isDynamicTestActive = computed(() => {
  return (
    currentRoute.value.startsWith('/dynamic-test') ||
    currentRoute.value === '/test-tools/test-case-assistant'
  );
});

// 默认折叠动态测试菜单（仅命中路由时自动展开）
const isDynamicTestExpanded = ref(isDynamicTestActive.value);

function toggleDynamicTestSubmenu() {
  isDynamicTestExpanded.value = !isDynamicTestExpanded.value;
}

// 代码审查状态变量
const isCodeReviewActive = computed(() => {
  return currentRoute.value.startsWith('/code-review');
});

// 默认展开代码审查菜单
const isCodeReviewExpanded = ref(true);

const showLegacyCodeReviewRegression = ref(false);

function toggleCodeReviewSubmenu() {
  isCodeReviewExpanded.value = !isCodeReviewExpanded.value;
}

// 资产管理状态变量
const isAssetManageActive = computed(() => {
  return currentRoute.value.startsWith('/database-manage');
});

// 默认折叠资产管理菜单（仅命中路由时自动展开）
const isAssetManageExpanded = ref(isAssetManageActive.value);

function toggleAssetManageSubmenu() {
  isAssetManageExpanded.value = !isAssetManageExpanded.value;
}

watch(
  () => currentRoute.value,
  () => {
    isDynamicTestExpanded.value = isDynamicTestActive.value;
    isAssetManageExpanded.value = isAssetManageActive.value;
  },
  { immediate: true }
);
</script>

<style scoped>
.side-navigation {
  width: 220px;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  background-color: #2c3e50;
  color: #ecf0f1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #34495e;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.side-nav {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.nav-header {
  padding: 20px 15px;
  border-bottom: 1px solid #34495e;
  background-color: #1a2530;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-header h1 {
  margin: 0;
  font-weight: 500;
  font-size: 1.2rem;
  color: #ecf0f1;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

/* 用户信息样式 */
.user-info {
  display: flex;
  align-items: center;
  padding: 15px;
  background-color: #1a2530;
  border-bottom: 1px solid #34495e;
  gap: 10px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-icon {
  width: 24px;
  height: 24px;
  display: inline-block;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ffffff'%3E%3Cpath d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.user-details {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #ecf0f1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-username {
  font-size: 12px;
  color: #95a5a6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  width: 32px;
  height: 32px;
  border: none;
  background-color: #34495e;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  flex-shrink: 0;
}

.logout-btn:hover {
  background-color: #e74c3c;
}

.logout-icon {
  width: 18px;
  height: 18px;
  display: inline-block;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.nav-links {
  list-style: none;
  padding: 0;
  margin: 20px 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.nav-links li {
  margin-bottom: 5px;
}

.nav-links li a {
  padding: 15px 20px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s;
  color: #ecf0f1;
  text-decoration: none;
  width: 100%;
}

.nav-links li a:hover {
  background-color: #34495e;
  transform: translateX(5px);
}

.nav-links li a.active {
  background-color: #3498db;
  position: relative;
  transform: translateX(5px);
  border-radius: 0 4px 4px 0;
}

.nav-links li a.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background-color: #2ecc71;
}

.nav-icon {
  width: 22px;
  height: 22px;
  margin-right: 12px;
  display: inline-block;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  opacity: 0.8;
  transition: opacity 0.3s;
}

.nav-links li a:hover .nav-icon,
.nav-links li a.active .nav-icon {
  opacity: 1;
}

.doc-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1v5h5v10H6V3h7z'/%3E%3C/svg%3E");
}

.project-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M10 4H4c-1.11 0-2 .89-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z'/%3E%3C/svg%3E");
}

.analysis-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M3 13h2v-2H3v2zm0 4h2v-2H3v2zM3 9h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z'/%3E%3C/svg%3E");
}

.feedback-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 11H6v-2h12v2zm0-3H6V8h12v2zm0-3H6V5h12v2z'/%3E%3C/svg%3E");
}

.code-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z'/%3E%3C/svg%3E");
}

.dynamic-test-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z'/%3E%3C/svg%3E");
}

.config-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z'/%3E%3C/svg%3E");
}

.test-tools-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z'/%3E%3C/svg%3E");
}

.report-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M4 20h16v2H4zM6 10h3v8H6zM11 6h3v12h-3zM16 13h3v5h-3z'/%3E%3C/svg%3E");
}

.asset-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M20 6h-2.18c.11-.31.18-.65.18-1a2.996 2.996 0 0 0-5.5-1.65l-.5.67-.5-.68C10.96 2.54 10.05 2 9 2 7.34 2 6 3.34 6 5c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-5-2c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zM9 4c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1z'/%3E%3C/svg%3E");
}

.bottom-nav-item {
  margin-top: auto;
  border-top: 1px solid #34495e;
  padding-top: 15px;
  margin-top: 20px;
}

.bottom-nav-item a {
  display: flex;
  align-items: center;
  color: #ecf0f1;
  text-decoration: none;
}

.has-submenu {
  position: relative;
}

.nav-item {
  padding: 15px 20px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s;
  color: #ecf0f1;
  text-decoration: none;
  width: 100%;
}

.nav-item:hover {
  background-color: #34495e;
  transform: translateX(5px);
}

.nav-item.active {
  background-color: #3498db;
  position: relative;
  transform: translateX(5px);
  border-radius: 0 4px 4px 0;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background-color: #2ecc71;
}

.dropdown-icon {
  width: 22px;
  height: 22px;
  margin-left: 12px;
  display: inline-block;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  opacity: 0.8;
  transition: opacity 0.3s, transform 0.3s;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M7.41 7.84L12 12.42l4.59-4.58L18 9.25l-6 6-6-6z'/%3E%3C/svg%3E");
}

.dropdown-icon.dropdown-open {
  transform: rotate(180deg);
}

.submenu {
  list-style: none;
  padding: 0 0 0 20px;
  margin: 5px 0;
  background-color: #243342;
  border-left: 1px solid #34495e;
  width: 100%;
}

.submenu li {
  margin-bottom: 5px;
}

.submenu li a {
  padding: 10px 15px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s;
  color: #ecf0f1;
  text-decoration: none;
  width: 100%;
  font-size: 0.9rem;
}

.submenu li a:hover {
  background-color: #34495e;
  transform: translateX(5px);
}

.submenu li a.active {
  background-color: #3498db;
  position: relative;
  transform: translateX(5px);
  border-radius: 0 4px 4px 0;
}

.submenu li a.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background-color: #2ecc71;
}
</style>
