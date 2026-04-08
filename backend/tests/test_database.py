import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from database import Database

@pytest.fixture
def db():
    """创建数据库连接Fixture"""
    return Database(db_path=":memory:")  # 使用内存数据库进行测试

def test_get_all_tags(db):
    """测试获取所有标签接口"""
    tags = db.get_all_tags()

    assert isinstance(tags, dict)
    assert "skills" in tags
    assert "locations" in tags
    assert "experience" in tags
    assert "job_types" in tags

    assert isinstance(tags["skills"], list)
    assert isinstance(tags["locations"], list)
    assert isinstance(tags["experience"], list)
    assert isinstance(tags["job_types"], list)

def test_filter_jobs_by_locations(db):
    """测试按地点筛选职位"""
    filters = {"locations": ["杭州", "北京"]}
    jobs = db.filter_jobs(filters)

    assert isinstance(jobs, list)
    for job in jobs:
        assert job["location"] in ["杭州", "北京"]

def test_filter_jobs_by_keywords(db):
    """测试按关键词筛选职位"""
    filters = {"keywords": ["Python", "大模型"]}
    jobs = db.filter_jobs(filters)

    assert isinstance(jobs, list)
    for job in jobs:
        content = f"{job['title']} {job['requirements']} {job['responsibilities']}".lower()
        assert "python" in content or "大模型" in content

def test_filter_jobs_combined(db):
    """测试组合条件筛选"""
    filters = {
        "locations": ["杭州"],
        "keywords": ["Python"],
        "max_experience": 3
    }
    jobs = db.filter_jobs(filters)

    assert isinstance(jobs, list)
    for job in jobs:
        assert job["location"] == "杭州"
        content = f"{job['title']} {job['requirements']} {job['responsibilities']}".lower()
        assert "python" in content
