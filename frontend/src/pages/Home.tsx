import React from 'react';
import { Layout, Typography, Space } from 'antd';
import TagSelector from '../components/TagSelector';
import JobList from '../components/JobList';

const { Header, Content } = Layout;
const { Title } = Typography;

const Home: React.FC = () => {
  return (
    <Layout className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 - 深色背景配白色文字，绝对清晰 */}
      <Header
        className="shadow-md px-8 flex items-center justify-between sticky top-0 z-10"
        style={{
          height: '64px',
          lineHeight: '64px',
          background: 'linear-gradient(135deg, #00b38a 0%, #00875f 100%) !important',
        }}
      >
        <Space size="middle">
          <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-[#00b38a] font-bold text-xl shadow-md">
            B
          </div>
          <Title
            level={3}
            className="!mb-0 !text-2xl font-bold text-white"
          >
            智能职位推荐系统
          </Title>
        </Space>
        <div className="flex items-center gap-4">
          <span
            className="text-sm px-3 py-1 rounded-full font-medium bg-white/20 text-white border border-white/30"
          >
            淘天招聘
          </span>
          <span
            className="text-sm font-medium text-white/90"
          >
            共 2000+ 个职位
          </span>
        </div>
      </Header>

      {/* 主内容区 - 三栏布局 */}
      <Content className="p-4">
        <div className="flex gap-4 h-[calc(100vh-112px)]">
          {/* 左侧标签选择区 - 25%宽度 */}
          <div className="w-[25%] min-w-[280px] h-full">
            <TagSelector />
          </div>

          {/* 中间职位列表区 - 75%宽度 */}
          <div className="flex-1 min-w-[400px] h-full">
            <JobList />
          </div>
        </div>
      </Content>
    </Layout>
  );
};

export default Home;
