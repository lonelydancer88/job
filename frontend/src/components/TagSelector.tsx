import React, { useEffect, useState } from 'react';
import { Card, Checkbox, Button, Space, Typography, Divider, Spin, Empty, Input, message, Popconfirm } from 'antd';
import { FilterOutlined, ReloadOutlined, SearchOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useAppStore } from '../store';
import { getTags, addCustomTag, deleteCustomTag } from '../services/api';
import type { CustomTag } from '../types';

const { Title, Text } = Typography;
const CheckboxGroup = Checkbox.Group;

const TagSelector: React.FC = () => {
  const {
    tags,
    setTags,
    filters,
    setSkills,
    setLocations,
    setExperience,
    setJobTypes,
    resetFilters,
    loading,
    setLoading,
  } = useAppStore();

  const [newTag, setNewTag] = useState('');
  const [addingTag, setAddingTag] = useState(false);
  const [customTags, setCustomTags] = useState<CustomTag[]>([]);

  useEffect(() => {
    fetchTags();
  }, [setTags, setLoading]);

  const fetchTags = async () => {
    setLoading(true);
    try {
      const res = await getTags();
      if (res.code === 0) {
        setTags(res.data);
        setCustomTags(res.data.custom_skills || []);
      }
    } catch (error) {
      console.error('获取标签失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTag = async () => {
    if (!newTag.trim()) {
      message.warning('请输入标签名称');
      return;
    }

    try {
      await addCustomTag(newTag.trim());
      message.success('标签添加成功');
      setNewTag('');
      setAddingTag(false);
      // 重新获取标签列表
      await fetchTags();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '添加失败');
    }
  };

  const handleDeleteTag = async (tagId: number, tagName: string) => {
    try {
      await deleteCustomTag(tagId);
      message.success('标签删除成功');
      // 如果删除的标签正在被使用，移除它
      if (filters.skills.includes(tagName)) {
        setSkills(filters.skills.filter(s => s !== tagName));
      }
      // 重新获取标签列表
      await fetchTags();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  if (loading && !tags) {
    return (
      <Card className="h-full">
        <div className="flex justify-center items-center h-64">
          <Spin size="large" />
        </div>
      </Card>
    );
  }

  if (!tags) {
    return (
      <Card className="h-full">
        <Empty description="暂无标签数据" />
      </Card>
    );
  }

  return (
    <Card
      className="h-full overflow-y-auto"
      title={
        <Space>
          <FilterOutlined />
          <span>筛选条件</span>
        </Space>
      }
      extra={
        <Button
          type="text"
          icon={<ReloadOutlined />}
          onClick={resetFilters}
          size="small"
        >
          重置
        </Button>
      }
    >
      {/* 技能标签 */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-3">
          <Title level={5} className="!mb-0">
            <SearchOutlined className="mr-2" />
            技能标签
          </Title>
          <Button
            type="text"
            icon={<PlusOutlined />}
            size="small"
            onClick={() => setAddingTag(!addingTag)}
          >
            添加
          </Button>
        </div>

        {/* 添加标签输入框 */}
        {addingTag && (
          <div className="mb-3 flex gap-2">
            <Input
              size="small"
              placeholder="输入新标签"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onPressEnter={handleAddTag}
            />
            <Button size="small" type="primary" onClick={handleAddTag}>
              确定
            </Button>
            <Button size="small" onClick={() => { setAddingTag(false); setNewTag(''); }}>
              取消
            </Button>
          </div>
        )}

        {/* 标签列表 */}
        <div className="space-y-1">
          <CheckboxGroup
            value={filters.skills}
            onChange={setSkills}
            className="flex flex-wrap gap-2"
          >
            {tags?.skills.map((skill: string) => {
              const customTag = customTags.find(t => t.name === skill);
              return (
                <div key={skill} className="flex items-center gap-1">
                  <Checkbox value={skill} style={{ marginBottom: '6px' }}>{skill}</Checkbox>
                  {customTag && (
                    <Popconfirm
                      title="确定删除这个标签？"
                      onConfirm={() => handleDeleteTag(customTag.id, skill)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <DeleteOutlined
                        className="text-xs text-gray-400 hover:text-red-500 cursor-pointer"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </Popconfirm>
                  )}
                </div>
              );
            })}
          </CheckboxGroup>
        </div>
      </div>

      <Divider className="my-4" />

      {/* 地点标签 */}
      <div className="mb-6">
        <Title level={5} className="mb-3">
          🏙️ 工作地点
        </Title>
        <CheckboxGroup
          options={tags.locations.map((loc: string) => ({ label: loc, value: loc }))}
          value={filters.locations}
          onChange={setLocations}
          className="flex flex-wrap gap-2"
        />
      </div>

      <Divider className="my-4" />

      {/* 工作经验 */}
      <div className="mb-6">
        <Title level={5} className="mb-3">
          ⏳ 工作经验
        </Title>
        <CheckboxGroup
          options={tags.experience.map((exp: string) => ({ label: exp, value: exp }))}
          value={filters.experience ? [filters.experience] : []}
          onChange={(values: string[]) => setExperience(values[0])}
          className="flex flex-col gap-2"
        />
      </div>

      <Divider className="my-4" />

      {/* 职位类型 */}
      <div className="mb-6">
        <Title level={5} className="mb-3">
          💼 职位类型
        </Title>
        <CheckboxGroup
          options={tags.job_types.map((jt: string) => ({ label: jt, value: jt }))}
          value={filters.job_types}
          onChange={setJobTypes}
          className="flex flex-wrap gap-2"
        />
      </div>

      <Divider className="my-4" />

      <div className="text-center text-gray-500 text-sm">
        <Text type="secondary">
          提示：同类型标签为OR逻辑，不同类型标签为AND逻辑
        </Text>
      </div>
    </Card>
  );
};

export default TagSelector;
