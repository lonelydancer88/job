import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_tags_api():
    """测试获取标签API"""
    response = client.get("/api/v1/tags")
    assert response.status_code == 200

    data = response.json()
    assert data["code"] == 0
    assert "data" in data
    assert "skills" in data["data"]
    assert "locations" in data["data"]

def test_filter_jobs_api():
    """测试职位筛选API"""
    request_data = {
        "skills": ["Python", "大模型"],
        "locations": ["杭州"],
        "experience": "3年",
        "job_types": [],
        "sort_by": "match_score",
        "page": 1,
        "page_size": 10
    }

    response = client.post("/api/v1/jobs/filter", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["code"] == 0
    assert "data" in data
    assert "list" in data["data"]
    assert "total" in data["data"]
    assert data["data"]["page"] == 1
    assert data["data"]["page_size"] == 10

def test_filter_jobs_api_pagination():
    """测试分页功能"""
    request_data = {
        "skills": [],
        "locations": [],
        "experience": None,
        "job_types": [],
        "sort_by": "match_score",
        "page": 2,
        "page_size": 5
    }

    response = client.post("/api/v1/jobs/filter", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["data"]["page"] == 2
    assert len(data["data"]["list"]) <= 5

def test_get_job_detail_api():
    """测试获取职位详情API"""
    # 先获取一个职位ID
    filter_response = client.post("/api/v1/jobs/filter", json={
        "skills": [], "locations": [], "job_types": [], "page": 1, "page_size": 1
    })
    job_list = filter_response.json()["data"]["list"]

    if job_list:
        job_id = job_list[0]["id"]
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == job_id
        assert "title" in data["data"]
        assert "requirements" in data["data"]

def test_get_stats_api():
    """测试统计信息API"""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200

    data = response.json()
    assert data["code"] == 0
    assert "total_jobs" in data["data"]
    assert "skill_count" in data["data"]
    assert data["data"]["total_jobs"] >= 0
