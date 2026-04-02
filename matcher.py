from typing import Dict, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database import Database
from resume_parser import ResumeParser

class JobMatcher:
    def __init__(self):
        self.db = Database()
        self.vectorizer = TfidfVectorizer(
            stop_words=['english', 'chinese'],
            max_features=10000,
            ngram_range=(1, 2)
        )

    def preprocess_job_text(self, job: Dict) -> str:
        """Combine job fields into a single text string for matching"""
        fields = [
            job.get('title', ''),
            job.get('department', ''),
            job.get('location', ''),
            job.get('responsibilities', ''),
            job.get('requirements', '')
        ]
        return ' '.join([field for field in fields if field])

    def calculate_keyword_match(self, resume_info: Dict, job: Dict) -> Tuple[float, List[str]]:
        """Calculate keyword match score between resume and job"""
        resume_skills = set(resume_info.get('skills', []))
        resume_keywords = set(resume_info.get('keywords', []))
        all_resume_keywords = resume_skills.union(resume_keywords)

        if not all_resume_keywords:
            return 0.0, []

        job_text = self.preprocess_job_text(job).lower()
        matching_keywords = []

        for keyword in all_resume_keywords:
            if keyword.lower() in job_text:
                matching_keywords.append(keyword)

        score = len(matching_keywords) / len(all_resume_keywords)
        return min(score, 1.0), matching_keywords

    def calculate_similarity(self, resume_text: str, job_texts: List[str]) -> List[float]:
        """Calculate TF-IDF cosine similarity between resume and all jobs"""
        if not job_texts:
            return []

        # Combine resume text with job texts for vectorization
        all_texts = [resume_text] + job_texts
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)

        # Calculate similarity between resume (first vector) and all jobs
        resume_vector = tfidf_matrix[0:1]
        job_vectors = tfidf_matrix[1:]
        similarities = cosine_similarity(resume_vector, job_vectors)[0]

        return similarities

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

        # Prepare job texts
        job_texts = [self.preprocess_job_text(job) for job in jobs]

        # Calculate similarity scores
        similarity_scores = self.calculate_similarity(resume_text, job_texts)

        # Calculate keyword match scores
        results = []
        for i, job in enumerate(jobs):
            keyword_score, matching_keywords = self.calculate_keyword_match(resume_info, job)
            similarity_score = similarity_scores[i]

            # Combined score: 40% keyword match + 60% TF-IDF similarity
            total_score = (keyword_score * 0.4) + (similarity_score * 0.6)

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
            print(f"   匹配度: {result['total_score']}% (关键词: {result['keyword_score']}%, 语义: {result['similarity_score']}%)")
            print(f"   部门: {job['department'] or '未知'}")
            print(f"   薪资: {job['salary'] or '面议'}")
            print(f"   地点: {job['location'] or '未知'}")
            print(f"   发布时间: {job['publish_date'] or '未知'}")
            print(f"   匹配关键词: {', '.join(result['matching_keywords'][:10]) if result['matching_keywords'] else '无'}")
            print(f"   链接: {job['url']}")
            print("-" * 80)
