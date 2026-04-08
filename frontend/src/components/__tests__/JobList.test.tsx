import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import JobList from '../JobList';
import { useAppStore } from '../../store';

// Mock the store
vi.mock('../../store', () => ({
  useAppStore: vi.fn(),
}));

// Mock API calls
vi.mock('../../services/api', () => ({
  filterJobs: vi.fn(),
  getJobDetail: vi.fn(),
}));

describe('JobList Component', () => {
  it('renders empty state when no jobs', () => {
    (useAppStore as unknown as vi.Mock).mockReturnValue({
      jobList: [],
      totalJobs: 0,
      loading: false,
      filters: { skills: [], locations: [], experience: undefined, job_types: [] },
      sortBy: 'match_score',
      page: 1,
      pageSize: 20,
    });

    render(<JobList />);
    expect(screen.getByText('暂无匹配职位，请调整筛选条件')).toBeInTheDocument();
  });

  it('renders job list correctly', () => {
    const mockJobs = [
      {
        id: 1,
        title: '算法工程师',
        salary: '20-30K',
        location: '杭州',
        work_experience: '3年',
        match_score: 95.5,
        matching_keywords: ['Python', '大模型'],
      },
    ];

    (useAppStore as unknown as vi.Mock).mockReturnValue({
      jobList: mockJobs,
      totalJobs: 1,
      loading: false,
      filters: { skills: [], locations: [], experience: undefined, job_types: [] },
      sortBy: 'match_score',
      page: 1,
      pageSize: 20,
    });

    render(<JobList />);

    expect(screen.getByText('算法工程师')).toBeInTheDocument();
    expect(screen.getByText('20-30K')).toBeInTheDocument();
    expect(screen.getByText('杭州')).toBeInTheDocument();
    expect(screen.getByText('匹配度: 95.5%')).toBeInTheDocument();
    expect(screen.getByText('Python')).toBeInTheDocument();
  });
});
