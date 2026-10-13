<template>
  <div>
    <el-progress :percentage="progress.percent" :status="progressStatus" />
    <div>{{ progress.desc }}</div>
  </div>
</template>

<script>
export default {
  name: 'RegressionReview',
  props: {
    sessionId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      progress: {
        percent: 0,
        desc: '等待AI分析...'
      },
      timer: null
    }
  },
  computed: {
    progressStatus() {
      if (this.progress.stage === 'error') return 'exception'
      if (this.progress.stage === 'done') return 'success'
      return ''
    }
  },
  mounted() {
    this.pollProgress()
  },
  beforeDestroy() {
    if (this.timer) clearInterval(this.timer)
  },
  data() {
    return {
      progress: {
        percent: 0,
        desc: '等待AI分析...'
      },
      timer: null,
      // 添加完成标记，防止多次触发done事件
      hasCompleted: false,
      lastStage: null,
      // 添加记录请求ID，防止重复响应
      requestCounter: 0
    }
  },
  methods: {
    pollProgress() {
      // 添加日志跟踪
      console.log(`开始轮询进度 - sessionId: ${this.sessionId}`);
      
      this.timer = setInterval(async () => {
        // 如果已经完成，停止轮询
        if (this.hasCompleted) {
          console.log('审查已完成，停止轮询');
          clearInterval(this.timer);
          return;
        }
        
        try {
          // 生成唯一请求ID跟踪请求响应
          const currentRequestId = ++this.requestCounter;
          
          // 修正路径，添加缺失的前缀
          const res = await fetch(`/api/documentReview/Regression/reviewer/api/regression/review/progress?session_id=${this.sessionId}`)
          const data = await res.json()
          
          // 如果不是最新请求的响应，忽略它
          if (currentRequestId !== this.requestCounter) {
            console.log(`过期的进度请求(${currentRequestId})被忽略`);
            return;
          }
          
          console.log(`获取进度数据(${currentRequestId}):`, data);
          
          // 如果当前状态与上次相同，不重复处理
          if (this.lastStage === data.stage) {
            return;
          }
          
          // 更新进度和状态
          this.progress = data;
          this.lastStage = data.stage;
          
          // 如果完成或出错，停止轮询并发送信号
          if (data.stage === 'done' || data.stage === 'error') {
            console.log(`审查已${data.stage === 'done' ? '完成' : '出错'}，停止轮询`)
            clearInterval(this.timer);
            this.hasCompleted = true;
            this.$emit('done', data);
          }
        } catch (error) {
          console.error('获取进度失败:', error);
        }
      }, 2000); // 增加轮询间隔到 2 秒，减少服务器负担
    }
  }
}
</script>
