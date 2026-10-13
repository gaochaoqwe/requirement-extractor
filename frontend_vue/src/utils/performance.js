/**
 * 前端性能监控工具
 */

export class PerformanceMonitor {
  constructor() {
    this.marks = new Map()
    this.measures = new Map()
  }

  // 标记开始时间
  mark(name) {
    const markName = `${name}-start`
    performance.mark(markName)
    this.marks.set(name, Date.now())
    console.log(`🚀 [Performance] ${name} 开始`)
  }

  // 标记结束时间并计算耗时
  measure(name) {
    const startTime = this.marks.get(name)
    if (!startTime) {
      console.warn(`⚠️ [Performance] 未找到 ${name} 的开始标记`)
      return
    }

    const endTime = Date.now()
    const duration = endTime - startTime
    
    const startMarkName = `${name}-start`
    const endMarkName = `${name}-end`
    const measureName = `${name}-duration`
    
    performance.mark(endMarkName)
    performance.measure(measureName, startMarkName, endMarkName)
    
    this.measures.set(name, duration)
    
    // 根据耗时显示不同颜色的日志
    if (duration < 100) {
      console.log(`✅ [Performance] ${name} 完成: ${duration}ms (快速)`)
    } else if (duration < 500) {
      console.log(`⚡ [Performance] ${name} 完成: ${duration}ms (正常)`)
    } else if (duration < 1000) {
      console.warn(`⚠️ [Performance] ${name} 完成: ${duration}ms (较慢)`)
    } else {
      console.error(`🐌 [Performance] ${name} 完成: ${duration}ms (很慢)`)
    }
    
    return duration
  }

  // 获取所有测量结果
  getAllMeasures() {
    return Object.fromEntries(this.measures)
  }

  // 监控路由切换性能
  monitorRouteChange(to, from) {
    const routeName = to.name || to.path
    this.mark(`route-${routeName}`)
    
    // 在下一个tick测量，确保组件已加载
    this.$nextTick(() => {
      this.measure(`route-${routeName}`)
    })
  }

  // 监控组件加载性能
  monitorComponentLoad(componentName) {
    this.mark(`component-${componentName}`)
    
    return () => {
      this.measure(`component-${componentName}`)
    }
  }

  // 监控API请求性能
  monitorApiRequest(apiName) {
    this.mark(`api-${apiName}`)
    
    return () => {
      this.measure(`api-${apiName}`)
    }
  }

  // 获取页面加载性能指标
  getPageLoadMetrics() {
    if (!window.performance || !window.performance.timing) {
      console.warn('浏览器不支持Performance API')
      return null
    }

    const timing = window.performance.timing
    const metrics = {
      // DNS查询时间
      dnsLookup: timing.domainLookupEnd - timing.domainLookupStart,
      // TCP连接时间
      tcpConnect: timing.connectEnd - timing.connectStart,
      // 请求响应时间
      request: timing.responseEnd - timing.requestStart,
      // DOM解析时间
      domParse: timing.domContentLoadedEventEnd - timing.domLoading,
      // 页面完全加载时间
      pageLoad: timing.loadEventEnd - timing.navigationStart,
      // 首次渲染时间
      firstPaint: this.getFirstPaint(),
      // 首次内容渲染时间
      firstContentfulPaint: this.getFirstContentfulPaint()
    }

    console.table(metrics)
    return metrics
  }

  // 获取首次渲染时间
  getFirstPaint() {
    const paintEntries = performance.getEntriesByType('paint')
    const firstPaint = paintEntries.find(entry => entry.name === 'first-paint')
    return firstPaint ? Math.round(firstPaint.startTime) : null
  }

  // 获取首次内容渲染时间
  getFirstContentfulPaint() {
    const paintEntries = performance.getEntriesByType('paint')
    const fcp = paintEntries.find(entry => entry.name === 'first-contentful-paint')
    return fcp ? Math.round(fcp.startTime) : null
  }

  // 清理性能数据
  clear() {
    this.marks.clear()
    this.measures.clear()
    performance.clearMarks()
    performance.clearMeasures()
  }
}

// 创建全局实例
export const performanceMonitor = new PerformanceMonitor()

// 在开发环境下自动监控页面加载
if (import.meta.env.DEV) {
  window.addEventListener('load', () => {
    setTimeout(() => {
      performanceMonitor.getPageLoadMetrics()
    }, 100)
  })
} 