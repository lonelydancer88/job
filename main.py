import asyncio
import argparse
from database import Database

def main():
    parser = argparse.ArgumentParser(description='淘系招聘职位爬取与匹配系统')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Crawl job listings from talent.taotian.com')
    crawl_parser.add_argument('--pages', type=int, default=10, help='Number of pages to crawl (default: 10)')
    crawl_parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    crawl_parser.add_argument('--all-jobs', action='store_true', help='Crawl all jobs, not just social R&D positions')

    # Match command
    match_parser = subparsers.add_parser('match', help='Match resume with jobs in database')
    match_parser.add_argument('--resume', required=True, help='Path to resume file (PDF/DOCX/TXT)')
    match_parser.add_argument('--top', type=int, default=10, help='Number of top matches to return (default: 10)')

    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')

    args = parser.parse_args()

    if args.command == 'crawl':
        from spider import TaotianSpider
        only_social_rd = not args.all_jobs
        if only_social_rd:
            print(f"Starting crawler with {args.pages} pages (only 社会招聘 R&D positions)...")
        else:
            print(f"Starting crawler with {args.pages} pages (all positions)...")
        spider = TaotianSpider(headless=args.headless)
        asyncio.run(spider.crawl(max_pages=args.pages, only_social_rd=only_social_rd))

    elif args.command == 'match':
        from matcher_simple import SimpleJobMatcher
        print(f"Matching resume: {args.resume}")
        matcher = SimpleJobMatcher()
        results = matcher.match_jobs(args.resume, top_n=args.top)
        matcher.print_match_results(results)

    elif args.command == 'stats':
        db = Database()
        count = db.get_job_count()
        print(f"Database statistics:")
        print(f"Total jobs stored: {count}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
