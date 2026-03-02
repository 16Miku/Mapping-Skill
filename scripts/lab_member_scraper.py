"""
实验室成员批量爬取模板

从实验室人员页面批量爬取成员信息，适用于学术实验室网站。

依赖:
    pip install requests beautifulsoup4

使用示例:
    from lab_member_scraper import LabMemberScraper

    scraper = LabMemberScraper()
    members = scraper.scrape_lab("https://ai.stanford.edu/people/")

    for member in members:
        print(f"{member['name']}: {member['email']}")
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
import json


@dataclass
class MemberProfile:
    """实验室成员资料"""
    name: str = ""
    name_cn: str = ""
    role: str = ""  # PhD, PostDoc, Professor, etc.
    email: str = ""
    affiliation: str = ""
    research_interests: List[str] = field(default_factory=list)
    homepage: str = ""
    google_scholar: str = ""
    github: str = ""
    linkedin: str = ""
    education: List[str] = field(default_factory=list)
    source_url: str = ""

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


class LabMemberScraper:
    """
    实验室成员爬虫

    支持多种常见的学术网站模板:
    - Hugo Academic / Wowchemy
    - Jekyll Scholar
    - 自定义 PHP/HTML 页面
    """

    def __init__(self, delay: float = 0.3):
        """
        初始化爬虫

        Args:
            delay: 请求之间的延迟 (秒)
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_lab(self, lab_url: str) -> List[MemberProfile]:
        """
        爬取实验室成员列表

        Args:
            lab_url: 实验室人员页面 URL

        Returns:
            成员资料列表
        """
        print(f"Scraping: {lab_url}")

        # 获取成员链接列表
        member_urls = self._get_member_urls(lab_url)
        print(f"Found {len(member_urls)} members")

        # 爬取每个成员
        members = []
        for i, url in enumerate(member_urls, 1):
            print(f"[{i}/{len(member_urls)}] {url[:60]}...")
            member = self.scrape_member(url)
            if member.name:
                members.append(member)

            time.sleep(self.delay)

        return members

    def _get_member_urls(self, lab_url: str) -> List[str]:
        """
        从实验室页面提取成员 URL

        Args:
            lab_url: 实验室页面 URL

        Returns:
            成员 URL 列表
        """
        try:
            response = self.session.get(lab_url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            urls = []

            # 常见的成员链接模式
            patterns = [
                r'/author/',
                r'/people/',
                r'/members/',
                r'/~\w+',
                r'/person/',
            ]

            for link in soup.find_all('a', href=True):
                href = link.get('href', '')

                # 检查是否匹配成员模式
                for pattern in patterns:
                    if re.search(pattern, href):
                        # 转换为完整 URL
                        if href.startswith('/'):
                            base_url = '/'.join(lab_url.split('/')[:3])
                            full_url = base_url + href
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            continue

                        # 排除非成员链接
                        if self._is_member_link(full_url, link.get_text()):
                            urls.append(full_url)
                        break

            # 去重
            return list(set(urls))

        except Exception as e:
            print(f"Error getting member URLs: {e}")
            return []

    def _is_member_link(self, url: str, link_text: str) -> bool:
        """
        判断链接是否是成员链接

        Args:
            url: 链接 URL
            link_text: 链接文本

        Returns:
            是否是成员链接
        """
        # 排除关键词
        exclude_keywords = [
            'login', 'sign', 'admin', 'contact',
            'about', 'research', 'publication', 'project',
            'avatar', 'image', 'photo'
        ]

        url_lower = url.lower()
        text_lower = link_text.lower().strip()

        for kw in exclude_keywords:
            if kw in url_lower or kw in text_lower:
                return False

        # 检查链接文本是否像人名
        if text_lower in ['', 'here', 'more', 'read more']:
            return False

        # 通常人名是 2-30 个字符
        if len(text_lower) < 2 or len(text_lower) > 30:
            return False

        return True

    def scrape_member(self, url: str) -> MemberProfile:
        """
        爬取单个成员页面

        Args:
            url: 成员页面 URL

        Returns:
            成员资料
        """
        profile = MemberProfile(source_url=url)

        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取各种信息
            profile.name = self._extract_name(soup)
            profile.email = self._extract_email(soup, response.text)
            profile.role = self._extract_role(soup, response.text)
            profile.research_interests = self._extract_interests(soup)
            profile.homepage = self._extract_homepage(soup, url)
            profile.google_scholar = self._extract_scholar(soup)
            profile.github = self._extract_github(soup)
            profile.linkedin = self._extract_linkedin(soup)
            profile.education = self._extract_education(soup)

        except Exception as e:
            print(f"  Error: {e}")

        return profile

    def _extract_name(self, soup: BeautifulSoup) -> str:
        """提取姓名"""
        # 尝试 title 标签
        title = soup.find('title')
        if title:
            name = title.get_text().split('-')[0].split('|')[0].strip()
            if name and len(name) < 50:
                return name

        # 尝试 h1 标签
        h1 = soup.find('h1')
        if h1:
            name = h1.get_text(strip=True)
            if name and len(name) < 50:
                return name

        return ''

    def _extract_email(self, soup: BeautifulSoup, html: str) -> str:
        """提取邮箱"""
        # 导入解密器
        from cloudflare_email_decoder import extract_cloudflare_email

        # 方法 1: mailto 链接
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')

            if 'mailto:' in href.lower():
                return href.replace('mailto:', '').strip()

            # Cloudflare 保护
            if '/cdn-cgi/l/email-protection' in href:
                email = extract_cloudflare_email(href)
                if email:
                    return email

        # 方法 2: 页面文本
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        match = re.search(email_pattern, html)
        if match:
            return match.group()

        return ''

    def _extract_role(self, soup: BeautifulSoup, html: str) -> str:
        """提取角色/职位"""
        text = html.lower()

        # 角色关键词
        roles = {
            'PhD': ['phd student', 'ph.d. student', 'doctoral student', '博士生'],
            'PostDoc': ['postdoc', 'post-doctoral', 'postdoctoral', '博士后'],
            'Professor': ['professor', 'associate professor', 'assistant professor', '教授'],
            'Master': ['master student', "master's student", '硕士生'],
            'Researcher': ['research scientist', 'researcher', '研究员']
        }

        for role, keywords in roles.items():
            for kw in keywords:
                if kw in text:
                    return role

        return ''

    def _extract_interests(self, soup: BeautifulSoup) -> List[str]:
        """提取研究兴趣"""
        # 常见的研究领域关键词
        keywords = [
            'machine learning', 'deep learning', 'reinforcement learning',
            'natural language processing', 'nlp', 'computer vision',
            'robotics', 'embodied ai', 'multimodal', 'llm', 'transformer',
            'generative ai', 'diffusion model', 'gan', 'vae',
            'graph neural network', 'gnn', 'optimization', 'causality'
        ]

        text = soup.get_text().lower()
        found = []

        for kw in keywords:
            if kw in text:
                found.append(kw)

        return found

    def _extract_homepage(self, soup: BeautifulSoup, current_url: str) -> str:
        """提取个人主页"""
        for link in soup.find_all('a', href=True):
            text = link.get_text().lower()
            href = link.get('href', '')

            if 'homepage' in text or 'personal' in text or 'website' in text:
                if href.startswith('http'):
                    return href

        return current_url

    def _extract_scholar(self, soup: BeautifulSoup) -> str:
        """提取 Google Scholar 链接"""
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'scholar.google' in href.lower():
                return href
        return ''

    def _extract_github(self, soup: BeautifulSoup) -> str:
        """提取 GitHub 链接"""
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            href_lower = href.lower()

            if 'github.com' in href_lower:
                # 排除模板链接
                if 'wowchemy' not in href_lower and 'academic' not in href_lower:
                    return href
        return ''

    def _extract_linkedin(self, soup: BeautifulSoup) -> str:
        """提取 LinkedIn 链接"""
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'linkedin.com/in' in href.lower():
                return href
        return ''

    def _extract_education(self, soup: BeautifulSoup) -> List[str]:
        """提取教育背景"""
        text = soup.get_text()

        # 尝试匹配教育部分
        edu_match = re.search(r'Education\s*\n([\s\S]*?)(?=Research|Experience|Publications|$)', text)

        if edu_match:
            edu_text = edu_match.group(1)
            # 分割成多行
            lines = [l.strip() for l in edu_text.split('\n') if l.strip()]
            # 过滤掉太短的行
            return [l for l in lines if len(l) > 10]

        return []


def save_to_json(members: List[MemberProfile], filepath: str):
    """保存到 JSON 文件"""
    data = [m.to_dict() for m in members]
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(members)} members to {filepath}")


def save_to_csv(members: List[MemberProfile], filepath: str):
    """保存到 CSV 文件"""
    import csv

    fieldnames = [
        'name', 'name_cn', 'role', 'email', 'affiliation',
        'research_interests', 'homepage', 'google_scholar',
        'github', 'linkedin', 'education', 'source_url'
    ]

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for member in members:
            row = member.to_dict()
            row['research_interests'] = ', '.join(row['research_interests'])
            row['education'] = ' | '.join(row['education'])
            writer.writerow(row)

    print(f"Saved {len(members)} members to {filepath}")


# 使用示例
if __name__ == "__main__":
    # 示例: 爬取实验室成员
    lab_url = "https://example.edu/lab/people/"

    scraper = LabMemberScraper(delay=0.3)
    members = scraper.scrape_lab(lab_url)

    # 打印结果
    print(f"\n=== Found {len(members)} members ===")
    for member in members:
        print(f"  {member.name} ({member.role})")
        if member.email:
            print(f"    Email: {member.email}")
        if member.research_interests:
            print(f"    Interests: {', '.join(member.research_interests)}")

    # 保存结果
    save_to_json(members, "lab_members.json")
    save_to_csv(members, "lab_members.csv")
