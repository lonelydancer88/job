# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 项目概述
淘天招聘职位爬取与智能筛选系统，包含三大核心功能：
1. 招聘网站爬虫（淘天集团官网）
2. 自然语言交互式职位筛选
3. BOSS直聘风格Web UI智能职位推荐

## 📋 常用命令

### 基础开发命令
```bash
# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 爬取职位数据
python main.py crawl                   # 爬取前10页研发类职位
python main.py crawl --pages 20        # 爬取20页
python main.py crawl --headless        # 无头模式运行
python main.py crawl --all-jobs        # 爬取所有类别职位

# 查看数据库统计
python main.py stats

# 自然语言筛选
python job_filter_nlp.py

# 导出数据到JSONL
python dump_jobs.py
```

### Web UI开发命令
```bash
# 一键启动前后端开发服务
./run.sh

# 单独启动后端API服务
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 单独启动前端开发服务
cd frontend && npm run dev

# 构建前端生产版本
cd frontend && npm run build
```

### Docker部署命令
```bash
# 构建并启动所有服务
docker-compose up -d --build

# 停止服务
docker-compose down

# 查看服务日志
docker-compose logs -f
```

## 🏗️ 系统架构

### 整体架构
```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   前端Web UI     │    │   后端API服务    │    │   数据层         │
│  (React + TS)    │◄──►│  (FastAPI)       │◄──►│  SQLite数据库    │
└──────────────────┘    └──────────────────┘    └──────────────────┘
          │                     │
          ▼                     ▼
┌──────────────────┐    ┌──────────────────┐
│  标签选择组件     │    │  匹配算法模块     │
│  职位列表组件     │    │  数据库操作模块   │
│  职位详情组件     │    │  爬虫模块         │
└──────────────────┘    └──────────────────┘
```

### 核心模块职责

#### 后端模块
| 模块 | 职责 | 关键文件 |
|------|------|----------|
| 爬虫模块 | 爬取淘天招聘官网职位数据 | `spider.py` |
| 数据库模块 | SQLite数据存储与查询 | `database.py` |
| 匹配算法 | 职位与标签/简历的匹配计算 | `matcher_simple.py` |
| NLP筛选 | 自然语言查询解析与筛选 | `job_filter_nlp.py` |
| API服务 | 提供Web UI后端接口 | `backend/main.py` |

#### 前端模块
| 模块 | 职责 | 路径 |
|------|------|------|
| 标签选择区 | 多维度标签勾选与筛选 | `frontend/src/components/TagPanel/` |
| 职位列表区 | 职位卡片展示、排序、分页 | `frontend/src/components/JobList/` |
| 职位详情区 | 职位详情展示与匹配分析 | `frontend/src/components/JobDetail/` |
| 状态管理 | 全局状态管理 | `frontend/src/store/` |

### 匹配算法核心逻辑
1. **关键词匹配 (50%权重)**：用户勾选的标签与职位文本的匹配率
2. **文本相似度 (50%权重)**：Jaccard相似度计算，基于词频统计
3. **筛选逻辑**：同类型标签OR逻辑，不同类型标签AND逻辑
4. **结果排序**：按综合匹配度降序排列

## 🔗 服务访问地址
- 前端开发环境: http://localhost:3000
- 后端API文档: http://localhost:8000/docs
- Docker部署访问: http://localhost

## 📁 关键文件路径
```
/Users/hpl/vibecoding/job/
├── main.py                 # 命令行主入口
├── spider.py               # 爬虫模块
├── database.py             # 数据库操作
├── matcher_simple.py       # 匹配算法
├── job_filter_nlp.py       # NLP筛选
├── backend/
│   └── main.py             # FastAPI后端入口
├── frontend/
│   └── src/                # React前端源码
├── docker-compose.yml      # Docker部署配置
└── run.sh                  # 一键启动脚本
```

## ⚠️ 重要注意事项
1. 首次使用必须先运行爬虫爬取数据，否则Web UI和筛选功能无数据
2. 匹配算法直接复用`matcher_simple.py`的逻辑，修改时需保持前后端一致性
3. 标签数据从数据库职位信息中动态统计，不需要硬编码
4. 所有职位数据存储在`jobs.db`SQLite文件中，可直接备份和迁移