import asyncio
from spider import TaotianSpider
from database import Database

async def update_job_details():
    db = Database()
    jobs = db.get_all_jobs()

    # 筛选出需要更新详情的职位（没有职责和要求的）
    jobs_to_update = [job for job in jobs if not job['responsibilities'] or not job['requirements'] or job['title'].startswith('职位_')]
    print(f"Found {len(jobs_to_update)} jobs to update details")

    if not jobs_to_update:
        print("No jobs need update")
        return

    spider = TaotianSpider(headless=False)
    await spider.init_browser()

    updated_count = 0
    failed_count = 0

    for job in jobs_to_update:
        job_id = job['job_id']
        job_url = job['url']

        # 补全完整URL
        if not job_url.startswith('http'):
            full_url = f"https://talent.taotian.com{job_url}"
        else:
            full_url = job_url

        print(f"\nUpdating job {job_id}: {full_url}")

        try:
            job_detail = await spider.parse_job_detail(full_url)
            if job_detail and job_detail.get('responsibilities'):
                # 更新数据库
                conn = db._get_conn()
                cursor = conn.cursor()

                cursor.execute('''
                UPDATE jobs
                SET title = ?, department = ?, salary = ?, location = ?,
                    responsibilities = ?, requirements = ?
                WHERE job_id = ?
                ''', (
                    job_detail.get('title', job['title']),
                    job_detail.get('department', job['department']),
                    job_detail.get('salary', job['salary']),
                    job_detail.get('location', job['location']),
                    job_detail.get('responsibilities', job['responsibilities']),
                    job_detail.get('requirements', job['requirements']),
                    job_id
                ))

                conn.commit()
                conn.close()

                updated_count += 1
                print(f"✅ Updated job: {job_detail.get('title', job['title'])}")
            else:
                failed_count += 1
                print(f"❌ Failed to get details for job {job_id}")

        except Exception as e:
            failed_count += 1
            print(f"❌ Error updating job {job_id}: {str(e)[:100]}")

    await spider.browser.close()
    print(f"\nUpdate completed: {updated_count} updated, {failed_count} failed")

# 给Database添加一个获取连接的方法
def _get_conn(self):
    return sqlite3.connect(self.db_path)

Database._get_conn = _get_conn

if __name__ == "__main__":
    import sqlite3
    asyncio.run(update_job_details())
