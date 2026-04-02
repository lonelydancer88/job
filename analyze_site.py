import asyncio
from playwright.async_api import async_playwright

async def analyze_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )

        print("访问首页...")
        await page.goto("https://talent.taotian.com/", timeout=120000, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        await asyncio.sleep(3)

        print("当前URL:", page.url)
        print("页面标题:", await page.title())

        # 打印页面上所有可见的文本
        all_text = await page.evaluate('''() => document.body.innerText''')
        print("页面可见文本前500字符:", all_text[:500])

        # 尝试找所有按钮和链接
        elements = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a, button'))
                .map(el => ({
                    tag: el.tagName,
                    text: el.textContent.trim(),
                    href: el.href || ''
                }))
                .filter(item => item.text && item.text.length < 30)
                .slice(0, 30);
        }''')

        print("\n页面上的按钮/链接:")
        for el in elements:
            print(f"- [{el['tag']}] {el['text']} {el['href']}")

        # 截图看看页面
        await page.screenshot(path="site_home.png", full_page=True)
        print("\n已截图保存到 site_home.png")

        # 尝试找社会招聘入口
        try:
            await page.get_by_role("link", name="社会招聘").click(timeout=5000)
            await page.wait_for_timeout(5000)
            print("\n点击社会招聘后URL:", page.url)
            await page.screenshot(path="site_social.png")
        except Exception as e:
            print(f"点击社会招聘失败: {e}")
            # 试试点击校园招聘
            try:
                await page.get_by_role("link", name="校园招聘").click(timeout=5000)
                await page.wait_for_timeout(5000)
                print("\n点击校园招聘后URL:", page.url)
                await page.screenshot(path="site_campus.png")
            except Exception as e2:
                print(f"点击校园招聘也失败: {e2}")

        await browser.close()

asyncio.run(analyze_site())
