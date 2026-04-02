from typing import Dict, List, Tuple
from database import Database
from resume_parser import ResumeParser
import re
from collections import Counter

class SimpleJobMatcher:
    def __init__(self):
        self.db = Database()

    def preprocess_job_text(self, job: Dict) -> str:
        """Combine job fields into a single text string for matching"""
        fields = [
            job.get('title', ''),
            job.get('department', ''),
            job.get('location', ''),
            job.get('responsibilities', ''),
            job.get('requirements', '')
        ]
        return ' '.join([field for field in fields if field]).lower()

    def calculate_keyword_match(self, resume_info: Dict, job: Dict) -> Tuple[float, List[str]]:
        """Calculate keyword match score between resume and job"""
        resume_skills = set(resume_info.get('skills', []))
        resume_keywords = set(resume_info.get('keywords', []))
        all_resume_keywords = resume_skills.union(resume_keywords)

        if not all_resume_keywords:
            return 0.0, []

        job_text = self.preprocess_job_text(job)
        matching_keywords = []

        for keyword in all_resume_keywords:
            if keyword.lower() in job_text:
                matching_keywords.append(keyword)

        score = len(matching_keywords) / len(all_resume_keywords)
        return min(score, 1.0), matching_keywords

    def calculate_text_similarity(self, resume_text: str, job_text: str) -> float:
        """Simple text similarity based on common word frequency"""
        # 简单的词频匹配
        def get_word_counts(text):
            words = re.findall(r'[\w\u4e00-\u9fff]+', text.lower())
            stop_words = {'的', '了', '和', '是', '在', '我', '有', '也', '可以', '能够', '擅长', '熟悉', '掌握',
                          'the', 'and', 'of', 'to', 'a', 'in', 'for', 'on', 'with', 'as', 'is', 'that', 'this'}
            return Counter([w for w in words if w not in stop_words and len(w) >= 2])

        resume_counts = get_word_counts(resume_text)
        job_counts = get_word_counts(job_text)

        common_words = set(resume_counts.keys()) & set(job_counts.keys())
        if not common_words:
            return 0.0

        # Jaccard相似度
        intersection = sum(min(resume_counts[w], job_counts[w]) for w in common_words)
        union = sum(resume_counts.values()) + sum(job_counts.values()) - intersection

        return intersection / union if union > 0 else 0.0

    def match_jobs(self, resume_path: str, top_n: int = 10) -> List[Dict]:
        """Match resume against all jobs in database and return top N matches"""
        # Parse resume
        parser = ResumeParser()
        resume_info = parser.parse_resume(resume_path)
        if not resume_info:
            return []

        resume_text = resume_info.get('full_text', '')
        if not resume_text:
            return []

        # Get all jobs from database
        jobs = self.db.get_all_jobs()
        if not jobs:
            print("No jobs found in database, please run crawler first.")
            return []

        results = []
        for job in jobs:
            keyword_score, matching_keywords = self.calculate_keyword_match(resume_info, job)
            job_text = self.preprocess_job_text(job)
            similarity_score = self.calculate_text_similarity(resume_text, job_text)

            # Combined score: 50% keyword match + 50% text similarity
            total_score = (keyword_score * 0.5) + (similarity_score * 0.5)

            results.append({
                "job": job,
                "total_score": round(total_score * 100, 2),
                "keyword_score": round(keyword_score * 100, 2),
                "similarity_score": round(similarity_score * 100, 2),
                "matching_keywords": matching_keywords
            })

        # Sort by total score descending
        results.sort(key=lambda x: x["total_score"], reverse=True)

        # Return top N results
        return results[:top_n]

    def print_match_results(self, results: List[Dict]):
        """Pretty print match results"""
        if not results:
            print("No matching jobs found.")
            return

        print(f"\n=== Top {len(results)} Matching Jobs ===")
        for i, result in enumerate(results, 1):
            job = result["job"]
            print(f"\n{i}. {job['title']}")
            print(f"   匹配度: {result['total_score']}% (关键词: {result['keyword_score']}%, 文本相似度: {result['similarity_score']}%)")
            print(f"   部门: {job['department'] or '未知'}")
            print(f"   薪资: {job['salary'] or '面议'}")
            print(f"   地点: {job['location'] or '未知'}")
            print(f"   发布时间: {job['publish_date'] or '未知'}")
            print(f"   匹配关键词: {', '.join(result['matching_keywords'][:10]) if result['matching_keywords'] else '无'}")
            print(f"   链接: {job['url']}")
            print("-" * 80)
