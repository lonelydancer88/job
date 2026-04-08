# 单元测试说明

## 后端测试

### 安装测试依赖
```bash
cd backend
source venv/bin/activate
pip install -r requirements-dev.txt
```

### 运行后端测试
```bash
# 运行所有测试
pytest tests/ -v

# 运行单个测试文件
pytest tests/test_database.py -v

# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html
```

### 后端测试用例说明
- `test_database.py` - 数据库层测试：标签获取、多条件筛选功能
- `test_matcher.py` - 匹配算法测试：标签匹配、得分计算、排序逻辑
- `test_api.py` - API接口测试：所有HTTP接口的请求和响应验证

## 前端测试

### 运行前端测试
```bash
cd frontend

# 运行所有测试
npm test

# 启动UI界面运行测试
npm run test:ui

# 生成覆盖率报告
npm run test:coverage
```

### 前端测试用例说明
- `TagSelector.test.tsx` - 标签选择组件测试：渲染、标签展示、交互逻辑
- `JobList.test.tsx` - 职位列表组件测试：空状态、数据渲染、分页功能

## 测试覆盖率要求
- 后端核心逻辑覆盖率 ≥ 80%
- 前端组件覆盖率 ≥ 70%

## CI/CD 集成
可以将测试命令集成到CI/CD流程中，每次提交代码时自动运行测试，确保代码质量。
