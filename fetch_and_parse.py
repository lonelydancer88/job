import asyncio
from playwright.async_api import async_playwright

async def fetch_and_analyze():
    print("🔍 自动获取页面源码并分析结构...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )

        # 访问页面
        await page.goto("https://talent.taotian.com/off-campus/position-list?lang=zh&search=", timeout=120000)

        print("\n⏳ 等待30秒，请完成滑块验证/登录...")
        for i in range(3):
            print(f"   还有 {30 - i*10} 秒...")
            await page.wait_for_timeout(10000)

        # 保存完整HTML源码
        content = await page.content()
        with open("full_page.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 完整页面源码已保存到 full_page.html")

        # 自动分析页面结构
        print("\n🔬 正在分析页面结构...")

        # 查找职位列表容器
        list_container = await page.evaluate('''() => {
            // 找包含多个职位的容器
            const containers = document.querySelectorAll('div, ul, section');
            for (const container of containers) {
                const children = Array.from(container.children);
                let jobCount = 0;
                children.forEach(child => {
                    const text = child.textContent.trim();
                    if (text.includes('工程师') || text.includes('开发') || text.includes('研发')) {
                        jobCount++;
                    }
                });
                if (jobCount >= 3) {
                    return {
                        tag: container.tagName,
                        className: container.className,
                        id: container.id,
                        childCount: children.length,
                        jobCount: jobCount
                    };
                }
            }
            return null;
        }''')

        if list_container:
            print(f"✅ 找到职位列表容器:")
            print(f"   标签: {list_container['tag']}")
            print(f"   Class: {list_container['className']}")
            print(f"   包含职位数: {list_container['jobCount']}")
        else:
            print("⚠️  未找到明确的列表容器，尝试直接提取所有职位")

        # 提取所有职位结构
        jobs = await page.evaluate('''() => {
            const jobs = [];
            // 遍历所有元素，找职位结构
            document.querySelectorAll('*').forEach(el => {
                const text = el.textContent.trim();
                if ((text.includes('工程师') || text.includes('开发') || text.includes('研发')) && text.length > 20 && text.length < 500) {
                    // 提取元素结构
                    const structure = {
                        text: text,
                        className: el.className,
                        tag: el.tagName,
                        childElements: []
                    };
                    el.querySelectorAll('*').forEach(child => {
                        if (child.textContent.trim()) {
                            structure.childElements.push({
                                tag: child.tagName,
                                className: child.className,
                                text: child.textContent.trim().slice(0, 30)
                            });
                        }
                    });
                    jobs.push(structure);
                }
            });
            return jobs.slice(0, 3); // 返回前3个职位的结构
        }''')

        print(f"\n📋 找到的职位结构样例:")
        for i, job in enumerate(jobs, 1):
            print(f"\n职位{i} 结构:")
            print(f"   总文本: {job['text'][:100]}...")
            print(f"   子元素:")
            for child in job['childElements'][:5]:
                print(f"     <{child['tag']} class='{child['className']}'> {child['text']}")

        await browser.close()

        print("\n🚀 源码抓取完成，现在更新爬取逻辑适配页面结构！")

if __name__ == "__main__":
    asyncio.run(fetch_and_analyze())
