import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  css: {
    preprocessorOptions: {
      less: {
        modifyVars: {
          // BOSS直聘风格主题色
          '@primary-color': '#1579ff',
          '@success-color': '#00b42a',
          '@warning-color': '#ff7d00',
          '@error-color': '#f53f3f',
          '@info-color': '#1579ff',
          // 字体配置
          '@font-size-base': '14px',
          '@font-family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
          // 边框圆角
          '@border-radius-base': '6px',
          // 组件尺寸
          '@height-base': '36px',
          '@height-lg': '40px',
          '@height-sm': '28px',
        },
        javascriptEnabled: true,
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
