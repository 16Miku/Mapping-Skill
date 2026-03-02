"""
实验室成员批量爬取模板

从实验室人员页面批量爬取成员信息，适用于学术实验室网站。
基于 LAMDA (南大) 和 TongClass (清华-北大) 实战验证。

实战案例:
- LAMDA: 108 名博士生，URL 格式 /Name/ (ASP.NET .ashx 页面)
- TongClass: 154 名成员，URL 格式 /author/Name/ (Hugo Academic)

依赖:
    pip install requests beautifulsoup4

使用示例:
    from lab_member_scraper import LabMemberScraper

    scraper = LabMemberScraper()
    members = scraper.scrape_lab("https://www.lamda.nju.edu.cn/CH.PhD_student.ashx")

    for member in members:
        print(f"{member.name}: {member.email}")
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from urllib.parse import urljoin
import json


# ==================== 数据模型 ====================

@dataclass
class MemberProfile:
    """实验室成员资料"""
    name: str = ""           # 英文名或拼音名
    name_cn: str = ""        # 中文名
    role: str = ""           # PhD, PostDoc, Professor, etc.
    email: str = ""
    affiliation: str = ""
    research_interests: List[str] = field(default_factory=list)
    bio: str = ""            # 个人介绍
    homepage: str = ""
    google_scholar: str = ""
    github: str = ""
    linkedin: str = ""
    zhihu: str = ""
    bilibili: str = ""
    twitter: str = ""
    publications: List[str] = field(default_factory=list)
    education: List[str] = field(default_factory=list)
    source_url: str = ""

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


# ==================== 爬虫类 ====================

class LabMemberScraper:
    """
    实验室成员爬虫

    支持多种常见的学术网站模板:
    - Hugo Academic / Wowchemy (TongClass 等)
    - Jekyll Scholar
    - 自定义 PHP/HTML/ASP.NET 页面 (LAMDA 等)

    实战踩坑总结:
    1. 列表页的导航链接会混入成员链接 → 需要中文名长度过滤 + URL 关键词排除
    2. 中国高校邮箱常用 [at] 混淆 → 需要正则匹配
    3. .edu.cn 域名常有 SSL 握手失败 → 需要异常捕获
    4. 论文列表通常在 "Publications" 标题下的 ul/ol 中
    """

    # 列表页中需要排除的 URL 关键词（导航链接噪声）
    EXCLUDE_URL_KEYWORDS = [
        'login', 'sign', 'admin', 'contact', 'about',
        'research', 'publication', 'project', 'avatar', 'image', 'photo',
        'MainPage', 'Pub.ashx', 'App.ashx', 'Data.ashx', 'Lib.ashx',
        'Seminar', 'Link.ashx', 'Album', 'index',
    ]

    # 已知有 SSL 问题的域名
    SSL_PROBLEM_DOMAINS = ['www.nju.edu.cn', 'www.tsinghua.edu.cn']

    def __init__(self, delay: float = 0.5, base_url: str = ""):
        """
        初始化爬虫

        Args:
            delay: 请求之间的延迟 (秒)
            base_url: 网站根 URL (用于拼接相对链接)
        """
        self.delay = delay
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def scrape_lab(self, lab_url: str, max_members: Optional[int] = None) -> List[MemberProfile]:
        """
        爬取实验室成员列表（两阶段：列表页 → 详情页）

        Args:
            lab_url: 实验室人员页面 URL
            max_members: 限制爬取数量 (用于调试)

        Returns:
            成员资料列表
        """
        # 自动推断 base_url
        if not self.base_url:
            self.base_url = '/'.join(lab_url.split('/')[:3])

        print(f"正在获取成员列表: {lab_url}")

        # 阶段 1: 获取成员链接列表
        member_entries = self._get_member_entries(lab_url)
        print(f"初步提取到 {len(member_entries)} 名成员")

        if max_members:
            member_entries = member_entries[:max_members]
            print(f"⚠️ 调试模式：只处理前 {max_members} 名")

        # 阶段 2: 逐个爬取详情页
        members = []
        for i, entry in enumerate(member_entries, 1):
            print(f"[{i}/{len(member_entries)}] {entry.get('name', 'Unknown')} ({entry['url'][:60]}...)")

            member = self._scrape_detail_page(entry)
            if member.name or member.name_cn:
                members.append(member)

            time.sleep(self.delay)

        print(f"\n成功爬取 {len(members)} 名成员信息")
        return members

    def _get_member_entries(self, lab_url: str) -> List[Dict]:
        """
        从实验室页面提取成员条目 (名字 + URL)

        实战踩坑:
        - LAMDA 的列表页混入了大量导航链接 (MainPage, Pub, App 等)
        - 用中文名长度 (2-5字) 过滤可以去除大部分噪声
        - 需要同时支持 /author/Name/ 和 /Name/ 两种 URL 模式
        """
        try:
            response = self.session.get(lab_url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # 缩小搜索范围：优先从 content div 中查找
            content_div = soup.find('div', id='content') or soup.body
            if not content_div:
                return []

            entries = []
            seen_urls: Set[str] = set()

            for link in content_div.find_all('a', href=True):
                href = link.get('href', '')
                name = self._clean_text(link.get_text())

                # 基本验证
                if not href or not name:
                    continue

                # 排除导航链接
                if self._is_excluded_url(href):
                    continue

                # 中文名过滤：2-5 个字符（中文名通常 2-4 个字）
                # 英文名过滤：至少 2 个字符
                if self._is_chinese(name):
                    if len(name) < 2 or len(name) > 5:
                        continue
                else:
                    if len(name) < 2 or len(name) > 40:
                        continue

                # 拼接完整 URL
                full_url = urljoin(self.base_url, href)

                # 去重
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # 检测该链接是否可能跳到外部 (排除外部链接)
                if not full_url.startswith(self.base_url) and '.edu' not in full_url:
                    continue

                entries.append({
                    'name': name,
                    'url': full_url,
                })

            return entries

        except Exception as e:
            print(f"获取成员列表失败: {e}")
            return []

    def _scrape_detail_page(self, entry: Dict) -> MemberProfile:
        """
        爬取单个成员的详情页

        提取顺序: 姓名 → 邮箱 → 研究方向 → 社交链接 → 论文 → Bio
        """
        url = entry['url']
        name_from_list = entry.get('name', '')

        profile = MemberProfile(source_url=url)

        # 预设列表页获取的名字
        if self._is_chinese(name_from_list):
            profile.name_cn = name_from_list
        else:
            profile.name = name_from_list

        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()

            # 1. 姓名提取 (补充详情页信息)
            if not profile.name:
                profile.name = self._extract_name(soup, url)

            # 2. 邮箱提取 (支持多种混淆方式)
            profile.email = self._extract_email(soup, text_content)

            # 3. 研究方向
            profile.research_interests = self._extract_interests(soup, text_content)

            # 4. 角色/职位
            profile.role = self._extract_role(text_content)

            # 5. 社交链接 (一次遍历提取全部)
            self._extract_all_links(soup, profile)

            # 6. 论文列表
            profile.publications = self._extract_publications(soup)

            # 7. 个人介绍
            profile.bio = self._extract_bio(soup, text_content)

            # 8. 教育背景
            profile.education = self._extract_education(soup, text_content)

        except requests.exceptions.SSLError:
            print(f"    [!] SSL 错误，跳过: {url}")
        except requests.exceptions.Timeout:
            print(f"    [!] 超时，跳过: {url}")
        except Exception as e:
            print(f"    [!] 爬取失败: {e}")

        return profile

    # ==================== 提取方法 ====================

    def _extract_name(self, soup: BeautifulSoup, url: str) -> str:
        """
        提取英文名

        优先级:
        1. <title> 标签 (通常是 "Name - Lab")
        2. <h1> 标签
        3. URL 路径 (如 /zhangzn/ → zhangzn，作为保底)
        """
        # 尝试 title 标签
        title = soup.find('title')
        if title:
            name = title.get_text().split('-')[0].split('|')[0].strip()
            if name and 2 <= len(name) <= 50:
                return name

        # 尝试 h1 标签
        h1 = soup.find('h1')
        if h1:
            name = h1.get_text(strip=True)
            if name and 2 <= len(name) <= 50:
                return name

        # 从 URL 提取 (保底方案)
        url_name = url.strip('/').split('/')[-1]
        if url_name and url_name.isalpha() and len(url_name) >= 2:
            return url_name

        return ''

    def _extract_email(self, soup: BeautifulSoup, text: str) -> str:
        """
        综合邮箱提取，支持多种混淆方式

        优先级:
        1. mailto: 链接 (最可靠)
        2. Cloudflare XOR 加密
        3. [at] / (at) 文本混淆 (中国高校常见)
        4. 纯文本正则匹配 (最后手段)
        """
        # 1. mailto 链接
        mailto = soup.select_one('a[href^="mailto:"]')
        if mailto:
            return mailto['href'].replace('mailto:', '').strip()

        # 2. Cloudflare 保护
        cf_link = soup.select_one('a[href*="/cdn-cgi/l/email-protection"]')
        if cf_link:
            try:
                from cloudflare_email_decoder import extract_cloudflare_email
                email = extract_cloudflare_email(cf_link['href'])
                if email:
                    return email
            except ImportError:
                pass

        # 3. [at] / (at) 混淆 (LAMDA 等中国高校常见)
        at_pattern = r'([a-zA-Z0-9._-]+)\s*(?:\[at\]|\(at\))\s*([a-zA-Z0-9._-]+\.[a-zA-Z]{2,})'
        match = re.search(at_pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}@{match.group(2)}"

        # 4. 纯文本正则
        email_pattern = r'[\w.-]+@[\w.-]+\.\w+'
        match = re.search(email_pattern, text)
        if match:
            email = match.group()
            # 排除常见的非个人邮箱
            if not any(x in email for x in ['example.com', 'noreply', 'contact@']):
                return email

        return ''

    def _extract_role(self, text: str) -> str:
        """提取角色/职位"""
        text_lower = text.lower()

        roles = {
            'PhD': ['phd student', 'ph.d. student', 'doctoral student', '博士生', 'ph.d. candidate'],
            'PostDoc': ['postdoc', 'post-doctoral', 'postdoctoral', '博士后'],
            'Professor': ['professor', 'associate professor', 'assistant professor', '教授', '副教授', '助理教授'],
            'Master': ['master student', "master's student", '硕士生'],
            'Researcher': ['research scientist', 'researcher', '研究员', '研究助理']
        }

        for role, keywords in roles.items():
            for kw in keywords:
                if kw in text_lower:
                    return role

        return ''

    def _extract_interests(self, soup: BeautifulSoup, text: str) -> List[str]:
        """
        提取研究方向

        策略:
        1. 查找 "Research Interests:" 后的文本
        2. 查找 "Interests" 标题下的列表
        3. 关键词匹配 (保底)
        """
        # 策略 1: "Research Interests: xxx"
        interest_match = re.search(r'Research\s*Interests?:?\s*(.{10,200})', text, re.IGNORECASE)
        if interest_match:
            raw = interest_match.group(1).split('\n')[0].strip()
            interests = [s.strip() for s in re.split(r'[,;，；、]', raw) if s.strip()]
            if interests:
                return interests

        # 策略 2: "Interests" 标题后的列表 (Hugo Academic)
        interests_match = re.search(r'Interests\s*\n([\s\S]*?)(?=Education|Publications|$)', text)
        if interests_match:
            raw = interests_match.group(1).strip()
            interests = [s.strip() for s in raw.split('\n') if s.strip() and s.strip() not in ['•', '*', '-']]
            if interests:
                return interests

        return []

    def _extract_all_links(self, soup: BeautifulSoup, profile: MemberProfile):
        """
        一次遍历提取所有社交/学术链接

        排除已知的模板链接 (wowchemy, academic-theme 等)
        """
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            href_lower = href.lower()

            # 排除无效链接
            if '%e6%97%a0' in href:  # URL 编码的"无"
                continue

            if 'github.com' in href_lower and 'wowchemy' not in href_lower and 'academic' not in href_lower:
                if not profile.github:
                    profile.github = href
            elif 'scholar.google' in href_lower:
                if not profile.google_scholar:
                    profile.google_scholar = href
            elif 'linkedin.com' in href_lower:
                if not profile.linkedin:
                    profile.linkedin = href
            elif 'zhihu.com' in href_lower:
                if not profile.zhihu:
                    profile.zhihu = href
            elif 'bilibili.com' in href_lower:
                if not profile.bilibili:
                    profile.bilibili = href
            elif 'twitter.com' in href_lower or 'x.com' in href_lower:
                if not profile.twitter:
                    profile.twitter = href

    def _extract_publications(self, soup: BeautifulSoup) -> List[str]:
        """
        提取论文列表

        策略: 找 "Publications/Conference/Journal" 标题后的 ul/ol 列表
        LAMDA 经验: 标题可能是 h1-h4/strong/b，列表可能在 div 内嵌套

        Returns:
            论文标题列表 (最多 5 篇)
        """
        # 查找包含 Publication 关键词的标题标签
        headers = soup.find_all(
            ['h1', 'h2', 'h3', 'h4', 'strong', 'b'],
            string=re.compile(r'Publication|Conference|Journal|Selected\s+Paper', re.IGNORECASE)
        )

        for header in headers:
            # 寻找标题后的 ul/ol/div
            next_elem = header.find_next_sibling(['ul', 'ol', 'div'])
            if not next_elem:
                continue

            target_list = None
            if next_elem.name in ['ul', 'ol']:
                target_list = next_elem
            elif next_elem.name == 'div':
                inner_ul = next_elem.find(['ul', 'ol'])
                if inner_ul:
                    target_list = inner_ul

            if not target_list:
                continue

            pubs = []
            for item in target_list.find_all('li'):
                text = self._clean_text(item.get_text())
                link_tag = item.find('a')
                link = urljoin(self.base_url, link_tag['href']) if link_tag else ''

                # 过滤太短的条目（不太可能是论文标题）
                if len(text) > 20:
                    if link:
                        pubs.append(f"{text} [{link}]")
                    else:
                        pubs.append(text)

                if len(pubs) >= 5:
                    break

            if pubs:
                return pubs

        return []

    def _extract_bio(self, soup: BeautifulSoup, text: str) -> str:
        """
        提取个人简介

        策略: 查找 "Biography/Introduction/About" 标题后的第一个 <p>
        """
        bio_header = soup.find(string=re.compile(r'Biography|Introduction|About\s+Me', re.IGNORECASE))
        if bio_header:
            parent = bio_header.find_parent()
            if parent:
                bio_p = parent.find_next_sibling('p')
                if bio_p:
                    return self._clean_text(bio_p.get_text())

        return ''

    def _extract_education(self, soup: BeautifulSoup, text: str) -> List[str]:
        """提取教育背景"""
        edu_match = re.search(r'Education\s*\n([\s\S]*?)(?=Research|Experience|Publications|$)', text)

        if edu_match:
            edu_text = edu_match.group(1)
            lines = [l.strip() for l in edu_text.split('\n') if l.strip()]
            return [l for l in lines if len(l) > 10]

        return []

    # ==================== 工具方法 ====================

    @staticmethod
    def _clean_text(text: str) -> str:
        """清洗文本：去除多余空格、换行"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def _is_chinese(text: str) -> bool:
        """检测文本是否包含中文字符"""
        return bool(re.search(r'[\u4e00-\u9fff]', text))

    def _is_excluded_url(self, href: str) -> bool:
        """检测 URL 是否应该被排除"""
        href_lower = href.lower()

        # 已知排除关键词
        for kw in self.EXCLUDE_URL_KEYWORDS:
            if kw.lower() in href_lower:
                return True

        # SSL 问题域名
        for domain in self.SSL_PROBLEM_DOMAINS:
            if domain in href_lower:
                return True

        return False


# ==================== 保存工具 ====================

def save_to_json(members: List[MemberProfile], filepath: str):
    """保存到 JSON 文件"""
    data = [m.to_dict() for m in members]
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存 {len(members)} 名成员到 {filepath}")


def save_to_csv(members: List[MemberProfile], filepath: str):
    """保存到 CSV 文件 (Excel 兼容)"""
    import csv

    fieldnames = [
        'name', 'name_cn', 'role', 'email', 'affiliation',
        'research_interests', 'bio', 'homepage', 'google_scholar',
        'github', 'linkedin', 'zhihu', 'bilibili', 'twitter',
        'publications', 'education', 'source_url'
    ]

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for member in members:
            row = member.to_dict()
            row['research_interests'] = ', '.join(row['research_interests'])
            row['publications'] = ' | '.join(row['publications'])
            row['education'] = ' | '.join(row['education'])
            writer.writerow(row)

    print(f"✅ 已保存 {len(members)} 名成员到 {filepath}")


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 示例 1: 爬取 LAMDA 博士生
    # scraper = LabMemberScraper(delay=1.0, base_url="https://www.lamda.nju.edu.cn")
    # members = scraper.scrape_lab("https://www.lamda.nju.edu.cn/CH.PhD_student.ashx")

    # 示例 2: 爬取 TongClass 成员
    # scraper = LabMemberScraper(delay=0.3, base_url="https://tongclass.ac.cn")
    # members = scraper.scrape_lab("https://tongclass.ac.cn/people/")

    # 示例 3: 通用实验室页面
    lab_url = "https://example.edu/lab/people/"
    scraper = LabMemberScraper(delay=0.5)
    members = scraper.scrape_lab(lab_url, max_members=5)  # 调试模式

    # 打印结果
    print(f"\n=== 共 {len(members)} 名成员 ===")
    for member in members:
        name = member.name_cn or member.name
        print(f"  {name} ({member.role})")
        if member.email:
            print(f"    Email: {member.email}")
        if member.research_interests:
            print(f"    Interests: {', '.join(member.research_interests)}")

    # 保存结果
    # save_to_json(members, "lab_members.json")
    # save_to_csv(members, "lab_members.csv")
