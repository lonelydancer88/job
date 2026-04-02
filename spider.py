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

    async def parse_job_detail(self, job_url: str) -> Optional[Dict]:
        """Parse job detail page and extract job information"""
        try:
            await self.page.goto(job_url, timeout=60000, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)

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
            page_data = await self.page.evaluate('''() => {
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
                # 方法1：尝试点击下一页按钮
                try:
                    next_btn = self.page.get_by_role("button", name="下一页").first
                    if await next_btn.is_enabled(timeout=3000):
                        await next_btn.click()
                        await self.page.wait_for_timeout(4000)
                        await self.page.wait_for_load_state("domcontentloaded")
                        print(f"✅ 点击下一页成功，跳转到第 {page_num} 页")
                    else:
                        print("⚠️ 下一页按钮不可用")
                        return []
                except Exception as e:
                    # 方法2：直接构造分页URL访问
                    try:
                        # 直接构造列表页的分页URL，避免在详情页构造错误
                        base_list_url = "https://talent.taotian.com/off-campus/position-list?lang=zh&search="
                        new_url = f"{base_list_url}&page={page_num}"

                        print(f"⚠️ 点击下一页失败，尝试直接访问列表页URL: {new_url}")
                        await self.page.goto(new_url, timeout=60000, wait_until="domcontentloaded")
                        await self.page.wait_for_timeout(5000)
                    except Exception as e2:
                        print(f"❌ 翻页失败: {str(e)[:50]}, {str(e2)[:50]}")
                        return []

            # 等待页面动态渲染完成
            await self.page.wait_for_timeout(8000)
            await self.random_delay()

            job_links = set()

            # 1. 先找所有a标签的职位链接
            a_links = await self.page.evaluate('''() => {
                const links = [];
                document.querySelectorAll('a').forEach(a => {
                    const href = a.href;
                    const text = a.textContent.trim();
                    if (href && href.includes('/position/') && text && text.length > 3 && text.length < 100) {
                        links.push(href);
                    }
                });
                return links;
            }''')
            for link in a_links:
                job_links.add(link)

            # 2. 用Playwright监听popup事件捕获新打开的标签页
            if len(job_links) < 5:
                popup_event = asyncio.create_task(self.page.wait_for_event("popup", timeout=10000))

                # 找所有职位卡片
                job_cards = await self.page.locator('div[role="row"], div.cursor-pointer').all()
                click_tasks = []
                for card in job_cards[:10]:
                    try:
                        if await card.is_enabled(timeout=500):
                            click_tasks.append(card.click(force=True, timeout=2000))
                    except:
                        pass

                # 等待点击完成
                if click_tasks:
                    await asyncio.gather(*click_tasks, return_exceptions=True)

                # 捕获所有新打开的页面
                try:
                    new_page = await popup_event
                    await new_page.wait_for_load_state()
                    job_links.add(new_page.url)
                    await new_page.close()
                except:
                    pass

            job_links = set()

            # 1. 先找所有a标签的职位链接
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

            # 2. 如果a标签找的少，直接在页面内点击捕获链接
            if len(job_links) < 5:
                # 先重写window.open直接捕获URL，不需要实际打开标签页
                captured = await self.page.evaluate('''() => {
                    const links = new Set();
                    const originalOpen = window.open;
                    window.open = function(url) {
                        if (url.includes('/position/') || url.includes('positionId')) {
                            links.add(url);
                        }
                        return { close: () => {} };
                    };

                    // 点击所有看起来像职位的元素
                    document.querySelectorAll('div, span, li').forEach(el => {
                        const text = el.textContent.trim();
                        if (text.length > 5 && text.length < 100 &&
                            (text.includes('工程师') || text.includes('专家') || text.includes('开发') ||
                             text.includes('算法') || text.includes('运营') || text.includes('产品')) &&
                            (text.includes('杭州') || text.includes('北京') || text.includes('上海') ||
                             text.includes('深圳') || text.includes('广州') || text.includes('成都'))) {
                            try { el.click(); } catch(e) {}
                        }
                    });

                    // 恢复原来的window.open
                    window.open = originalOpen;
                    return Array.from(links);
                }''')

                for link in captured:
                    job_links.add(link)

            return list(job_links)[:20]

        except Exception as e:
            print(f"Error parsing job list page {page_num}: {str(e)[:80]}...")
            return []

    async def select_filters(self):
        """Select filters: 社会招聘 + 研发岗位"""
        try:
            # 先访问社会招聘主页面
            social_url = "https://talent.taotian.com/off-campus/position-list?lang=zh&search="
            print(f"访问社会招聘页面: {social_url}")
            await self.page.goto(social_url, timeout=120000, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(8000)
            print(f"✅ 成功进入社会招聘页面")

            # 先点击职位类别展开
            print("展开职位类别筛选...")
            try:
                # 尝试多种定位方式找职位类别按钮
                category_btn = None
                selectors = [
                    'button:has-text("职位类别")',
                    'div[role="button"]:has-text("职位类别")',
                    'span:has-text("职位类别")',
                    '//*[contains(text(), "职位类别")]'
                ]

                for selector in selectors:
                    try:
                        if selector.startswith('//'):
                            category_btn = self.page.locator(selector).first
                        else:
                            category_btn = self.page.locator(selector).first
                        if await category_btn.is_enabled(timeout=2000):
                            break
                    except:
                        continue

                if category_btn:
                    await category_btn.click(force=True)
                    await self.page.wait_for_timeout(2000)
                    print("✅ 职位类别已展开")
            except Exception as e:
                print(f"⚠️ 展开职位类别失败: {str(e)[:50]}")

            # 勾选技术类
            print("勾选技术类...")
            try:
                tech_checkbox = None
                tech_selectors = [
                    'label:has-text("技术类") >> input[type="checkbox"]',
                    'div:has-text("技术类") >> input[type="checkbox"]',
                    '//*[contains(text(), "技术类")]/preceding::input[@type="checkbox"][1]',
                    'div[role="treeitem"]:has-text("技术类")'
                ]

                for selector in tech_selectors:
                    try:
                        if selector.startswith('//'):
                            tech_checkbox = self.page.locator(selector).first
                        else:
                            tech_checkbox = self.page.locator(selector).first
                        if await tech_checkbox.is_enabled(timeout=2000):
                            break
                    except:
                        continue

                if tech_checkbox:
                    # 如果是treeitem，先点击展开
                    if await tech_checkbox.get_attribute('role') == 'treeitem':
                        await tech_checkbox.click(force=True)
                        await self.page.wait_for_timeout(1000)
                        # 直接点击整个item
                        await tech_checkbox.click(force=True)
                    else:
                        # 直接点击元素
                        await tech_checkbox.click(force=True)
                    print("✅ 技术类已勾选")
                    await self.page.wait_for_timeout(2000)
            except Exception as e:
                print(f"⚠️ 勾选技术类失败: {str(e)[:50]}")

            # 展开技术类子菜单
            print("展开技术类子菜单...")
            try:
                expand_icon = None
                expand_selectors = [
                    'div[role="treeitem"]:has-text("技术类") i[class*="expand"]',
                    'div[role="treeitem"]:has-text("技术类") i[class*="arrow"]',
                    'div:has-text("技术类") >> span[role="button"]'
                ]

                for selector in expand_selectors:
                    try:
                        expand_icon = self.page.locator(selector).first
                        if await expand_icon.is_enabled(timeout=2000):
                            break
                    except:
                        continue

                if expand_icon:
                    await expand_icon.click(force=True)
                    await self.page.wait_for_timeout(2000)
                    print("✅ 技术类子菜单已展开")
            except Exception as e:
                print(f"⚠️ 展开技术类子菜单失败: {str(e)[:50]}")

            # 勾选算法类
            print("勾选算法类...")
            try:
                algo_checkbox = None
                algo_selectors = [
                    'label:has-text("算法") >> input[type="checkbox"]',
                    'div:has-text("算法") >> input[type="checkbox"]',
                    '//*[contains(text(), "算法")]/preceding::input[@type="checkbox"][1]'
                ]

                for selector in algo_selectors:
                    try:
                        if selector.startswith('//'):
                            algo_checkbox = self.page.locator(selector).first
                        else:
                            algo_checkbox = self.page.locator(selector).first
                        if await algo_checkbox.is_enabled(timeout=2000):
                            break
                    except:
                        continue

                if algo_checkbox:
                    # 直接点击元素
                    await algo_checkbox.click(force=True)
                    print("✅ 算法类已勾选")
                    await self.page.wait_for_timeout(3000)
            except Exception as e:
                print(f"⚠️ 勾选算法类失败: {str(e)[:50]}")

            # 获取职位总数并计算总页数
            self.total_jobs = 0
            self.total_pages = 0
            try:
                # 尝试多种方式获取职位总数
                job_count_text = ""
                # 先找包含数字和岗位/职位的文本
                elements = await self.page.locator('div, span, p').all_inner_texts()
                for text in elements:
                    if ('个岗位' in text or '个职位' in text or '条结果' in text) and any(c.isdigit() for c in text):
                        job_count_text = text
                        break

                if not job_count_text:
                    # 直接在页面文本里找
                    page_text = await self.page.inner_text('body')
                    import re
                    match = re.search(r'共\s*(\d+)\s*(个岗位|个职位|条结果)', page_text)
                    if match:
                        job_count_text = match.group(0)

                # 提取数字
                if job_count_text:
                    import re
                    match = re.search(r'(\d+)', job_count_text)
                    if match:
                        self.total_jobs = int(match.group(1))
                        # 每页约7-8个职位，计算总页数
                        self.total_pages = (self.total_jobs + 6) // 7  # 向上取整
                        print(f"✅ 筛选完成，共 {self.total_jobs} 个相关职位，预计 {self.total_pages} 页")
            except Exception as e:
                print(f"✅ 筛选完成，开始爬取")

            await self.random_delay()
            return True
        except Exception as e:
            print(f"⚠️ 页面加载出现异常，将继续尝试爬取: {str(e)[:100]}...")
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

            # 连续空页计数器，连续3页空才停止
            empty_page_count = 0
            total_processed = 0

            # 进度条显示函数
            def print_progress(current, total, stats):
                progress = int(current / total * 50)
                bar = "█" * progress + "░" * (50 - progress)
                percent = f"{current/total*100:.1f}%"
                status = f"| {bar} | {percent} | 总发现:{stats['total_found']} | 新增:{stats['new_added']} | 重复:{stats['duplicate']} | 失败:{stats['failed']} |"
                sys.stdout.write("\r" + status)
                sys.stdout.flush()

            # 自动调整最大页数为实际总页数
            if hasattr(self, 'total_pages') and self.total_pages > 0:
                if max_pages > self.total_pages:
                    max_pages = self.total_pages
                    print(f"📊 自动调整爬取页数为实际总页数: {max_pages} 页")
                else:
                    print(f"📊 待爬取总页数: {self.total_pages} 页，本次爬取前 {max_pages} 页")

            for page_num in range(1, max_pages + 1):
                print(f"\n📄 正在爬取第 {page_num}/{max_pages} 页...")
                job_urls = await self.parse_job_list(page_num)

                if not job_urls:
                    empty_page_count += 1
                    print(f"⚠️ 第 {page_num} 页无职位，空页计数: {empty_page_count}/3")
                    if empty_page_count >= 3:
                        print("\n🛑 连续3页无职位，爬取结束")
                        break
                    print_progress(page_num, max_pages, stats)
                    continue
                else:
                    empty_page_count = 0

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
                    # 关闭多余的标签页，只保留当前页
                    pages = self.browser.contexts[0].pages
                    for page in pages[1:]:  # 第一个是主页，其他都关闭
                        await page.close()

                    print(f"🔍 正在爬取: {full_url}")
                    job = await self.parse_job_detail(full_url)

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
