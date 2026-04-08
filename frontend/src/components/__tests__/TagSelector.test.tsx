import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import TagSelector from '../TagSelector';
import { useAppStore } from '../../store';

// Mock the store
vi.mock('../../store', () => ({
  useAppStore: vi.fn(),
}));

describe('TagSelector Component', () => {
  it('renders correctly when loading', () => {
    (useAppStore as unknown as vi.Mock).mockReturnValue({
      tags: null,
      loading: true,
      filters: { skills: [], locations: [], experience: undefined, job_types: [] },
    });

    render(<TagSelector />);
    expect(screen.getByRole('spinbutton')).toBeInTheDocument();
  });

  it('renders all tag categories when data is loaded', () => {
    const mockTags = {
      skills: ['Python', 'Java', '大模型'],
      locations: ['北京', '上海', '杭州'],
      experience: ['1年', '2年', '3年'],
      job_types: ['算法工程师', '大模型工程师'],
    };

    (useAppStore as unknown as vi.Mock).mockReturnValue({
      tags: mockTags,
      loading: false,
      filters: { skills: [], locations: [], experience: undefined, job_types: [] },
    });

    render(<TagSelector />);

    expect(screen.getByText('技能标签')).toBeInTheDocument();
    expect(screen.getByText('工作地点')).toBeInTheDocument();
    expect(screen.getByText('工作经验')).toBeInTheDocument();
    expect(screen.getByText('职位类型')).toBeInTheDocument();

    expect(screen.getByText('Python')).toBeInTheDocument();
    expect(screen.getByText('杭州')).toBeInTheDocument();
    expect(screen.getByText('3年')).toBeInTheDocument();
  });
});
