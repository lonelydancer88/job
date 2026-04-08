import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout, Typography, Button, Card, Descriptions, Divider, Tag, Space, Breadcrumb, Spin, message } from 'antd';
import { ArrowLeftOutlined, LinkOutlined, StarOutlined, ShareAltOutlined } from '@ant-design/icons';
import { getJobDetail } from '../services/api';
import type { Job } from '../types';

const { Header, Content } = Layout;
const { Title, Paragraph } = Typography;

const JobDetailPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchJobDetail = async () => {
      if (!jobId) return;

      setLoading(true);
      try {
        const res = await getJobDetail(parseInt(jobId));
        if (res.code === 0) {
          setJob(res.data);
        }
      } catch (error) {
        console.error('获取职位详情失败:', error);
        message.error('获取职位详情失败，请返回重试');
      } finally {
        setLoading(false);
      }
    };

    fetchJobDetail();
  }, [jobId]);

  if (loading) {
    return (
      <Layout className="min-h-screen bg-gray-50">
        <Header className="bg-white shadow-sm px-6">
          <Breadcrumb className="py-4">
            <Breadcrumb.Item onClick={() => navigate('/')} className="cursor-pointer">
              首页
            </Breadcrumb.Item>
            <Breadcrumb.Item>职位详情</Breadcrumb.Item>
          </Breadcrumb>
        </Header>
        <Content className="p-6 flex justify-center items-center">
          <Spin size="large" />
        </Content>
      </Layout>
    );
  }

  if (!job) {
    return (
      <Layout className="min-h-screen bg-gray-50">
        <Header className="bg-white shadow-sm px-6">
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
            className="my-4"
          >
            返回列表
          </Button>
        </Header>
        <Content className="p-6 flex justify-center items-center">
          <div className="text-center">
            <p className="text-gray-500 mb-4">职位不存在或已被删除</p>
            <Button type="primary" onClick={() => navigate('/')}>返回职位列表</Button>
          </div>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <Header className="bg-white shadow-sm px-8 flex items-center justify-between sticky top-0 z-10" style={{ height: '64px', lineHeight: '64px' }}>
        <Breadcrumb>
          <Breadcrumb.Item
            onClick={() => navigate('/')}
            className="cursor-pointer hover:text-[#00b38a] transition-colors"
          >
            ← 返回职位列表
          </Breadcrumb.Item>
          <Breadcrumb.Item className="text-gray-400">职位详情</Breadcrumb.Item>
        </Breadcrumb>
        <div className="flex items-center gap-4">
          <span className="text-sm px-3 py-1 bg-[#e6fff9] text-[#00b38a] rounded-full font-medium">
            淘天招聘
          </span>
        </div>
      </Header>

      {/* 详情内容 */}
      <Content className="p-6 max-w-5xl mx-auto w-full">
        <Card className="shadow-md">
          {/* 职位头部信息 */}
          <div className="mb-6">
            <div className="flex justify-between items-start mb-4">
              <Title level={2} className="!mb-0 text-gray-900">
                {job.title}
              </Title>
              <Title level={2} className="!mb-0 text-[#fa6041] font-bold">
                {job.salary || '面议'}
              </Title>
            </div>

            <div className="flex flex-wrap gap-3 mb-6">
              <Tag style={{ background: 'linear-gradient(135deg, #165dff 0%, #4080ff 100%)', color: '#ffffff', border: 'none', fontSize: '14px', padding: '6px 16px', borderRadius: '20px', fontWeight: '500' }}>
                📍 {job.location}
              </Tag>
              <Tag style={{ background: 'linear-gradient(135deg, #00b38a 0%, #00c79b 100%)', color: '#ffffff', border: 'none', fontSize: '14px', padding: '6px 16px', borderRadius: '20px', fontWeight: '500' }}>
                ⏳ {job.work_experience}
              </Tag>
              <Tag style={{ background: 'linear-gradient(135deg, #722ed1 0%, #9254de 100%)', color: '#ffffff', border: 'none', fontSize: '14px', padding: '6px 16px', borderRadius: '20px', fontWeight: '500' }}>
                🏢 {job.department}
              </Tag>
              {job.publish_date && (
                <Tag style={{ background: 'linear-gradient(135deg, #fa8c16 0%, #ffa940 100%)', color: '#ffffff', border: 'none', fontSize: '14px', padding: '6px 16px', borderRadius: '20px', fontWeight: '500' }}>
                  🕒 发布时间：{job.publish_date}
                </Tag>
              )}
            </div>

            <Descriptions bordered column={2} size="small" className="mb-6">
              <Descriptions.Item label="职位ID">{job.job_id}</Descriptions.Item>
              <Descriptions.Item label="部门">{job.department || '未注明'}</Descriptions.Item>
            </Descriptions>

            <Space className="mb-6" size="middle">
              <Button
                type="primary"
                size="large"
                icon={<LinkOutlined />}
                onClick={() => window.open(job.url, '_blank')}
                style={{
                  background: 'linear-gradient(135deg, #00b38a 0%, #00c79b 100%)',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0 32px',
                  height: '44px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  boxShadow: '0 4px 12px rgba(0, 179, 138, 0.3)',
                }}
              >
                立即投递
              </Button>
              <Button
                size="large"
                icon={<StarOutlined />}
                style={{ borderRadius: '8px', height: '44px', padding: '0 24px' }}
              >
                收藏
              </Button>
              <Button
                size="large"
                icon={<ShareAltOutlined />}
                style={{ borderRadius: '8px', height: '44px', padding: '0 24px' }}
              >
                分享
              </Button>
            </Space>
          </div>

          <Divider />

          {/* 岗位职责 */}
          <div className="mb-8">
            <Title level={3} className="!mb-4 text-gray-800">
              📋 岗位职责
            </Title>
            <Paragraph className="text-gray-700 whitespace-pre-line text-base leading-relaxed">
              {job.responsibilities || '暂无信息'}
            </Paragraph>
          </div>

          <Divider />

          {/* 任职要求 */}
          <div className="mb-8">
            <Title level={3} className="!mb-4 text-gray-800">
              ✅ 任职要求
            </Title>
            <Paragraph className="text-gray-700 whitespace-pre-line text-base leading-relaxed">
              {job.requirements || '暂无信息'}
            </Paragraph>
          </div>

          <Divider />

          <div className="flex justify-center gap-4 mt-8">
            <Button
              type="primary"
              size="large"
              icon={<LinkOutlined />}
              onClick={() => window.open(job.url, '_blank')}
              style={{
                minWidth: 220,
                background: 'linear-gradient(135deg, #00b38a 0%, #00c79b 100%)',
                border: 'none',
                borderRadius: '8px',
                height: '48px',
                fontSize: '16px',
                fontWeight: 'bold',
                boxShadow: '0 4px 12px rgba(0, 179, 138, 0.3)',
              }}
            >
              查看原职位并投递
            </Button>
            <Button
              size="large"
              onClick={() => navigate('/')}
              style={{ minWidth: 120, borderRadius: '8px', height: '48px' }}
            >
              返回列表
            </Button>
          </div>
        </Card>
      </Content>
    </Layout>
  );
};

export default JobDetailPage;
