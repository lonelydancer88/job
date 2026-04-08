import React, { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, List, Tag, Select, Space, Typography, Spin, Empty, Pagination, Progress, Button } from 'antd';
import { OrderedListOutlined, EyeOutlined } from '@ant-design/icons';
import { useAppStore } from '../store';
import { filterJobs } from '../services/api';
import type { JobListItem } from '../types';

const { Title, Text } = Typography;
const { Option } = Select;

const JobList: React.FC = () => {
  const navigate = useNavigate();
  const {
    filters,
    sortBy,
    setSortBy,
    page,
    setPage,
    pageSize,
    jobList,
    totalJobs,
    setJobList,
    loading,
    setLoading,
  } = useAppStore();

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await filterJobs({
        ...filters,
        sort_by: sortBy,
        page,
        page_size: pageSize,
      });
      if (res.code === 0) {
        setJobList(res.data.list, res.data.total);
      }
    } catch (error) {
      console.error('获取职位列表失败:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, sortBy, page, pageSize, setJobList, setLoading]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleJobClick = (job: JobListItem) => {
    navigate(`/job/${job.id}`);
  };

  const renderJobCard = (job: JobListItem) => (
    <List.Item
      key={job.id}
      className="transition-all duration-300 hover:shadow-lg hover:translate-y-[-2px] rounded-xl p-5 bg-white border border-gray-100 mb-3"
    >
      <div className="w-full">
        <div className="flex justify-between items-start mb-2">
          <Title
            level={4}
            className="!mb-0 !text-lg font-medium text-gray-900 cursor-pointer hover:text-blue-600 transition-colors"
            onClick={() => handleJobClick(job)}
          >
            {job.title}
          </Title>
          <Text strong className="text-[#fa6041] text-lg font-bold">
            {job.salary || '面议'}
          </Text>
        </div>

        <div className="flex items-center gap-3 mb-2 text-sm text-gray-600">
          <span>📍 {job.location}</span>
          <span>💼 {job.department}</span>
          <span>⏳ {job.work_experience}</span>
        </div>

        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Progress
              percent={job.match_score}
              size="small"
              showInfo={false}
              strokeColor="#00b38a"
              className="w-24"
            />
            <Text type="secondary" className="text-xs">
              匹配度: {job.match_score}%
            </Text>
          </div>
          <Text type="secondary" className="text-xs">
            🕒 {job.publish_date}
          </Text>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex flex-wrap gap-1">
            {job.matching_keywords.slice(0, 5).map((keyword) => (
              <Tag key={keyword} style={{ background: '#e6fff9', color: '#00b38a', border: 'none', fontSize: '12px', marginRight: '4px', marginBottom: '4px' }}>
                {keyword}
              </Tag>
            ))}
            {job.matching_keywords.length > 5 && (
              <Tag style={{ background: '#f5f7fa', color: '#999', border: 'none', fontSize: '12px' }}>
                +{job.matching_keywords.length - 5}
              </Tag>
            )}
          </div>
          <Button
            type="primary"
            ghost
            size="small"
            onClick={() => handleJobClick(job)}
            icon={<EyeOutlined />}
            style={{ borderRadius: '15px', padding: '0 12px', height: '28px', fontSize: '12px' }}
          >
            查看详情
          </Button>
        </div>
      </div>
    </List.Item>
  );

  return (
    <Card className="h-full flex flex-col" bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '16px' }}>
      {/* 顶部工具栏 */}
      <div className="flex justify-between items-center mb-4 pb-3 border-b border-gray-100">
        <Space>
          <OrderedListOutlined className="text-gray-600" />
          <Text strong className="text-base">
            职位列表 ({totalJobs}个)
          </Text>
        </Space>
        <Space>
          <Text type="secondary" className="text-sm">排序:</Text>
          <Select
            value={sortBy}
            onChange={setSortBy}
            size="small"
            style={{ width: 120 }}
          >
            <Option value="match_score">匹配度优先</Option>
            <Option value="salary">薪资优先</Option>
            <Option value="publish_date">最新优先</Option>
          </Select>
        </Space>
      </div>

      {/* 职位列表 */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <Spin size="large" />
          </div>
        ) : jobList.length === 0 ? (
          <div className="flex justify-center items-center h-64">
            <Empty description="暂无匹配职位，请调整筛选条件" />
          </div>
        ) : (
          <List
            dataSource={jobList}
            renderItem={renderJobCard}
            split={false}
            className="space-y-3"
          />
        )}
      </div>

      {/* 分页 */}
      {totalJobs > 0 && (
        <div className="mt-4 pt-3 border-t border-gray-100 flex justify-center">
          <Pagination
            current={page}
            pageSize={pageSize}
            total={totalJobs}
            onChange={setPage}
            showSizeChanger={false}
            showQuickJumper
            showTotal={(total: number) => `共 ${total} 个职位`}
          />
        </div>
      )}
    </Card>
  );
};

export default JobList;
