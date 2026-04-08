import { create } from 'zustand';
import type { TagsResponse, JobListItem, FilterRequest, CustomTag } from '../types';

interface AppState {
  // 标签数据
  tags: TagsResponse | null;
  setTags: (tags: TagsResponse) => void;

  // 筛选条件
  filters: Omit<FilterRequest, 'page' | 'page_size' | 'sort_by'>;
  setSkills: (skills: string[]) => void;
  setLocations: (locations: string[]) => void;
  setExperience: (experience: string | undefined) => void;
  setJobTypes: (jobTypes: string[]) => void;
  resetFilters: () => void;

  // 排序和分页
  sortBy: 'match_score' | 'salary' | 'publish_date';
  setSortBy: (sortBy: 'match_score' | 'salary' | 'publish_date') => void;
  page: number;
  setPage: (page: number) => void;
  pageSize: number;

  // 职位数据
  jobList: JobListItem[];
  totalJobs: number;
  setJobList: (jobs: JobListItem[], total: number) => void;


  // 加载状态
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

const initialFilters = {
  skills: [],
  locations: [],
  experience: undefined,
  job_types: [],
};

export const useAppStore = create<AppState>((set) => ({
  // 标签数据
  tags: null,
  setTags: (tags: TagsResponse) => set({ tags }),

  // 筛选条件
  filters: initialFilters,
  setSkills: (skills: string[]) => set((state) => ({ filters: { ...state.filters, skills } })),
  setLocations: (locations: string[]) => set((state) => ({ filters: { ...state.filters, locations } })),
  setExperience: (experience: string | undefined) => set((state) => ({ filters: { ...state.filters, experience } })),
  setJobTypes: (jobTypes: string[]) => set((state) => ({ filters: { ...state.filters, job_types: jobTypes } })),
  resetFilters: () => set({ filters: initialFilters, page: 1 }),

  // 排序和分页
  sortBy: 'match_score',
  setSortBy: (sortBy: 'match_score' | 'salary' | 'publish_date') => set({ sortBy, page: 1 }),
  page: 1,
  setPage: (page: number) => set({ page }),
  pageSize: 20,

  // 职位数据
  jobList: [],
  totalJobs: 0,
  setJobList: (jobs: JobListItem[], total: number) => set({ jobList: jobs, totalJobs: total }),


  // 加载状态
  loading: false,
  setLoading: (loading: boolean) => set({ loading }),
}));
