import json
import sqlite3
from database import Database

def dump_to_jsonl(output_file: str = "jobs_dump.jsonl"):
    db = Database()
    jobs = db.get_all_jobs()

    with open(output_file, 'w', encoding='utf-8') as f:
        for job in jobs:
            # 转换为json，确保中文正常显示
            json_line = json.dumps(job, ensure_ascii=False)
            f.write(json_line + '\n')

    print(f"✅ 成功导出 {len(jobs)} 个职位到 {output_file}")
    return len(jobs)

if __name__ == "__main__":
    count = dump_to_jsonl()
    print(f"\n导出完成！共 {count} 条记录")
