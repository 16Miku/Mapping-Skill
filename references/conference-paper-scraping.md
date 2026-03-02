# 会议论文爬取指南

> 本文档记录从学术会议平台（如 OpenReview）爬取论文和作者信息的最佳实践。

---

## 概述

学术会议是发现 AI/ML 领域优秀研究者的重要渠道。通过爬取会议论文数据，可以：
1. **发现新晋作者** - 找到刚进入领域的新 PhD
2. **获取最新研究** - 了解前沿研究方向
3. **建立作者档案** - 收集联系方式和学术链接

---

## 支持的会议平台

| 平台 | 会议 | API 支持 |
|------|------|---------|
| **OpenReview** | ICML, NeurIPS, ICLR, AAAI | ✅ 官方 Python SDK |
| **ACL Anthology** | ACL, EMNLP, NAACL | ⚠️ 需要爬虫 |
| **IEEE Xplore** | CVPR, ICCV | ⚠️ 需要爬虫 |
| **ACM DL** | KDD, SIGIR | ⚠️ 需要爬虫 |

---

## OpenReview 平台

### 1. 环境配置

```bash
pip install openreview-py pandas tqdm
```

### 2. 登录认证

OpenReview 需要账号登录才能访问 API：

```python
import openreview

# 方式 1: 直接登录
client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username='your_email@example.com',
    password='your_password'
)

# 方式 2: 使用环境变量
import os
client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=os.getenv('OPENREVIEW_USER'),
    password=os.getenv('OPENREVIEW_PASSWORD')
)
```

### 3. 常用会议 Venue ID

```python
VENUE_IDS = {
    'ICML 2025': 'ICML.cc/2025/Conference',
    'ICML 2024': 'ICML.cc/2024/Conference',
    'NeurIPS 2024': 'NeurIPS.cc/2024/Conference',
    'NeurIPS 2023': 'NeurIPS.cc/2023/Conference',
    'ICLR 2025': 'ICLR.cc/2025/Conference',
    'ICLR 2024': 'ICLR.cc/2024/Conference',
}
```

### 4. 获取论文列表

```python
def get_all_papers(client, venue_id):
    """
    获取会议的所有论文

    Args:
        client: OpenReview 客户端
        venue_id: 会议 ID (如 'ICML.cc/2025/Conference')

    Returns:
        论文 Note 对象列表
    """
    print(f"正在获取 {venue_id} 的论文...")
    submissions = client.get_all_notes(content={'venueid': venue_id})
    print(f"共获取到 {len(submissions)} 篇论文")
    return submissions
```

### 5. 提取论文信息

```python
def extract_paper_info(note):
    """
    从 OpenReview Note 对象提取论文信息

    Args:
        note: OpenReview Note 对象

    Returns:
        论文信息字典
    """
    # OpenReview 的字段结构
    title = note.content.get('title', {}).get('value', '')
    authors = note.content.get('authors', {}).get('value', [])
    author_ids = note.content.get('authorids', {}).get('value', [])

    # 论文链接
    paper_link = f"https://openreview.net/forum?id={note.id}"

    # 对齐作者和 ID
    if len(authors) != len(author_ids):
        author_ids = author_ids + [''] * (len(authors) - len(author_ids))

    return {
        'title': title,
        'authors': list(zip(authors, author_ids)),
        'paper_link': paper_link,
        'note_id': note.id
    }
```

### 6. 获取作者 Profile

```python
def get_author_profile(client, author_id):
    """
    获取作者的 OpenReview Profile

    Args:
        client: OpenReview 客户端
        author_id: 作者 ID (如 '~San_Zhang1')

    Returns:
        Profile 信息字典
    """
    # 跳过 Email ID (没有 Profile)
    if '@' in author_id:
        return {'email': author_id, 'has_profile': False}

    try:
        profile = client.get_profile(author_id)
        return extract_profile_links(profile)
    except Exception as e:
        return {'error': str(e), 'has_profile': False}


def extract_profile_links(profile):
    """
    从 Profile 对象提取各种链接

    Args:
        profile: OpenReview Profile 对象

    Returns:
        链接信息字典
    """
    if not profile or not hasattr(profile, 'content'):
        return {}

    content = profile.content

    return {
        'has_profile': True,
        'email': content.get('preferredEmail', ''),
        'emails': content.get('emails', []),
        'homepage': content.get('homepage', ''),
        'google_scholar': content.get('gscholar', content.get('google_scholar', '')),
        'dblp': content.get('dblp', ''),
        'orcid': content.get('orcid', ''),
        'github': content.get('github', ''),
        'linkedin': content.get('linkedin', ''),
        'profile_link': f"https://openreview.net/profile?id={profile.id}"
    }
```

---

## 华人作者识别

### 姓氏匹配法

```python
# 常见华人姓氏拼音 (Top 100)
CHINESE_SURNAMES = set([
    'li', 'wang', 'zhang', 'liu', 'chen', 'yang', 'huang', 'zhao', 'wu', 'zhou',
    'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'he', 'gao', 'lin', 'luo',
    'cheng', 'zheng', 'xie', 'tang', 'deng', 'feng', 'han', 'cao', 'zeng', 'peng',
    'xiao', 'cai', 'pan', 'tian', 'dong', 'yuan', 'jiang', 'ye', 'wei', 'su',
    # ... 更多姓氏
])

def is_likely_chinese(name, surname_db=None):
    """
    根据姓名判断是否可能是华人

    Args:
        name: 英文姓名 (如 "San Zhang")
        surname_db: 姓氏数据库 (可选)

    Returns:
        是否可能是华人
    """
    if not name:
        return False

    surnames = surname_db or CHINESE_SURNAMES
    parts = name.strip().lower().split()

    if len(parts) < 2:
        return False

    # 检查最后一部分是否是华人姓氏
    last_name = parts[-1]
    return last_name in surnames
```

### 多维度评分法

更精确的识别方法参见 `references/chinese-surnames.md`：

```python
def chinese_score(name, institution='', profile_id=''):
    """
    多维度华人识别评分

    Returns:
        0.0-1.0 的置信度分数
    """
    score = 0.0

    # 1. 姓氏匹配 (40%)
    if is_likely_chinese(name):
        score += 0.4

    # 2. 机构匹配 (35%)
    chinese_institutions = ['tsinghua', 'pku', 'ustc', 'sjtu', 'fudan', ...]
    if any(inst in institution.lower() for inst in chinese_institutions):
        score += 0.35

    # 3. 名字结构 (15%)
    first_name = name.split()[0] if name else ''
    if len(first_name) <= 4 and first_name.isalpha():
        score += 0.15

    # 4. Profile ID 模式 (10%)
    if profile_id and profile_id.startswith('~'):
        score += 0.1

    return min(score, 1.0)
```

---

## 速率限制与错误处理

### OpenReview 限制

OpenReview API 有速率限制，建议：

```python
import time
from tqdm import tqdm

def process_papers_with_rate_limit(client, papers, delay=0.1):
    """
    带速率限制的论文处理

    Args:
        client: OpenReview 客户端
        papers: 论文列表
        delay: 请求间隔 (秒)
    """
    results = []

    for paper in tqdm(papers):
        try:
            info = extract_paper_info(paper)

            for name, author_id in info['authors']:
                profile = get_author_profile(client, author_id)
                results.append({
                    'paper_title': info['title'],
                    'author_name': name,
                    **profile
                })

            time.sleep(delay)

        except Exception as e:
            print(f"Error: {e}")
            continue

    return results
```

---

## 成功案例：ICML 2025

```
论文总数: 3,257 篇
华人作者记录: 8,221 条
包含 Homepage: 6,013 (73%)
包含 Google Scholar: 5,891 (72%)
处理时间: ~12 分钟
```

---

## 参考脚本

完整的代码模板请参见 `scripts/openreview_scraper.py`

---

## 相关文档

- [华人姓氏数据库](./chinese-surnames.md)
- [URL 过滤与优先级规则](./url-priority-rules.md)
- [候选人去重规则](./deduplication-rules.md)
