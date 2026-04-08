import sqlite3
from typing import Dict, List, Optional
import os

class Database:
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database and create tables if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id VARCHAR(64) UNIQUE,
            title VARCHAR(255),
            department VARCHAR(255),
            salary VARCHAR(100),
            location VARCHAR(100),
            work_experience VARCHAR(100),
            responsibilities TEXT,
            requirements TEXT,
            publish_date VARCHAR(50),
            url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        # 兼容旧表，添加work_experience字段
        try:
            cursor.execute('ALTER TABLE jobs ADD COLUMN work_experience VARCHAR(100)')
        except:
            # 字段已存在
            pass

        # 创建自定义标签表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) UNIQUE NOT NULL,
            type VARCHAR(50) DEFAULT 'skill',
            is_custom BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
        conn.close()

    def add_custom_tag(self, name: str, tag_type: str = 'skill') -> bool:
        """Add a custom tag"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO custom_tags (name, type) VALUES (?, ?)',
                (name.strip(), tag_type)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # 标签已存在
            return False

    def delete_custom_tag(self, tag_id: int) -> bool:
        """Delete a custom tag"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM custom_tags WHERE id = ? AND is_custom = 1', (tag_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def get_custom_tags(self, tag_type: str = 'skill') -> List[Dict]:
        """Get all custom tags, sorted by creation time ascending (newest last)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM custom_tags WHERE type = ? ORDER BY created_at ASC',
            (tag_type,)
        )
        tags = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tags

    def insert_job(self, job: Dict) -> bool:
        """Insert a job into database, return False if duplicate"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO jobs (job_id, title, department, salary, location, work_experience, responsibilities, requirements, publish_date, url)
            VALUES (:job_id, :title, :department, :salary, :location, :work_experience, :responsibilities, :requirements, :publish_date, :url)
            ''', job)

            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Duplicate job_id
            conn.close()
            return False

    def job_exists(self, job_id: str) -> bool:
        """Check if job already exists in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT 1 FROM jobs WHERE job_id = ?', (job_id,))
        exists = cursor.fetchone() is not None

        conn.close()
        return exists

    def get_all_jobs(self) -> List[Dict]:
        """Get all jobs from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM jobs ORDER BY created_at DESC')
        jobs = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return jobs

    def get_job_count(self) -> int:
        """Get total number of jobs in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM jobs')
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def get_all_tags(self) -> Dict:
        """Get all available tags from existing jobs"""
        import re
        from collections import Counter

        jobs = self.get_all_jobs()
        if not jobs:
            return {
                "skills": [],
                "locations": [],
                "experience": [],
                "job_types": []
            }

        # 提取地点标签（过滤非城市的无效地点）
        valid_cities = {"北京", "上海", "广州", "深圳", "杭州", "成都", "南京", "武汉", "西安",
                       "重庆", "苏州", "郑州", "青岛", "厦门", "长沙", "天津", "合肥",
                       "济南", "福州", "东莞", "沈阳", "宁波", "昆明", "哈尔滨", "贵阳"}
        locations = []
        import re
        for job in jobs:
            loc = job.get('location', '').strip()
            if not loc:
                continue
            # 处理特殊字符和分隔符
            loc = loc.replace('*', '').replace('、', '/').replace(' ', '')
            # 拆分多地点（支持/分隔）
            loc_parts = loc.split('/')
            for part in loc_parts:
                # 清理特殊字符，只保留中文
                clean_part = re.sub(r'[^\u4e00-\u9fff]', '', part)
                if not clean_part:
                    continue
                # 检查是否是有效城市
                for city in valid_cities:
                    if city in clean_part:
                        locations.append(city)
                        break
        location_counter = Counter(locations)
        top_locations = [loc for loc, cnt in location_counter.most_common(20)]

        # 提取工作经验标签
        experience_pattern = re.compile(r'(\d+)\s*年')
        experiences = []
        for job in jobs:
            exp_text = job.get('work_experience', '')
            match = experience_pattern.search(exp_text)
            if match:
                exp_year = int(match.group(1))
                if exp_year <= 5:
                    experiences.append(f"{exp_year}年")
                else:
                    experiences.append("5年及以上")
        exp_counter = Counter(experiences)
        sorted_experience = sorted(exp_counter.keys(), key=lambda x: int(x.replace('年', '').replace('及以上', '')))

        # 提取职位类型标签
        job_titles = [job.get('title', '') for job in jobs if job.get('title')]
        job_type_counter = Counter()
        common_job_types = ["算法工程师", "大模型算法工程师", "广告算法工程师", "推荐算法工程师",
                           "NLP算法工程师", "机器学习工程师", "深度学习工程师", "CV算法工程师"]
        for title in job_titles:
            for job_type in common_job_types:
                if job_type in title:
                    job_type_counter[job_type] += 1
                    break
        top_job_types = [jt for jt, cnt in job_type_counter.most_common(20)]

        # 提取技能标签（从职位要求中提取高频技能）
        skill_keywords = ["C", "人工智能", "ICML", "SFT", "机器学习", "ICLR", "Java", "NeurIPS",
                         "Agent", "ACL", "推荐", "RL", "强化学习", "RLHF", "PyTorch",
                         "TensorFlow", "LLM", "Python", "RAG", "广告"]
        skill_counter = Counter()
        for job in jobs:
            req_text = job.get('requirements', '').lower() + job.get('title', '').lower()
            for skill in skill_keywords:
                if skill.lower() in req_text:
                    skill_counter[skill] += 1
        top_skills = [skill for skill, cnt in skill_counter.most_common(20) if cnt > 0]

        # 合并自定义标签
        custom_tags = self.get_custom_tags('skill')
        for tag in custom_tags:
            if tag['name'] not in top_skills:
                top_skills.append(tag['name'])

        return {
            "skills": top_skills,
            "locations": top_locations,
            "experience": sorted_experience,
            "job_types": top_job_types,
            "custom_skills": custom_tags
        }

    def filter_jobs(self, filters: Dict = None) -> List[Dict]:
        """Filter jobs by various criteria"""
        if filters is None:
            filters = {}

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM jobs WHERE 1=1'
        params = []

        # 地点筛选
        if filters.get('locations'):
            placeholders = ', '.join(['?' for _ in filters['locations']])
            query += f' AND location IN ({placeholders})'
            params.extend(filters['locations'])

        # 工作经验筛选：精确匹配指定年限
        if filters.get('max_experience') is not None:
            exp = filters['max_experience']
            query += " AND work_experience LIKE ?"
            params.append(f"%{exp} %年%")

        # 关键词筛选（技能、职位类型）
        if filters.get('keywords'):
            keyword_conditions = []
            for keyword in filters['keywords']:
                keyword_conditions.append("(title LIKE ? OR requirements LIKE ? OR responsibilities LIKE ?)")
                params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
            if keyword_conditions:
                query += ' AND (' + ' OR '.join(keyword_conditions) + ')'

        query += ' ORDER BY created_at DESC'

        cursor.execute(query, params)
        jobs = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return jobs
