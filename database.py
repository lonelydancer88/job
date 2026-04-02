import sqlite3
from typing import Dict, List, Optional
import os

class Database:
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database and create jobs table if not exists"""
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

        conn.commit()
        conn.close()

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
