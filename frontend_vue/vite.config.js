import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  build: {
    // 🔧 优化构建配置，解决生产环境问题
    rollupOptions: {
      output: {
        // 🔧 优化分块策略，减少网络请求库的独立打包
        manualChunks: {
          // 将Vue相关库打包到一个chunk
          'vue-vendor': ['vue', 'vue-router'],
          // 🚀 将axios与Vue一起打包，避免跨chunk的依赖问题
          'vendor': ['axios', 'element-plus'],
          // 将图标库单独打包
          'icons': ['@element-plus/icons-vue']
        },
        // 优化chunk文件名
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    },
    // 🔧 启用压缩优化
    minify: 'terser',
    terserOptions: {
      compress: {
        // 移除console.log（生产环境）
        drop_console: false, // 暂时保留console以便调试
        drop_debugger: true,
        // 🚀 保持函数名和对象属性，避免reduce等方法被错误优化
        keep_fnames: true,
        keep_fargs: true,
        passes: 1, // 减少优化次数，避免过度优化导致错误
      },
      mangle: {
        // 🚀 保持重要的属性名不被混淆
        keep_fnames: true,
        reserved: ['reduce', 'map', 'filter', 'forEach', 'data', 'response']
      }
    },
    // 设置chunk大小警告限制
    chunkSizeWarningLimit: 1000,
    // 🔧 启用CSS代码分割，但确保关键CSS内联
    cssCodeSplit: true,
    // 🔧 启用源码映射以便调试
    sourcemap: true,
    // 目标环境
    target: 'es2015',
    // 🔧 确保资源内联阈值合理
    assetsInlineLimit: 4096,
  },
  server: {
    proxy: {
      // '/pm_api': {
      //   target: 'http://localhost:5002',
      //   changeOrigin: true,
      //   secure: false
      // },
      '/api': {
        target: 'http://localhost:5002',
        changeOrigin: true,
        secure: false,
        ws: true,
        // 🔧 提高超时，避免大文件上传/长任务导致 ERR_EMPTY_RESPONSE
        timeout: 1200000, // 20 分钟
        proxyTimeout: 1200000,
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq) => {
            // 保持连接活跃
            proxyReq.setHeader('Connection', 'keep-alive')
          })
        }
      },
      '/regression': {
        target: 'http://localhost:5002',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
