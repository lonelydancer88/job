import json
import re
import csv
from typing import List, Dict, Optional

class NLPJobFilter:
    def __init__(self, data_path: str = "jobs_dump.jsonl"):
        self.all_jobs: List[Dict] = []
        self.filtered_jobs: List[Dict] = []
        self.filters: Dict = {
            "include_keywords": [],
            "exclude_keywords": [],
            "locations": [],
            "min_experience": None,
            "max_experience": None,
            "exclude_departments": [],
            "include_departments": [],
        }
        self.sort_by = "experience"
        self.sort_reverse = True
        self._load_data(data_path)
        self.filtered_jobs = self.all_jobs.copy()

    def _load_data(self, data_path: str):
        """加载并预处理职位数据"""
        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                job = json.loads(line)
                # 预处理工作经验
                work_exp = job.get("work_experience", "")
                exp_match = re.search(r"工作年限:(\d+)\s*年", work_exp)
                job["experience_years"] = int(exp_match.group(1)) if exp_match else None
                # 统一地点格式
                location = job.get("location", "")
                cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "南京", "武汉", "西安"]
                if len(location) <= 4 and location not in cities:
                    job["actual_location"] = "未注明"
                    job["department_info"] = location
                else:
                    job["actual_location"] = location
                    job["department_info"] = job.get("department", "")
                self.all_jobs.append(job)

    def _apply_filters(self):
        """应用所有筛选条件"""
        result = self.all_jobs.copy()

        # 包含关键词筛选
        if self.filters["include_keywords"]:
            result = [
                job for job in result
                if any(
                    kw.lower() in f"{job.get('title', '')} {job.get('responsibilities', '')} {job.get('requirements', '')}".lower()
                    for kw in self.filters["include_keywords"]
                )
            ]

        # 排除关键词筛选
        if self.filters["exclude_keywords"]:
            result = [
                job for job in result
                if not any(
                    kw.lower() in f"{job.get('title', '')} {job.get('responsibilities', '')} {job.get('requirements', '')} {job.get('department', '')}".lower()
                    for kw in self.filters["exclude_keywords"]
                )
            ]

        # 地点筛选
        if self.filters["locations"]:
            result = [
                job for job in result
                if any(loc.lower() in job["actual_location"].lower() for loc in self.filters["locations"])
            ]

        # 工作经验筛选
        if self.filters["min_experience"] is not None:
            result = [
                job for job in result
                if job["experience_years"] is not None and job["experience_years"] >= self.filters["min_experience"]
            ]

        if self.filters["max_experience"] is not None:
            result = [
                job for job in result
                if job["experience_years"] is not None and job["experience_years"] <= self.filters["max_experience"]
            ]

        # 部门筛选
        if self.filters["include_departments"]:
            result = [
                job for job in result
                if any(dept.lower() in job.get("department", "").lower() for dept in self.filters["include_departments"])
            ]

        if self.filters["exclude_departments"]:
            result = [
                job for job in result
                if not any(dept.lower() in job.get("department", "").lower() for dept in self.filters["exclude_departments"])
            ]

        # 排序
        if self.sort_by == "experience":
            result.sort(
                key=lambda x: x["experience_years"] if x["experience_years"] is not None else -1,
                reverse=self.sort_reverse
            )
        elif self.sort_by == "date":
            result.sort(
                key=lambda x: x.get("publish_date", "") if x.get("publish_date") else "0",
                reverse=self.sort_reverse
            )

        self.filtered_jobs = result

    def _parse_natural_language(self, query: str) -> str:
        """解析自然语言查询，返回执行结果"""
        query = query.strip()
        original_query = query
        query = query.lower()
        response = []

        # 退出指令
        if any(word in query for word in ["退出", "再见", "结束", "quit", "exit"]):
            return "exit"

        # 重置指令
        if any(word in query for word in ["重置", "清空", "reset", "clear"]):
            self.filters = {
                "include_keywords": [],
                "exclude_keywords": [],
                "locations": [],
                "min_experience": None,
                "max_experience": None,
                "exclude_departments": [],
                "include_departments": [],
            }
            self.sort_by = "experience"
            self.sort_reverse = True
            response.append("✅ 已重置所有筛选条件")

        # 导出指令
        export_filename = None
        if any(word in query for word in ["导出", "保存", "export", "save", "csv"]):
            match = re.search(r"导出(?:到|为)?\s*([a-zA-Z0-9_\u4e00-\u9fa5.]+\.csv)", original_query)
            export_filename = match.group(1) if match else "matched_jobs.csv"

        # 显示/查看列表指令
        custom_display = None
        if any(word in query for word in ["显示", "查看", "列表", "show", "list"]):
            match_page = re.search(r"第?(\d+)页", query)
            match_size = re.search(r"每页(\d+)个|显示(\d+)个", query)
            page = int(match_page.group(1)) if match_page else 1
            page_size = int(match_size.group(1) or match_size.group(2)) if match_size else 10
            custom_display = self._get_jobs_display(page_size, page)

        # 排序指令
        if "排序" in query or "排一下" in query:
            if "经验" in query or "工作年限" in query:
                self.sort_by = "experience"
            elif "日期" in query or "时间" in query or "发布" in query:
                self.sort_by = "date"
            self.sort_reverse = not any(word in query for word in ["升序", "从小到大", "从低到高", "正序"])
            sort_type = "工作经验" if self.sort_by == "experience" else "发布日期"
            sort_order = "降序" if self.sort_reverse else "升序"
            response.append(f"📊 已按{sort_type}{sort_order}排序")

        # 解析排除关键词
        exclude_patterns = [
            r"不要([^，。；,\s]+)",
            r"排除([^，。；,\s]+)",
            r"去掉([^，。；,\s]+)",
            r"不包含([^，。；,\s]+)",
        ]
        exclude_kws = []
        for pattern in exclude_patterns:
            matches = re.findall(pattern, original_query)
            for match in matches:
                kws = [kw.strip() for kw in re.split(r"[、,，/]|或者|或", match) if kw.strip() and len(kw.strip()) > 1]
                # 清理关键词后缀
                kws = [re.sub(r"(相关|的|岗位|职位)$", "", kw.strip()) for kw in kws]
                exclude_kws.extend(kws)

        if exclude_kws:
            self.filters["exclude_keywords"].extend(exclude_kws)
            self.filters["exclude_keywords"] = list(set(self.filters["exclude_keywords"]))
            response.append(f"❌ 已添加排除关键词: {', '.join(exclude_kws)}")

        # 解析包含关键词
        include_patterns = [
            r"要([^，。；,\s]+)相关",
            r"包含([^，。；,\s]+)",
            r"找([^，。；,\s]+)的",
            r"关键词([^，。；,\s]+)",
            r"需要([^，。；,\s]+)",
        ]
        include_kws = []
        for pattern in include_patterns:
            matches = re.findall(pattern, original_query)
            for match in matches:
                kws = [kw.strip() for kw in re.split(r"[、,，/]|或者|或", match) if kw.strip() and len(kw.strip()) > 1]
                # 清理关键词后缀
                kws = [re.sub(r"(相关|的|岗位|职位)$", "", kw.strip()) for kw in kws]
                include_kws.extend(kws)

        if include_kws:
            self.filters["include_keywords"].extend(include_kws)
            self.filters["include_keywords"] = list(set(self.filters["include_keywords"]))
            response.append(f"✅ 已添加包含关键词: {', '.join(include_kws)}")

        # 解析地点
        location_patterns = [
            r"地点?([^，。；,\s]+)",
            r"城市([^，。；,\s]+)",
            r"在([^，。；,\s]+)的",
            r"只要([^，。；,\s]+)的",
        ]
        locations = []
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "南京", "武汉", "西安"]
        for pattern in location_patterns:
            matches = re.findall(pattern, original_query)
            for match in matches:
                locs = [loc.strip() for loc in re.split(r"[、,，/]|或者|或", match) if loc.strip() in cities]
                locations.extend(locs)

        # 额外识别城市名称
        for city in cities:
            if city in original_query and city not in locations:
                locations.append(city)

        if locations:
            self.filters["locations"] = list(set(self.filters["locations"] + locations))
            response.append(f"📍 已设置工作地点: {', '.join(locations)}")

        # 解析经验要求
        min_exp = None
        max_exp = None
        exp_match = re.search(r"(\d+)\s*年以上|不少于\s*(\d+)\s*年|最小经验\s*(\d+)\s*年|经验要大于等于\s*(\d+)\s*年", query)
        if exp_match:
            min_exp = int([g for g in exp_match.groups() if g][0])
            self.filters["min_experience"] = min_exp
            response.append(f"⏳ 已设置最小工作经验: {min_exp}年")

        exp_match = re.search(r"(\d+)\s*年以下|不超过\s*(\d+)\s*年|最大经验\s*(\d+)\s*年|经验要小于等于\s*(\d+)\s*年", query)
        if exp_match:
            max_exp = int([g for g in exp_match.groups() if g][0])
            self.filters["max_experience"] = max_exp
            response.append(f"⏳ 已设置最大工作经验: {max_exp}年")

        # 额外匹配直接说关键词的情况：只有当没有解析到任何其他条件时才触发
        has_other_conditions = (
            include_kws or
            exclude_kws or
            locations or
            min_exp is not None or
            max_exp is not None or
            "经验" in query or
            "地点" in query or
            "城市" in query or
            "排序" in query or
            "导出" in query or
            "重置" in query or
            "显示" in query or
            "查看" in query or
            "列表" in query
        )
        if not has_other_conditions:
            kws = [kw.strip() for kw in re.split(r"[、,，/]|或者|或", original_query) if kw.strip() and len(kw.strip()) > 1]
            # 清理关键词后缀
            kws = [re.sub(r"(相关|的|岗位|职位)$", "", kw.strip()) for kw in kws]
            if kws:
                self.filters["include_keywords"].extend(kws)
                self.filters["include_keywords"] = list(set(self.filters["include_keywords"]))
                response.append(f"✅ 已添加包含关键词: {', '.join(kws)}")

        # 应用筛选
        self._apply_filters()

        # 先显示当前查询条件列表
        response.append("\n" + "=" * 70)
        response.append("📋 当前查询条件列表：")
        if self.filters["include_keywords"]:
            response.append(f"  ✅ 包含关键词（任意匹配）: {', '.join(self.filters['include_keywords'])}")
        if self.filters["exclude_keywords"]:
            response.append(f"  ❌ 排除关键词（任意排除）: {', '.join(self.filters['exclude_keywords'])}")
        if self.filters["locations"]:
            response.append(f"  📍 工作地点（任意匹配）: {', '.join(self.filters['locations'])}")
        if self.filters["min_experience"] is not None:
            response.append(f"  ⏳ 最小工作经验: {self.filters['min_experience']}年")
        if self.filters["max_experience"] is not None:
            response.append(f"  ⏳ 最大工作经验: {self.filters['max_experience']}年")
        if self.filters["include_departments"]:
            response.append(f"  🏢 包含部门: {', '.join(self.filters['include_departments'])}")
        if self.filters["exclude_departments"]:
            response.append(f"  🏢 排除部门: {', '.join(self.filters['exclude_departments'])}")
        if not any(self.filters.values()):
            response.append(f"  🎯 无筛选条件，显示所有职位")
        response.append(f"  📊 匹配结果: {len(self.filtered_jobs)} 个职位")
        response.append("=" * 70)

        # 处理导出
        if export_filename:
            self.export_to_csv(export_filename)
            response.append(f"💾 已导出 {len(self.filtered_jobs)} 个职位到 {export_filename}")

        # 显示所有查询到的结果，不分页
        if len(self.filtered_jobs) > 0:
            if custom_display:
                response.append("\n" + custom_display)
            else:
                # 一页显示所有结果
                response.append("\n" + self._get_jobs_display(len(self.filtered_jobs), 1))
        else:
            response.append("\n❌ 没有找到匹配的职位")

        return "\n".join(response)

    def _get_jobs_display(self, page_size: int = 10, page: int = 1) -> str:
        """获取职位列表显示字符串"""
        if not self.filtered_jobs:
            return "❌ 没有匹配的职位"

        total = len(self.filtered_jobs)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = min(start + page_size, total)

        lines = [f"\n📄 职位列表 (第 {page}/{total_pages} 页，共 {total} 个):"]
        lines.append("-" * 120)
        for i, job in enumerate(self.filtered_jobs[start:end], start + 1):
            exp = f"{job['experience_years']}年" if job['experience_years'] is not None else "未注明"
            loc = job['actual_location']
            lines.append(f"{i:3d}. {job['title']:<40} | 经验: {exp:>5} | 地点: {loc:>8} | 部门: {job.get('department', '')}")
            lines.append(f"     链接: {job['url']}")
            if job.get('responsibilities'):
                resp = job['responsibilities'].replace('\n', ' ')[:100] + "..." if len(job['responsibilities']) > 100 else job['responsibilities']
                lines.append(f"     职责: {resp}")
            lines.append("-" * 120)

        return "\n".join(lines)

    def export_to_csv(self, filename: str = "matched_jobs.csv"):
        """导出结果到CSV"""
        if not self.filtered_jobs:
            return
        with open(filename, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["职位名称", "部门", "工作经验", "工作地点", "发布日期", "链接", "职责摘要"])
            for job in self.filtered_jobs:
                exp = f"{job['experience_years']}年" if job['experience_years'] is not None else "未注明"
                resp = job.get('responsibilities', '').replace('\n', ' ')[:200] if job.get('responsibilities') else ""
                writer.writerow([
                    job['title'],
                    job.get('department', ''),
                    exp,
                    job['actual_location'],
                    job.get('publish_date', ''),
                    job['url'],
                    resp
                ])

    def show_current_state(self):
        """显示当前筛选状态"""
        state = ["📋 当前筛选条件:"]
        if self.filters["include_keywords"]:
            state.append(f"  包含关键词: {', '.join(self.filters['include_keywords'])}")
        if self.filters["exclude_keywords"]:
            state.append(f"  排除关键词: {', '.join(self.filters['exclude_keywords'])}")
        if self.filters["locations"]:
            state.append(f"  工作地点: {', '.join(self.filters['locations'])}")
        if self.filters["min_experience"] is not None:
            state.append(f"  最小经验: {self.filters['min_experience']}年")
        if self.filters["max_experience"] is not None:
            state.append(f"  最大经验: {self.filters['max_experience']}年")
        if not any(self.filters.values()):
            state.append("  无筛选条件（显示所有职位）")
        sort_type = "工作经验" if self.sort_by == "experience" else "发布日期"
        sort_order = "降序" if self.sort_reverse else "升序"
        state.append(f"  排序方式: {sort_type}{sort_order}")
        state.append(f"  匹配数量: {len(self.filtered_jobs)} 个职位")
        return "\n".join(state)

def main():
    print("=" * 70)
    print("🎯 自然语言职位筛选系统")
    print("=" * 70)
    print("💡 支持自然语言查询，例如：")
    print("   - 要算法、大模型、对话系统相关的")
    print("   - 要大模型或对话系统的岗位（支持或逻辑）")
    print("   - 不要广告、视觉、多模态的")
    print("   - 只要北京或杭州的，3年以上经验")
    print("   - 按经验从高到低排序")
    print("   - 显示列表，导出到csv")
    print("   - 重置筛选，退出系统")
    print("=" * 70)

    filter = NLPJobFilter()
    print(f"✅ 加载完成，共 {len(filter.all_jobs)} 个职位\n")

    while True:
        query = input("请输入筛选要求：").strip()
        if not query:
            continue

        result = filter._parse_natural_language(query)
        if result == "exit":
            print("\n👋 感谢使用，再见！")
            break

        print("\n" + result + "\n")

if __name__ == "__main__":
    main()
