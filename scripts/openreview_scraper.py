"""
OpenReview 会议论文爬虫模板

从 OpenReview 平台爬取会议论文和作者信息，支持华人作者识别。

依赖:
    pip install openreview-py pandas tqdm

使用示例:
    from openreview_scraper import OpenReviewScraper

    scraper = OpenReviewScraper(username, password)
    results = scraper.scrape_conference('ICML.cc/2025/Conference')
    scraper.save_to_csv(results, 'icml2025_chinese.csv')
"""

import time
import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field, asdict
from tqdm import tqdm

try:
    import openreview
    import openreview.api
except ImportError:
    raise ImportError("请安装 openreview-py: pip install openreview-py")


# ==================== 数据模型 ====================

@dataclass
class AuthorInfo:
    """作者信息"""
    paper_title: str = ""
    paper_link: str = ""
    author_name: str = ""
    author_id: str = ""
    email: str = ""
    homepage: str = ""
    google_scholar: str = ""
    dblp: str = ""
    orcid: str = ""
    github: str = ""
    linkedin: str = ""
    profile_link: str = ""
    is_chinese: bool = False
    chinese_confidence: float = 0.0


# ==================== 华人姓氏数据库 ====================

CHINESE_SURNAMES: Set[str] = set([
    # Top 20
    'li', 'wang', 'zhang', 'liu', 'chen', 'yang', 'huang', 'zhao', 'wu', 'zhou',
    'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'he', 'gao', 'lin', 'luo',
    # 21-40
    'cheng', 'zheng', 'xie', 'tang', 'deng', 'feng', 'han', 'cao', 'zeng', 'peng',
    'xiao', 'cai', 'pan', 'tian', 'dong', 'yuan', 'jiang', 'ye', 'wei', 'su',
    # 41-60
    'lu', 'ding', 'ren', 'tan', 'jia', 'liao', 'yao', 'xiong', 'jin', 'wan',
    'xia', 'fu', 'fang', 'bai', 'zou', 'meng', 'qin', 'qiu', 'hou', 'jiang',
    # 港台拼音变体
    'tsai', 'chang', 'chien', 'chung', 'hsu', 'hsieh', 'liang',
])


# ==================== OpenReview 爬虫类 ====================

class OpenReviewScraper:
    """OpenReview 会议论文爬虫"""

    VENUE_IDS = {
        'ICML 2025': 'ICML.cc/2025/Conference',
        'ICML 2024': 'ICML.cc/2024/Conference',
        'NeurIPS 2024': 'NeurIPS.cc/2024/Conference',
        'ICLR 2025': 'ICLR.cc/2025/Conference',
    }

    def __init__(self, username: str, password: str, baseurl: str = 'https://api2.openreview.net'):
        self.client = openreview.api.OpenReviewClient(
            baseurl=baseurl,
            username=username,
            password=password
        )
        self.results: List[AuthorInfo] = []

    def get_all_papers(self, venue_id: str) -> List:
        """获取会议所有论文"""
        print(f"正在获取 {venue_id} 的论文...")
        submissions = self.client.get_all_notes(content={'venueid': venue_id})
        print(f"✅ 共获取到 {len(submissions)} 篇论文")
        return submissions

    def is_chinese_author(self, name: str, institution: str = "") -> tuple:
        """判断是否为华人作者"""
        if not name:
            return False, 0.0

        score = 0.0
        parts = name.strip().lower().split()

        if len(parts) < 2:
            return False, 0.0

        # 姓氏匹配 (40%)
        if parts[-1] in CHINESE_SURNAMES:
            score += 0.4

        # 机构匹配 (35%)
        chinese_insts = ['tsinghua', 'pku', 'ustc', 'sjtu', 'fudan', 'zhejiang']
        if any(i in institution.lower() for i in chinese_insts):
            score += 0.35

        # 名字结构 (15%)
        if len(parts[0]) <= 4 and parts[0].isalpha():
            score += 0.15

        return score >= 0.5, min(score, 1.0)

    def extract_profile_links(self, profile) -> Dict[str, str]:
        """从 Profile 对象提取链接"""
        data = {'email': '', 'homepage': '', 'google_scholar': '', 'dblp': '', 'orcid': '', 'github': '', 'linkedin': '', 'profile_link': ''}

        if not profile or not hasattr(profile, 'content'):
            return data

        content = profile.content
        data['email'] = content.get('preferredEmail', '')
        data['homepage'] = content.get('homepage', '')
        data['google_scholar'] = content.get('gscholar', '')
        data['dblp'] = content.get('dblp', '')
        data['github'] = content.get('github', '')
        data['linkedin'] = content.get('linkedin', '')

        if hasattr(profile, 'id'):
            data['profile_link'] = f"https://openreview.net/profile?id={profile.id}"

        return data

    def scrape_conference(self, venue_id: str, chinese_only: bool = True, delay: float = 0.1, max_papers: Optional[int] = None) -> List[AuthorInfo]:
        """爬取会议论文和作者信息"""
        papers = self.get_all_papers(venue_id)
        if max_papers:
            papers = papers[:max_papers]

        self.results = []

        for note in tqdm(papers, desc="处理论文"):
            try:
                title = note.content.get('title', {}).get('value', '')
                authors = note.content.get('authors', {}).get('value', [])
                author_ids = note.content.get('authorids', {}).get('value', [])
                paper_link = f"https://openreview.net/forum?id={note.id}"

                if len(authors) != len(author_ids):
                    author_ids = author_ids + [''] * (len(authors) - len(author_ids))

                for name, author_id in zip(authors, author_ids):
                    is_chinese, confidence = self.is_chinese_author(name)
                    if chinese_only and not is_chinese:
                        continue

                    author_info = AuthorInfo(
                        paper_title=title, paper_link=paper_link,
                        author_name=name, author_id=author_id,
                        is_chinese=is_chinese, chinese_confidence=confidence
                    )

                    if author_id and not author_id.startswith('@'):
                        try:
                            profile = self.client.get_profile(author_id)
                            links = self.extract_profile_links(profile)
                            for k, v in links.items():
                                setattr(author_info, k, v)
                        except Exception:
                            pass
                    elif '@' in author_id:
                        author_info.email = author_id

                    self.results.append(author_info)
                    if delay > 0:
                        time.sleep(delay)

            except Exception as e:
                continue

        return self.results

    def save_to_csv(self, filename: str):
        """保存结果到 CSV"""
        import pandas as pd
        if not self.results:
            return

        df = pd.DataFrame([asdict(r) for r in self.results])
        print(f"\n总计: {len(df)} 条 | Homepage: {len(df[df['homepage'] != ''])} | Scholar: {len(df[df['google_scholar'] != ''])}")
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ 已保存: {filename}")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    username = os.getenv("OPENREVIEW_USER", "")
    password = os.getenv("OPENREVIEW_PASSWORD", "")

    if not username or not password:
        print("请设置 OPENREVIEW_USER 和 OPENREVIEW_PASSWORD")
        exit(1)

    scraper = OpenReviewScraper(username, password)
    results = scraper.scrape_conference('ICML.cc/2025/Conference', max_papers=50)
    scraper.save_to_csv('icml2025_test.csv')
