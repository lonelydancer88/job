import asyncio
import random
import re
import sys
from typing import Dict, List, Optional
from urllib.parse import urljoin
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from database import Database
import time

class TaotianSpider:
    def __init__(self, headless: bool = True, delay_range: tuple = (2, 5)):
        self.base_url = "https://talent.taotian.com/"
        self.headless = headless
        self.delay_range = delay_range
        self.db = Database()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.total_jobs: int = 0
        self.total_pages: int = 0

    async def init_browser(self):
        """Initialize browser instance"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )

    async def random_delay(self):
        """Random delay to avoid anti-scraping"""
        delay = random.uniform(*self.delay_range)
        await asyncio.sleep(delay)

    def extract_job_id(self, url: str) -> Optional[str]:
        """Extract job id from job detail url"""
        # 匹配两种格式：/position/123 或者 positionId=123
        match = re.search(r'/position/(\d+)', url)
        if match:
            return match.group(1)
        match = re.search(r'positionId[=:](\d+)', url)
        if match:
            return match.group(1)
        return None

    async def parse_job_detail(self, job_url: str, reuse_page: bool = False, page = None) -> Optional[Dict]:
        """Parse job detail page and extract job information"""
        # 使用传入的page，否则用self.page
        p = page if page else self.page
        try:
            if not reuse_page and not page:
                await p.goto(job_url, timeout=60000, wait_until="domcontentloaded")
                await p.wait_for_timeout(2000)

            job = {
                "url": job_url,
                "job_id": self.extract_job_id(job_url),
                "title": "",
                "department": "",
                "salary": "",
                "location": "",
                "work_experience": "",
                "responsibilities": "",
                "requirements": "",
                "publish_date": ""
            }

            # 直接用JavaScript提取页面所有内容，适配动态渲染
            page_data = await p.evaluate('''() => {
                const data = {
                    title: '',
                    department: '',
                    salary: '',
                    location: '',
                    work_experience: '',
                    responsibilities: '',
                    requirements: '',
                    publish_date: ''
                };

                // 1. 提取标题和基本信息
                // 优先从页面title获取（格式：营销平台及市场部-规则管理-杭州）
                const pageTitle = document.title;
                if (pageTitle) {
                    const titleParts = pageTitle.split('-');
                    // 职位名称是倒数第二部分
                    if (titleParts.length >= 3) {
                        data.title = titleParts[titleParts.length - 2].trim();
                        data.department = titleParts.slice(0, titleParts.length - 2).join('-').trim();
                        data.location = titleParts[titleParts.length - 1].trim();
                    } else {
                        data.title = pageTitle.trim();
                    }
                }
                // 兜底用h1/h2
                if (!data.title) {
                    const titleElement = document.querySelector('h1') || document.querySelector('h2');
                    if (titleElement) {
                        data.title = titleElement.textContent.trim();
                    }
                }

                // 提取页面顶部的日期和地点（格式：更新于 2026-04-02 杭州）
                const headerElements = Array.from(document.querySelectorAll('div')).filter(el =>
                    el.textContent.includes('更新于')
                );
                for (const el of headerElements) {
                    const text = el.textContent.trim();
                    // 提取日期
                    const dateMatch = text.match(/更新于\\s*(\\d{4}-\\d{2}-\\d{2})/);
                    if (dateMatch) data.publish_date = dateMatch[1];
                    // 提取地点（杭州、北京、上海等城市名）
                    const cities = ['杭州', '北京', '上海', '深圳', '广州', '成都', '重庆', '南京', '武汉', '西安', '苏州', '中国香港'];
                    for (const city of cities) {
                        if (text.includes(city)) {
                            if (!data.location) data.location = city;
                            break;
                        }
                    }
                    if (data.publish_date && data.location) break;
                }

                // 兜底找地点
                if (!data.location) {
                    const allText = document.body.innerText;
                    const cities = ['杭州', '北京', '上海', '深圳', '广州', '成都', '重庆', '南京', '武汉', '西安', '苏州', '中国香港'];
                    for (const city of cities) {
                        if (allText.includes(` ${city}`) || allText.includes(`|${city}`) || allText.includes(`：${city}`)) {
                            data.location = city;
                            break;
                        }
                    }
                }

                // 2. 提取基础信息区域（所属部门、学历、工作年限）
                const basicInfoElements = Array.from(document.querySelectorAll('div[role="gridcell"], div.info-item, span.info, div.job-info'));
                basicInfoElements.forEach(el => {
                    const text = el.textContent.trim();
                    if (text.includes('所属部门:') || text.includes('部门：')) {
                        // 如果pageTitle里已经提取了部门，这里就补充完整
                        const dept = text.replace('所属部门:', '').replace('部门：', '').trim();
                        if (dept && !data.department.includes(dept)) {
                            data.department = dept;
                        }
                    } else if (!data.salary && (text.match(/\d+-\d+K/i) || text.match(/\d+K-\d+K/i) || text.includes('薪') || text.includes('¥')) && text.length < 30) {
                        data.salary = text;
                    } else if (!data.location && (text.includes('杭州') || text.includes('北京') || text.includes('上海') || text.includes('深圳') || text.includes('广州') || text.includes('成都')) && text.length < 20) {
                        data.location = text;
                    } else if (!data.work_experience) {
                        // 匹配工作年限
                        if (text.match(/(\d+-\d+年|经验\d+年|\d+年以上|工作年限\S*)/) && text.length < 30) {
                            // 提取纯年限信息
                            const match = text.match(/\d+-\d+年|\d+年以上/);
                            if (match) {
                                data.work_experience = match[0];
                            } else {
                                data.work_experience = text;
                            }
                        }
                    }
                });

                // 3. 提取岗位职责和任职要求
                const sections = Array.from(document.querySelectorAll('div')).filter(el => {
                    const text = el.textContent.trim();
                    return text.includes('职位描述') || text.includes('岗位职责') || text.includes('任职要求') || text.includes('职位要求');
                });

                let inResponsibilities = false;
                let inRequirements = false;
                const responsibilities = [];
                const requirements = [];

                // 遍历所有文本行，精确提取职责和要求
                const allLines = document.body.innerText.split('\\n').map(line => line.trim()).filter(line => line);
                for (const line of allLines) {
                    // 识别职责部分
                    if (line === '职位描述' || line === '岗位职责' || line === '工作内容') {
                        inResponsibilities = true;
                        inRequirements = false;
                        continue;
                    }
                    // 识别要求部分
                    if (line === '任职要求' || line === '职位要求' || line === '资格要求' || line === '我们希望你') {
                        inResponsibilities = false;
                        inRequirements = true;
                        continue;
                    }
                    // 收集职责
                    if (inResponsibilities) {
                        // 遇到下一个大标题停止
                        if (line.length < 15 && (line.includes('：') || line.includes('要求') || line.includes('资格'))) {
                            inResponsibilities = false;
                        } else if (line.length > 5) {
                            responsibilities.push(line);
                        }
                    }
                    // 收集要求
                    if (inRequirements) {
                        // 遇到页脚停止
                        if (line.includes('淘天集团') || line.includes('©') || line.includes('咨询电话')) {
                            break;
                        } else if (line.length > 5) {
                            requirements.push(line);
                        }
                    }
                }

                data.responsibilities = responsibilities.join('\\n');
                data.requirements = requirements.join('\\n');

                // 提取工作经验
                if (!data.work_experience) {
                    const allText = document.body.innerText;
                    // 更宽松的匹配规则
                    const expPatterns = [
                        /(\d+-\d+年)/,
                        /(\d+年以上)/,
                        /(\d+年经验)/,
                        /经验：(\S+)/,
                        /工作年限：(\S+)/,
                        /要求.*?(\d+年)/
                    ];

                    for (const pattern of expPatterns) {
                        const match = allText.match(pattern);
                        if (match) {
                            data.work_experience = match[1];
                            break;
                        }
                    }

                    // 从要求里提取经验相关内容
                    if (!data.work_experience && data.requirements) {
                        const reqLines = data.requirements.split('\\n');
                        for (const line of reqLines) {
                            if (line.includes('年') && (line.includes('经验') || line.includes('工作') || line.includes('从业'))) {
                                data.work_experience = line.trim();
                                break;
                            }
                        }
                    }
                }

                // 兜底方案：如果没找到结构化的职责要求，提取主要内容
                if (!data.responsibilities || !data.requirements) {
                    const mainContent = document.querySelector('main') || document.body;
                    const allText = mainContent.innerText;

                    // 尝试用关键词分割
                    const descIndex = Math.max(
                        allText.indexOf('职位描述'),
                        allText.indexOf('岗位职责'),
                        allText.indexOf('工作内容')
                    );
                    const reqIndex = Math.max(
                        allText.indexOf('任职要求'),
                        allText.indexOf('职位要求'),
                        allText.indexOf('资格要求')
                    );

                    if (descIndex > 0 && reqIndex > descIndex) {
                        data.responsibilities = allText.slice(descIndex + 4, reqIndex).trim();
                        data.requirements = allText.slice(reqIndex + 4).trim().split('淘天集团')[0].trim();
                    }
                }

                return data;
            }''')

            # 合并数据
            job.update(page_data)

            # 确保至少有标题
            if not job["title"]:
                # 从URL中提取ID作为备用标题
                job["title"] = f"职位_{job['job_id']}"

            return job

        except Exception as e:
            print(f"Error parsing job detail {job_url}: {str(e)[:50]}...")
            # 即使解析失败，也返回基本信息
            return {
                "url": job_url,
                "job_id": self.extract_job_id(job_url),
                "title": f"职位_{self.extract_job_id(job_url)}",
                "department": "",
                "salary": "",
                "location": "",
                "work_experience": "",
                "responsibilities": "",
                "requirements": "",
                "publish_date": ""
            }

    async def parse_job_list(self, page_num: int = 1) -> List[str]:
        """Parse job list page and return all job detail urls"""
        try:
            if page_num == 1:
                # 第一页已经在select_filters后加载了，不需要重新跳转
                pass
            else:
                # 获取当前页码（从页码显示区域获取，格式: 1/11）
                current_page_before = await self.page.evaluate('''() => {
                    const pageDisplay = document.querySelector('.next-pagination-display');
                    if (pageDisplay) {
                        const match = pageDisplay.textContent.trim().match(/(\\d+)\\/\\d+/);
                        if (match) return parseInt(match[1]);
                    }
                    return 1;
                }''')

                # 检查是否已经到最后一页（需要等待页面稳定后再判断）
                await self.page.wait_for_timeout(1000)
                is_last_page = await self.page.evaluate('''() => {
                    const nextBtn = document.querySelector('.next-pagination-item.next-next');
                    if (!nextBtn) return true;
                    // 检查是否有disabled类或者disabled属性
                    const isDisabled = nextBtn.disabled ||
                                     nextBtn.classList.contains('disabled') ||
                                     nextBtn.getAttribute('aria-disabled') === 'true';
                    return isDisabled;
                }''')
                if is_last_page:
                    print("⚠️ 已经是最后一页，无法继续翻页")
                    return []

                # 最多尝试3次点击下一页
                max_retries = 3
                click_success = False

                for retry in range(max_retries):
                    try:
                        # 精确查找下一页按钮（Next UI的分页组件）
                        next_btn = self.page.locator('.next-pagination-item.next-next').first
                        if await next_btn.is_enabled(timeout=2000):
                            # 滚动到可见区域
                            await next_btn.scroll_into_view_if_needed()
                            await self.page.wait_for_timeout(1000)
                            # 点击按钮
                            await next_btn.click(force=True)
                            click_success = True
                            break
                        else:
                            print(f"⚠️ 第 {retry+1} 次尝试下一页按钮不可用")
                    except Exception as e:
                        print(f"⚠️ 第 {retry+1} 次点击下一页失败: {str(e)[:50]}")
                    await self.page.wait_for_timeout(2000)

                if not click_success:
                    print("⚠️ 多次尝试后仍无法点击下一页，已到最后一页")
                    return []

                # 等待页面加载和内容更新
                await self.page.wait_for_timeout(5000)
                await self.page.wait_for_load_state("domcontentloaded")
                await self.page.wait_for_timeout(2000)

                # 验证是否成功跳转到下一页
                current_page_after = await self.page.evaluate('''() => {
                    const pageDisplay = document.querySelector('.next-pagination-display');
                    if (pageDisplay) {
                        const match = pageDisplay.textContent.trim().match(/(\\d+)\\/\\d+/);
                        if (match) return parseInt(match[1]);
                    }
                    return 1;
                }''')

                if current_page_after > current_page_before:
                    print(f"✅ 跳转到第 {current_page_after} 页成功")
                else:
                    print(f"⚠️ 页面可能未跳转，当前页码仍为 {current_page_after}")

            # 等待页面动态渲染完成
            await self.page.wait_for_timeout(8000)
            await self.random_delay()

            job_links = set()

            # 1. 找所有a标签的职位链接
            a_links = await self.page.evaluate('''() => {
                const links = [];
                document.querySelectorAll('a').forEach(a => {
                    const href = a.href;
                    if (href && (href.includes('/position/') || href.includes('positionId'))) {
                        links.push(href);
                    }
                });
                return links;
            }''')
            for link in a_links:
                job_links.add(link)

            # 2. 从表格行的属性和点击事件中获取链接
            if len(job_links) < 7:
                row_links = await self.page.evaluate('''() => {
                    const links = [];
                    // 遍历所有表格行
                    const rows = document.querySelectorAll('div[role="row"]');
                    rows.forEach(row => {
                        // 检查行的点击事件
                        const onclick = row.getAttribute('onclick');
                        if (onclick) {
                            // 提取positionId
                            const match = onclick.match(/positionId[=:"']*(\\d+)/);
                            if (match) {
                                links.push(`https://talent.taotian.com/off-campus/position-detail?positionId=${match[1]}`);
                            }
                        }
                        // 检查行内隐藏的链接
                        const hiddenLinks = row.querySelectorAll('[style*="display:none"] a');
                        hiddenLinks.forEach(a => {
                            if (a.href && (a.href.includes('/position/') || a.href.includes('positionId'))) {
                                links.push(a.href);
                            }
                        });
                    });
                    return links;
                }''')
                for link in row_links:
                    job_links.add(link)

            # 3. 拦截window.open点击获取（不会新开标签）
            if len(job_links) < 7:
                captured = await self.page.evaluate('''() => {
                    const links = new Set();
                    const originalOpen = window.open;
                    // 拦截window.open
                    window.open = function(url) {
                        if (url.includes('/position/') || url.includes('positionId')) {
                            links.add(url);
                        }
                        return { close: () => {} };
                    };

                    // 只点击职位名称单元格
                    document.querySelectorAll('div[role="gridcell"]:first-child').forEach(cell => {
                        try { cell.click(); } catch(e) {}
                    });

                    // 恢复原方法
                    window.open = originalOpen;
                    return Array.from(links);
                }''')
                for link in captured:
                    job_links.add(link)

            print(f"✅ 本页找到 {len(job_links)} 个职位链接")
            return list(job_links)[:10]

        except Exception as e:
            print(f"Error parsing job list page {page_num}: {str(e)[:80]}...")
            return []

    async def select_filters(self):
        """Select filters: 社会招聘 + 研发岗位"""
        try:
            # 先访问社会招聘主页面，直接搜索算法
            social_url = "https://talent.taotian.com/off-campus/position-list?lang=zh&search=算法"
            print(f"访问社会招聘页面并搜索算法: {social_url}")
            await self.page.goto(social_url, timeout=120000, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(8000)
            print(f"✅ 成功进入搜索结果页面")

            # 点击职位类别展开下拉
            print("展开职位类别筛选...")
            await self.page.click('text="职位类别"', force=True)
            await self.page.wait_for_timeout(2000)
            print("✅ 职位类别已展开")

            # 找到技术类并勾选
            print("勾选技术类...")
            await self.page.evaluate('''() => {
                const items = Array.from(document.querySelectorAll('div[role="treeitem"]'));
                for (const item of items) {
                    if (item.textContent.includes('技术类')) {
                        const checkbox = item.querySelector('input[type="checkbox"]');
                        if (checkbox && !checkbox.checked) {
                            checkbox.click();
                        }
                        break;
                    }
                }
            }''')
            await self.page.wait_for_timeout(3000)
            print("✅ 技术类已勾选")

            # 获取职位总数
            self.total_jobs = 0
            self.total_pages = 0
            try:
                # 提取总数
                count_text = await self.page.locator('text=/共\\s*\\d+\\s*个岗位/').first.inner_text()
                import re
                match = re.search(r'(\d+)', count_text)
                if match:
                    self.total_jobs = int(match.group(1))
                    self.total_pages = (self.total_jobs + 6) // 7  # 每页7个职位
                    print(f"\n📊 筛选完成：")
                    print(f"   总算法职位数: {self.total_jobs} 个")
                    print(f"   预计总页数: {self.total_pages} 页")

                    # 检查是否符合预期
                    if 100 <= self.total_jobs <= 115:
                        print("✅ 职位数量符合预期（107左右）")
                    else:
                        print(f"⚠️ 职位数量不符合预期：实际{self.total_jobs}个，预期107左右")
            except Exception as e:
                print(f"⚠️ 无法获取职位总数: {str(e)[:50]}")

            await self.random_delay()
            return True
        except Exception as e:
            print(f"⚠️ 筛选过程出现异常: {str(e)[:100]}...")
            return False

    def is_rd_job(self, job: Dict) -> bool:
        """Check if job is R&D related"""
        if not job.get("title"):
            return False

        title = job["title"].lower()
        rd_keywords = ["开发", "研发", "工程师", "算法", "技术", "程序", "软件", "java", "python", "go", "c++",
                      "前端", "后端", "客户端", "移动端", "测试", "运维", "安全", "数据", "ai", "nlp", "算法"]

        for keyword in rd_keywords:
            if keyword in title:
                return True
        return False

    async def crawl(self, max_pages: int = 10, only_social_rd: bool = True) -> dict:
        """Start crawling process"""
        if not self.browser:
            await self.init_browser()

        stats = {
            "total_found": 0,
            "rd_filtered": 0,
            "new_added": 0,
            "updated": 0,
            "duplicate": 0,
            "failed": 0
        }

        try:
            # Select filters first if needed
            if only_social_rd:
                await self.select_filters()

            # 进度条显示函数
            def print_progress(current, total, stats):
                progress = int(current / total * 50)
                bar = "█" * progress + "░" * (50 - progress)
                percent = f"{current/total*100:.1f}%"
                status = f"| {bar} | {percent} | 总发现:{stats['total_found']} | 新增:{stats['new_added']} | 重复:{stats['duplicate']} | 失败:{stats['failed']} |"
                sys.stdout.write("\r" + status)
                sys.stdout.flush()

            # 自动调整最大页数不超过实际总页数
            if hasattr(self, 'total_pages') and self.total_pages > 0:
                if max_pages > self.total_pages:
                    max_pages = self.total_pages
                    print(f"\n🚀 即将开始爬取全部 {max_pages} 页，共 {self.total_jobs} 个算法职位")
                else:
                    print(f"\n🚀 即将开始爬取前 {max_pages} 页，共约 {min(max_pages*10, self.total_jobs)} 个算法职位（总共有 {self.total_jobs} 个职位/{self.total_pages} 页）")
            else:
                print(f"\n🚀 即将开始爬取前 {max_pages} 页")

            for page_num in range(1, max_pages + 1):
                print(f"\n📄 正在爬取第 {page_num}/{max_pages} 页...")
                job_urls = await self.parse_job_list(page_num)

                if not job_urls:
                    print(f"⚠️ 第 {page_num} 页无职位，继续爬取下一页")
                    print_progress(page_num, max_pages, stats)
                    continue

                stats["total_found"] += len(job_urls)
                print(f"✅ 第 {page_num} 页找到 {len(job_urls)} 个职位")

                for idx, job_url in enumerate(job_urls, 1):
                    job_id = self.extract_job_id(job_url)
                    if not job_id:
                        stats["failed"] += 1
                        continue

                    job_exists = self.db.job_exists(job_id)
                    if job_exists:
                        # 检查是否需要更新：没有职责/要求 或 标题是占位符
                        import sqlite3
                        conn = sqlite3.connect(self.db.db_path)
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()
                        cursor.execute('SELECT title, responsibilities, requirements FROM jobs WHERE job_id = ?', (job_id,))
                        existing_job = dict(cursor.fetchone())
                        conn.close()

                        need_update = (not existing_job['responsibilities'] or
                                      not existing_job['requirements'] or
                                      existing_job['title'].startswith('职位_'))

                        if not need_update:
                            stats["duplicate"] += 1
                            print(f"Job {job_id} already exists and is complete, skipping...")
                            continue
                        else:
                            print(f"Job {job_id} exists but needs update, re-crawling...")

                    # 补全完整URL
                    if not job_url.startswith('http'):
                        full_url = f"https://talent.taotian.com{job_url}"
                    else:
                        full_url = job_url

                    # 在新标签页打开详情页，爬完就关闭，保持列表页不变
                    print(f"🔍 正在爬取: {full_url}")
                    try:
                        # 新开标签页
                        detail_page = await self.browser.new_page()
                        await detail_page.goto(full_url, timeout=60000, wait_until="domcontentloaded")
                        await detail_page.wait_for_timeout(2000)

                        # 爬取详情
                        job = await self.parse_job_detail(full_url, page=detail_page)

                        # 关闭详情页
                        await detail_page.close()
                    except Exception as e:
                        print(f"❌ 爬取详情失败，关闭详情页: {str(e)[:50]}")
                        # 确保关闭所有多余标签页
                        pages = self.browser.contexts[0].pages
                        for page in pages[1:]:
                            await page.close()
                        job = None

                    if job and job["title"]:
                        # Filter R&D jobs only
                        '''
                        if only_social_rd and not self.is_rd_job(job):
                            stats["rd_filtered"] += 1
                            print(f"Non-R&D job filtered out: {job['title']}")
                            continue
                        '''
                        if not job_exists:
                            success = self.db.insert_job(job)
                            if success:
                                stats["new_added"] += 1
                                print(f"Successfully added R&D job: {job['title']}")
                            else:
                                stats["duplicate"] += 1
                        else:
                            # 更新已有职位
                            import sqlite3
                            conn = sqlite3.connect(self.db.db_path)
                            cursor = conn.cursor()
                            cursor.execute('''
                            UPDATE jobs
                            SET title = ?, department = ?, salary = ?, location = ?, work_experience = ?,
                                responsibilities = ?, requirements = ?
                            WHERE job_id = ?
                            ''', (
                                job.get('title', existing_job['title']),
                                job.get('department', ''),
                                job.get('salary', ''),
                                job.get('location', ''),
                                job.get('work_experience', ''),
                                job.get('responsibilities', existing_job['responsibilities']),
                                job.get('requirements', existing_job['requirements']),
                                job_id
                            ))
                            conn.commit()
                            conn.close()
                            stats["updated"] += 1
                            print(f"Successfully updated job: {job['title']}")
                    else:
                        stats["failed"] += 1
                        print(f"❌ 解析失败: {job_url}")

                    # 更新进度
                    overall_progress = (page_num - 1) / max_pages + (idx / len(job_urls)) / max_pages
                    print_progress(page_num + (idx/len(job_urls)), max_pages, stats)

            print(f"\n✅ 爬取完成! 统计: {stats}")
            return stats

        finally:
            if self.browser:
                await self.browser.close()

if __name__ == "__main__":
    spider = TaotianSpider(headless=False)  # Set headless=True for production
    asyncio.run(spider.crawl(max_pages=5))
