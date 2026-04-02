# 淘系招聘职位爬取与匹配系统

一个自动爬取淘系招聘网站职位并基于简历智能匹配的工具。

## 功能特性

1. **爬虫模块**：自动爬取 https://talent.taotian.com/ 的职位信息，支持分页、反爬机制、数据去重
2. **简历解析**：支持 PDF/DOCX/TXT 格式简历的文本提取和信息解析
3. **智能匹配**：结合关键词匹配 + TF-IDF 余弦相似度算法，计算职位与简历的匹配度
4. **数据存储**：使用 SQLite 数据库存储职位信息，支持快速查询

## 安装依赖

```bash
pip install playwright pypdf2 python-docx beautifulsoup4 scikit-learn
playwright install chromium
```

## 使用说明

### 1. 爬取职位数据

```bash
# 爬取前10页职位（默认），显示浏览器窗口
python main.py crawl --pages 10

# 无头模式爬取（后台运行，不显示浏览器）
python main.py crawl --pages 20 --headless
```

### 2. 简历匹配

```bash
# 匹配简历，返回Top10相关职位
python main.py match --resume /path/to/your/resume.pdf --top 10

# 支持格式：PDF/DOCX/TXT
python main.py match --resume 我的简历.docx
```

### 3. 查看数据库统计

```bash
python main.py stats
```

## 项目结构

```
.
├── main.py              # 主入口文件
├── spider.py            # 爬虫模块
├── database.py          # 数据库操作
├── resume_parser.py     # 简历解析模块
├── matcher.py           # 匹配算法模块
├── jobs.db              # SQLite数据库文件（自动生成）
└── README.md            # 项目说明
```

## 匹配算法说明

MVP版本采用加权打分机制：
- 40% 关键词匹配：统计简历中技能关键词在职位要求中的出现频率
- 60% 语义相似度：使用TF-IDF + 余弦相似度计算简历文本与职位文本的相似度

后续可扩展接入大模型Embedding API实现更精准的语义匹配。

## 注意事项

1. 爬取时会自动添加随机延迟，避免触发网站反爬机制
2. 建议不要一次性爬取过多页面，合理控制爬取频率
3. 简历解析功能对非标准格式的简历可能存在提取不全的情况
4. 首次使用请先运行爬取命令获取职位数据，再进行匹配

## 后续优化方向

- 接入大模型Embedding API提升匹配准确率
- 添加Web界面，支持可视化操作
- 支持更多招聘网站的爬取
- 添加职位更新监控功能
- 支持自定义匹配规则和权重配置
