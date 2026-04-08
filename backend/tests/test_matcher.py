import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from matcher_simple import SimpleJobMatcher

@pytest.fixture
def matcher():
    """创建匹配器Fixture"""
    return SimpleJobMatcher()

def test_match_jobs_by_tags_empty(matcher):
    """测试空标签匹配"""
    results = matcher.match_jobs_by_tags({})
    assert isinstance(results, list)

def test_match_jobs_by_skills(matcher):
    """测试按技能标签匹配"""
    tags = {"skills": ["Python", "机器学习"]}
    results = matcher.match_jobs_by_tags(tags)

    assert isinstance(results, list)
    for result in results:
        assert "total_score" in result
        assert "matching_keywords" in result
        assert result["total_score"] >= 0
        assert result["total_score"] <= 100

def test_match_jobs_by_multiple_tags(matcher):
    """测试多维度标签匹配"""
    tags = {
        "skills": ["Python", "大模型"],
        "locations": ["杭州"],
        "max_experience": 3
    }
    results = matcher.match_jobs_by_tags(tags, top_n=10)

    assert isinstance(results, list)
    assert len(results) <= 10

    # 验证匹配度排序是降序的
    scores = [r["total_score"] for r in results]
    assert scores == sorted(scores, reverse=True)

def test_match_score_calculation(matcher):
    """测试匹配度计算逻辑"""
    tags = {"skills": ["Python", "大模型", "机器学习"]}
    results = matcher.match_jobs_by_tags(tags)

    if results:
        top_result = results[0]
        # 关键词匹配数量应该不超过总标签数量
        assert len(top_result["matching_keywords"]) <= 3
        # 总分应该是关键词得分和相似度得分的平均值
        expected_score = (top_result["keyword_score"] + top_result["similarity_score"]) / 2
        assert abs(top_result["total_score"] - expected_score) < 0.1
