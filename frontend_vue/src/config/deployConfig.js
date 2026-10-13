/**
 * 部署版本配置
 *
 * 613: 标准版（当前版本）—— 工具模式在前，纯AI模式在后，默认C语言
 * 612: 简版            —— 纯AI模式在前，工具模式在后，默认FPGA；
 *                         导航栏隐藏：文档审查、动态测试、测试工具、资产管理、用户反馈；
 *                         代码审查只保留配置项测试，隐藏新回归测试。
 *
 * 通过 VITE_DEPLOY_MODE 环境变量切换，无需改代码。
 */
const mode = import.meta.env.VITE_DEPLOY_MODE || '613'

export const is612 = mode === '612'

export const deployConfig = {
  mode,

  // 静态分析页面默认激活的 Tab
  staticAnalysisDefaultView: is612 ? 'analysis' : 'filter',

  // 顶部 Tab 选项顺序
  staticAnalysisViewOptions: is612
    ? [
        { label: '纯AI模式', value: 'analysis' },
        { label: '工具模式', value: 'filter' },
      ]
    : [
        { label: '工具模式', value: 'filter' },
        { label: '纯AI模式', value: 'analysis' },
      ],

  // 静态分析两个模式默认语言（612 默认 FPGA，613 默认 C）
  staticAnalysisDefaultLang: is612 ? 'fpga' : 'c',

  // 导航栏显示控制
  nav: {
    showDocumentReview:           !is612,
    showDynamicTest:              !is612,
    showTestReport:               !is612,
    showTestTools:                !is612,
    showAssetManage:              !is612,
    showCodeReviewRegressionTest: !is612,
    showFeedback:                 !is612,
  },
}
