import axios from 'axios';
import type { ApiResponse, TagsResponse, FilterRequest, FilterResponse, Job, StatsResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

import type { InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

// 请求拦截器
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data;
  },
  (error: AxiosError) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// 获取所有标签
export const getTags = async (): Promise<ApiResponse<TagsResponse>> => {
  return api.get('/tags');
};

// 筛选职位
export const filterJobs = async (params: FilterRequest): Promise<ApiResponse<FilterResponse>> => {
  return api.post('/jobs/filter', params);
};

// 获取职位详情
export const getJobDetail = async (jobId: number): Promise<ApiResponse<Job>> => {
  return api.get(`/jobs/${jobId}`);
};

// 获取统计信息
export const getStats = async (): Promise<ApiResponse<StatsResponse>> => {
  return api.get('/stats');
};

// 添加自定义标签
export const addCustomTag = async (name: string, type: string = 'skill'): Promise<ApiResponse> => {
  return api.post('/tags/custom', { name, type });
};

// 删除自定义标签
export const deleteCustomTag = async (tagId: number): Promise<ApiResponse> => {
  return api.delete(`/tags/custom/${tagId}`);
};

export default api;
