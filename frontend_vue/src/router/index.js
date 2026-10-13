import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// 登录模块
import Login from '../views/auth/Login.vue';

// 文档审查模块
import DocumentReviewContainer from '../views/documentReview/DocumentReviewContainer.vue';
import ConfigurationItemSimple from '../views/documentReview/configurationItem/ConfigurationItemSimple.vue';
import RegressionSimple from '../views/documentReview/regression/RegressionSimple.vue';

// 代码审查模块
import CodeReviewContainer from '../views/codeReview/CodeReviewContainer.vue';
import ConfigurationItemCodeReview from '../views/codeReview/configurationItem/ConfigurationItemCodeReview.vue';
import RegressionCodeReview from '../views/codeReview/regression/RegressionCodeReview.vue';
import RegressionTestCodeReview from '../views/codeReview/regressionTest/ConfigurationItemCodeReview.vue';
import CodeMapMultiMode from '../views/codeReview/configurationItem/CodeMapMultiMode.vue';
import RegressionTestCodeMapMultiMode from '../views/codeReview/regressionTest/CodeMapMultiMode.vue';
import FeatureReviewPage from '../views/codeReview/configurationItem/featureReview/FeatureReviewPage.vue';
import ChainReviewProgressPage from '../views/codeReview/configurationItem/ChainReviewProgressPage.vue';
import RegressionTestFeatureReviewPage from '../views/codeReview/regressionTest/featureReview/FeatureReviewPage.vue';
import RegressionTestChainReviewProgressPage from '../views/codeReview/regressionTest/ChainReviewProgressPage.vue';

// 静态分析模块
import StaticAnalysis from '../views/staticAnalysis/StaticAnalysis.vue';

// 项目管理模块
import ProjectListView from '../views/projectManagement/ProjectListView.vue';
import ProjectCreateView from '../views/projectManagement/ProjectCreateView.vue';
import ProjectDetailView from '../views/projectManagement/ProjectDetailView.vue';

// 数据库管理模块
import DatabaseManage from '../views/databaseManage/dynamicDatabaseManage/DatabaseManage.vue';
import OptoKnowledgeEntry from '../views/databaseManage/optoKnowledge/OptoKnowledgeEntry.vue';
import OptoKnowledgeGraph from '../views/databaseManage/optoKnowledge/OptoKnowledgeGraph.vue';
import AutomationDashboard from '../views/databaseManage/automationDashboard/AutomationDashboard.vue';

// 动态测试模块
import ConfigurationTestView from '../views/danamicTest/ConfigurationItem/ConfigurationTestView.vue';
import RegressionTestView from '../views/danamicTest/Regression/RegressionTestView.vue';

// 测试工具模块 - 改为懒加载以提升性能
// import TestToolsIndex from '../views/testTools/TestToolsIndex.vue';
// import AssessmentFormHelper from '../views/testTools/assessmentFormHelper/AssessmentFormHelper.vue';
// import StaticAnalysisFilter from '../views/testTools/staticAnalysisFilter/StaticAnalysisFilter.vue';
// import TestCaseSummary from '../views/testTools/testCaseSummary/TestCaseSummary.vue';
// import DocumentAnnotations2problemsSheet from '../views/testTools/documentAnnotations2problemsSheet/DocumentAnnotations2problemsSheet.vue';
// import TestEnvironmentDiagram from '../views/testTools/testEnvironmentDiagram/TestEnvironmentDiagram.vue';

// 管理员模块（隐藏路径，仅管理员知晓）
import TaskManager from '../views/admin/TaskManager.vue';
import TaskDataPanel from '../views/admin/TaskDataPanel.vue';
import UserManage from '../views/admin/UserManage.vue';

// 维护模块
import FeedbackPage from '../views/maintenance/feedback/FeedbackPage.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login,
      meta: { 
        title: '用户登录',
        public: true  // 标记为公开页面，不需要登录
      }
    },
    {
      path: '/',
      redirect: '/document-review'
    },
    {
      path: '/document-review',
      name: 'document-review',
      component: DocumentReviewContainer,
      redirect: '/document-review/configuration-item',
      children: [
        {
          path: 'configuration-item',
          name: 'configuration-item-simple',
          component: ConfigurationItemSimple,
          meta: { title: '配置项文档审查' }
        },
        {
          path: 'regression',
          name: 'regression-simple',
          component: RegressionSimple,
          meta: { title: '回归文档审查' }
        }
      ]
    },
    {
      path: '/code-review',
      name: 'code-review',
      component: CodeReviewContainer,
      redirect: '/code-review/configuration-item',
      children: [
        {
          path: 'configuration-item',
          name: 'configuration-item-code-review',
          component: ConfigurationItemCodeReview,
          meta: { title: '配置项代码审查' }
        },
        {
          path: 'feature-review/:taskId',
          name: 'feature-review',
          component: FeatureReviewPage,
          meta: { title: '功能审查' }
        },
        {
          path: 'chain-progress/:taskId',
          name: 'chain-review-progress',
          component: ChainReviewProgressPage,
          meta: { title: '链路审查进度' }
        },
        {
          path: 'regression',
          name: 'regression-code-review',
          component: RegressionCodeReview,
          meta: { title: '回归代码审查' }
        },
        {
          path: 'regression-test',
          name: 'regression-test-code-review',
          component: RegressionTestCodeReview,
          meta: { title: '新回归测试' }
        },
        {
          path: 'regression-test/feature-review/:taskId',
          name: 'regression-test-feature-review',
          component: RegressionTestFeatureReviewPage,
          meta: { title: '新回归测试-功能审查' }
        },
        {
          path: 'regression-test/chain-progress/:taskId',
          name: 'regression-test-chain-progress',
          component: RegressionTestChainReviewProgressPage,
          meta: { title: '新回归测试-链路审查进度' }
        },
        {
          path: 'regression-test/codemap/:taskId',
          name: 'regression-test-codemap',
          component: RegressionTestCodeMapMultiMode,
          meta: { title: '新回归测试-代码视图', fullScreen: true }
        }
      ]
    },
    {
      path: '/codemap/:taskId',
      name: 'codemap',
      component: CodeMapMultiMode,
      meta: { title: '代码视图', fullScreen: true }
    },
    {
      path: '/static-analysis',
      name: 'static-analysis',
      component: StaticAnalysis,
      meta: { title: '静态分析' }
    },
    {
      path: '/static-analysis/code-view/:sessionId',
      name: 'static-analysis-code-view',
      component: () => import('../views/staticAnalysis/filter/StaticAnalysisCodeView.vue'),
      meta: { title: '静态分析代码视图', fullScreen: true }
    },
    {
      path: '/static-analysis/fpga-code-view/:sessionId',
      name: 'static-analysis-fpga-code-view',
      component: () => import('../views/staticAnalysis/filterFpga/StaticAnalysisCodeView.vue'),
      meta: { title: 'FPGA 代码视图', fullScreen: true }
    },
    {
      path: '/static-analysis/normal-c-code-view/:sessionId',
      name: 'static-analysis-normal-c-code-view',
      component: () => import('../views/staticAnalysis/normalModeC/StaticAnalysisCodeView.vue'),
      meta: { title: '纯AI模式C代码视图', fullScreen: true }
    },
    {
      path: '/static-analysis/normal-fpga-code-view/:sessionId',
      name: 'static-analysis-normal-fpga-code-view',
      component: () => import('../views/staticAnalysis/normalModeFpga/StaticAnalysisCodeView.vue'),
      meta: { title: '纯AI模式FPGA代码视图', fullScreen: true }
    },
    {
      path: '/project-management',
      name: 'project-management',
      component: ProjectListView,
      meta: { title: '项目管理' }
    },
    {
      path: '/project-management/create',
      name: 'project-create',
      component: ProjectCreateView,
      meta: { title: '创建项目' }
    },
    {
      path: '/project-management/:id',
      name: 'project-detail',
      component: ProjectDetailView,
      meta: { title: '项目详情' }
    },
    {
      path: '/database-manage',
      name: 'database-manage',
      component: DatabaseManage,
      meta: { title: '数据库管理' }
    },
    {
      path: '/database-manage/opto-knowledge',
      name: 'opto-knowledge-entry',
      component: OptoKnowledgeEntry,
      meta: { title: '光电知识系统', fullScreen: true }
    },
    {
      path: '/database-manage/opto-knowledge/:domain',
      name: 'opto-knowledge-graph',
      component: OptoKnowledgeGraph,
      meta: { title: '光电知识图谱', fullScreen: true }
    },
    {
      path: '/database-manage/dynamic',
      name: 'database-manage-dynamic',
      component: DatabaseManage,
      meta: { title: '动态资产管理' }
    },
    {
      path: '/database-manage/static',
      name: 'database-manage-static',
      component: () => import('../views/databaseManage/staticAssets/StaticAssets.vue'),
      meta: { title: '静态资产管理' }
    },
    {
      path: '/database-manage/automation-dashboard',
      name: 'automation-dashboard',
      component: AutomationDashboard,
      meta: { title: '自动化看板' }
    },
    {
      path: '/dynamic-test/configuration-item',
      name: 'configuration-test',
      component: ConfigurationTestView,
      meta: { title: '配置项动态测试' }
    },
    {
      path: '/dynamic-test/regression',
      name: 'regression-test',
      component: RegressionTestView,
      meta: { title: '回归动态测试' }
    },
    {
      path: '/test-tools',
      name: 'TestToolsIndex',
      component: () => import('../views/testTools/TestToolsIndex.vue'),
      meta: { title: '测试工具' }
    },
    {
      path: '/test-report',
      name: 'TestReportIndex',
      component: () => import('../views/testReport/TestReportIndex.vue'),
      meta: { title: '测试报告' }
    },
    {
      path: '/test-tools/assessment-form-helper',
      name: 'AssessmentFormHelper',
      component: () => import('../views/testTools/assessmentFormHelper/AssessmentFormHelper.vue'),
      meta: { title: '充分性要求、通过准则列生成工具' }
    },
    {
      path: '/test-tools/static-analysis-filter',
      name: 'StaticAnalysisFilter',
      component: () => import('../views/testTools/staticAnalysisFilter/StaticAnalysisFilter.vue'),
      meta: { title: '静态分析问题过滤工具' }
    },
    {
      path: '/test-tools/test-case-summary',
      name: 'TestCaseSummary',
      component: () => import('../views/testTools/testCaseSummary/TestCaseSummary.vue'),
      meta: { title: '功能性能指标符合性表生成工具' }
    },
    {
      path: '/test-tools/test-case-assistant',
      name: 'TestCaseAssistant',
      component: () => import('../views/testTools/testCaseAssistant/TestCaseAssistant.vue'),
      meta: { title: '测试用例辅助设计（Excel）', fullScreen: true }
    },
    {
      path: '/test-tools/test-environment-diagram',
      name: 'TestEnvironmentDiagram',
      component: () => import('../views/testTools/testEnvironmentDiagram/TestEnvironmentDiagram.vue'),
      meta: { title: '测试环境图和说明生成工具' }
    },
    {
      path: '/test-tools/outline-rewriter',
      name: 'OutlineRewriter',
      component: () => import('../views/testTools/outlineRewriter/OutlineRewriter.vue'),
      meta: { title: '鉴定测评大纲二次编写工具' }
    },
    {
      path: '/maintenance/feedback',
      name: 'maintenance-feedback',
      component: FeedbackPage,
      meta: { title: '用户反馈' }
    },
    // 管理员任务管理页面（隐藏路径，不在导航中显示）
    {
      path: '/admin-task-manager',
      name: 'admin-task-manager',
      component: TaskManager,
      meta: { 
        title: '任务管理中心（管理员）',
        hidden: true,  // 标记为隐藏路由，不在导航菜单中显示
        requireAuth: true  // 需要管理员权限
      }
    },
    {
      path: '/admin-task-data',
      name: 'admin-task-data',
      component: TaskDataPanel,
      meta: {
        title: '任务数据查看与导出（管理员）',
        hidden: true,
        requireAuth: true
      }
    },
    // 管理员人员管理页面（隐藏路径，不在导航中显示）
    {
      path: '/admin-user-manage',
      name: 'admin-user-manage',
      component: UserManage,
      meta: {
        title: '人员管理（管理员）',
        hidden: true,
        requireAuth: true
      }
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = to.meta.title
  }

  // 检查是否是公开页面
  if (to.meta.public) {
    next()
    return
  }

  // 检查登录状态
  const authStore = useAuthStore()
  
  // 如果store中没有用户信息，尝试从localStorage恢复
  if (!authStore.isAuthenticated) {
    authStore.initFromStorage()
  }

  // 验证登录状态
  const isAuthenticated = await authStore.checkAuth()

  if (!isAuthenticated) {
    // 未登录，跳转到登录页
    next({
      path: '/login',
      query: { redirect: to.fullPath }  // 保存原始目标路径
    })
  } else {
    // 已登录，允许访问
    next()
  }
})

export default router
