export interface CustomTag {
  id: number;
  name: string;
  type: string;
  is_custom: boolean;
  created_at: string;
}

export interface TagsResponse {
  skills: string[];
  locations: string[];
  experience: string[];
  job_types: string[];
  custom_skills?: CustomTag[];
}

export interface Job {
  id: number;
  job_id: string;
  title: string;
  department: string;
  salary: string;
  location: string;
  work_experience: string;
  responsibilities: string;
  requirements: string;
  publish_date: string;
  url: string;
  created_at: string;
}

export interface JobMatchResult {
  job: Job;
  total_score: number;
  keyword_score: number;
  similarity_score: number;
  matching_keywords: string[];
}

export interface JobListItem {
  id: number;
  job_id: string;
  title: string;
  department: string;
  salary: string;
  location: string;
  work_experience: string;
  publish_date: string;
  url: string;
  match_score: number;
  keyword_score: number;
  similarity_score: number;
  matching_keywords: string[];
}

export interface FilterRequest {
  skills: string[];
  locations: string[];
  experience?: string;
  job_types: string[];
  sort_by: 'match_score' | 'salary' | 'publish_date';
  page: number;
  page_size: number;
}

export interface FilterResponse {
  list: JobListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface StatsResponse {
  total_jobs: number;
  skill_count: number;
  location_count: number;
  job_type_count: number;
  experience_count: number;
}

export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}
