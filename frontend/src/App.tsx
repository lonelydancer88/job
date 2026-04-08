import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Home from './pages/Home';
import JobDetailPage from './pages/JobDetailPage';
import './App.css';

// BOSS直聘风格主题配置
const theme = {
  token: {
    colorPrimary: '#00b38a', // BOSS直聘主色
    colorSuccess: '#00b38a',
    colorWarning: '#ff7d00',
    colorError: '#f53f3f',
    colorInfo: '#1579ff',
    fontSize: 14,
    borderRadius: 8,
    wireframe: false,
    colorBgBase: '#ffffff',
    colorBgLayout: '#f5f7fa',
    colorBgHeader: '#ffffff',
    colorBorder: '#e8eaed',
    fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif',
  },
  components: {
    Button: {
      borderRadius: 6,
      controlHeight: 36,
      primaryShadow: '0 2px 8px rgba(0, 179, 138, 0.3)',
      defaultBorderColor: '#e0e0e0',
    },
    Card: {
      borderRadius: 12,
      boxShadow: '0 2px 12px rgba(0, 0, 0, 0.05)',
      paddingLG: '20px',
    },
    Checkbox: {
      borderRadius: 4,
      colorPrimary: '#00b38a',
      colorPrimaryHover: '#00c79b',
    },
    Input: {
      borderRadius: 6,
    },
    Select: {
      borderRadius: 6,
    },
    Progress: {
      colorPrimary: '#00b38a',
      colorInfoBg: '#e6fff9',
    },
    Pagination: {
      itemActiveBg: '#00b38a',
      itemSize: 32,
      borderRadius: 6,
    },
    Tag: {
      borderRadius: 4,
      paddingSM: '3px 8px',
      colorPrimaryBg: '#e6fff9',
    },
    Typography: {
      colorText: '#333333',
      colorTextSecondary: '#666666',
      colorTextTertiary: '#999999',
    },
  },
};

function App() {
  return (
    <ConfigProvider locale={zhCN} theme={theme}>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/job/:jobId" element={<JobDetailPage />} />
        </Routes>
      </Router>
    </ConfigProvider>
  );
}

export default App;
