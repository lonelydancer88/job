from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from matcher_simple import SimpleJobMatcher

app = FastAPI(title="BOSS直聘风格职位推荐API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库和匹配器（使用项目根目录的数据库文件）
import os
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jobs.db")
db = Database(db_path=db_path)
matcher = SimpleJobMatcher()
matcher.db = db  # 更新匹配器的数据库实例

# Pydantic模型
class FilterRequest(BaseModel):
    skills: List[str] = []
    locations: List[str] = []
    experience: Optional[str] = None
    job_types: List[str] = []
    sort_by: str = "match_score"  # match_score, salary, publish_date
    page: int = 1
    page_size: int = 20

@app.get("/api/v1/tags", summary="获取所有可用标签")
async def get_tags():
    """获取所有可用的标签，包括技能、地点、工作经验、职位类型"""
    tags = db.get_all_tags()
    return {
        "code": 0,
        "message": "success",
        "data": tags
    }

@app.post("/api/v1/jobs/filter", summary="根据标签筛选职位")
async def filter_jobs(request: FilterRequest):
    """根据用户选择的标签筛选并匹配职位"""
    try:
        # 解析经验要求
        max_experience = None
        if request.experience:
            if request.experience == "5年及以上":
                max_experience = 5
            else:
                import re
                match = re.search(r'(\d+)', request.experience)
                if match:
                    max_experience = int(match.group(1))

        # 准备标签参数
        tags = {
            "skills": request.skills,
            "locations": request.locations,
            "max_experience": max_experience,
            "job_types": request.job_types
        }

        # 匹配职位
        results = matcher.match_jobs_by_tags(tags, top_n=200)

        # 排序
        if request.sort_by == "salary":
            # TODO: 实现按薪资排序，需要先解析薪资字段
            pass
        elif request.sort_by == "publish_date":
            results.sort(key=lambda x: x["job"].get("publish_date", ""), reverse=True)
        else:
            # 默认按匹配度排序
            pass

        # 分页
        total = len(results)
        start = (request.page - 1) * request.page_size
        end = start + request.page_size
        paginated_results = results[start:end]

        # 格式化返回结果
        jobs_data = []
        for result in paginated_results:
            job = result["job"]
            jobs_data.append({
                "id": job["id"],
                "job_id": job["job_id"],
                "title": job["title"],
                "department": job["department"],
                "salary": job["salary"],
                "location": job["location"],
                "work_experience": job["work_experience"],
                "publish_date": job["publish_date"],
                "url": job["url"],
                "match_score": result["total_score"],
                "keyword_score": result["keyword_score"],
                "similarity_score": result["similarity_score"],
                "matching_keywords": result["matching_keywords"]
            })

        return {
            "code": 0,
            "message": "success",
            "data": {
                "list": jobs_data,
                "total": total,
                "page": request.page,
                "page_size": request.page_size,
                "total_pages": (total + request.page_size - 1) // request.page_size
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"筛选失败: {str(e)}")

@app.get("/api/v1/jobs/{job_id}", summary="获取职位详情")
async def get_job_detail(job_id: int):
    """根据职位ID获取职位详细信息"""
    jobs = db.get_all_jobs()
    for job in jobs:
        if job["id"] == job_id:
            return {
                "code": 0,
                "message": "success",
                "data": job
            }
    raise HTTPException(status_code=404, detail="职位不存在")

@app.get("/api/v1/stats", summary="获取系统统计信息")
async def get_stats():
    """获取系统统计信息，包括职位总数、标签数量等"""
    total_jobs = db.get_job_count()
    tags = db.get_all_tags()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "total_jobs": total_jobs,
            "skill_count": len(tags["skills"]),
            "location_count": len(tags["locations"]),
            "job_type_count": len(tags["job_types"]),
            "experience_count": len(tags["experience"])
        }
    }

class TagCreateRequest(BaseModel):
    name: str
    type: str = "skill"

class TagDeleteRequest(BaseModel):
    id: int

@app.post("/api/v1/tags/custom", summary="添加自定义标签")
async def add_custom_tag(request: TagCreateRequest):
    """添加自定义技能标签"""
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="标签名称不能为空")

    success = db.add_custom_tag(request.name.strip(), request.type)
    if success:
        return {"code": 0, "message": "标签添加成功"}
    else:
        raise HTTPException(status_code=400, detail="标签已存在")

@app.delete("/api/v1/tags/custom/{tag_id}", summary="删除自定义标签")
async def delete_custom_tag(tag_id: int):
    """删除自定义技能标签"""
    success = db.delete_custom_tag(tag_id)
    if success:
        return {"code": 0, "message": "标签删除成功"}
    else:
        raise HTTPException(status_code=404, detail="标签不存在或不是自定义标签")

@app.get("/", summary="API根路径")
async def root():
    return {"message": "BOSS直聘风格职位推荐API服务运行中"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)