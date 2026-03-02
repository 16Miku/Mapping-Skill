# 会议论文爬取指南

> 本文档记录从学术会议平台（如 OpenReview）爬取论文和作者信息的完整实践经验，基于 ICML 2025 的真实爬取案例。

---

## 概述

学术会议是发现 AI/ML 领域优秀研究者的重要渠道。通过爬取会议论文数据，可以：
1. **发现新晋作者** - 找到刚进入领域的新 PhD
2. **获取最新研究** - 了解前沿研究方向
3. **建立作者档案** - 收集联系方式和学术链接（Homepage、Scholar、GitHub 等）

---

## 支持的会议平台

| 平台 | 会议 | API 支持 | 推荐方案 |
|------|------|---------|---------|
| **OpenReview** | ICML, NeurIPS, ICLR, AAAI | ✅ 官方 Python SDK | `openreview-py` |
| **ACL Anthology** | ACL, EMNLP, NAACL | ⚠️ 需要爬虫 | `requests + BS4` |
| **IEEE Xplore** | CVPR, ICCV | ⚠️ 需要爬虫 | `requests + BS4` |
| **ACM DL** | KDD, SIGIR | ⚠️ 需要爬虫 | `requests + BS4` |

---

## OpenReview 平台（重点）

### 1. 环境配置

```bash
pip install openreview-py pandas tqdm
```

### 2. 登录认证

OpenReview API 要求注册账号登录。有两种常见方式：

```python
import openreview

# 方式 1: 本地环境 (直接传入 / 环境变量)
import os
client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=os.getenv('OPENREVIEW_USER'),
    password=os.getenv('OPENREVIEW_PASSWORD')
)

# 方式 2: Google Colab 环境 (使用 Secrets)
from google.colab import userdata
client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=userdata.get('OPENREVIEW_USER'),
    password=userdata.get('OPENREVIEW_PASSWORD')
)
```

> **注意**: API base URL 必须是 `https://api2.openreview.net`（v2 API），不要用旧版 `api.openreview.net`。

### 3. 常用会议 Venue ID

```python
VENUE_IDS = {
    # ICML
    'ICML 2025': 'ICML.cc/2025/Conference',
    'ICML 2024': 'ICML.cc/2024/Conference',
    # NeurIPS
    'NeurIPS 2024': 'NeurIPS.cc/2024/Conference',
    'NeurIPS 2023': 'NeurIPS.cc/2023/Conference',
    # ICLR
    'ICLR 2025': 'ICLR.cc/2025/Conference',
    'ICLR 2024': 'ICLR.cc/2024/Conference',
}
```

> **Venue ID 格式规律**: `{会议名}.cc/{年份}/Conference`，可推断其他年份。

### 4. 获取论文列表

```python
# 核心 API 调用 - 一次性获取全部论文
submissions = client.get_all_notes(content={'venueid': VENUE_ID})
print(f"共获取到 {len(submissions)} 篇论文")
```

**实测数据**:
- ICML 2025: 3,257 篇论文，获取耗时约 1-2 分钟

### 5. 论文 Note 对象的字段结构

OpenReview 的 Note 对象字段以嵌套字典存储，需要 `.get('value')` 取值：

```python
# ⚠️ 注意：不是 note.content['title']，而是 note.content['title']['value']
title      = note.content.get('title', {}).get('value', '')
authors    = note.content.get('authors', {}).get('value', [])
author_ids = note.content.get('authorids', {}).get('value', [])
paper_link = f"https://openreview.net/forum?id={note.id}"

# 对齐作者名和 ID（有时长度不一致）
if len(authors) != len(author_ids):
    author_ids = author_ids + [''] * (len(authors) - len(author_ids))
```

### 6. Author ID 的两种形式

Author ID 有两种格式，需要分别处理：

| 类型 | 格式示例 | 含义 | 处理方式 |
|------|---------|------|---------|
| **Profile ID** | `~San_Zhang1` | 已注册 OpenReview 的用户 | 调用 `client.get_profile()` 获取详情 |
| **Email ID** | `user@email.com` | 未注册用户，由共同作者添加 | 直接用作邮箱，跳过 Profile 查询 |

```python
for name, uid in zip(authors, author_ids):
    # Email ID → 直接当邮箱用，跳过 Profile
    if '@' in uid:
        record = {
            'Author Name': name,
            'Email': uid,
            'Profile Link': 'N/A (Email User)',
            # ... 其他字段留空
        }
        continue

    # Profile ID → 查询 Profile 获取详细信息
    profile_link = f"https://openreview.net/profile?id={uid}"
    try:
        profile = client.get_profile(uid)
        links = extract_profile_links(profile)
    except Exception as e:
        links = {}  # Profile 获取失败，可能已被删除
```

### 7. Profile 对象详细字段提取

这是最关键的部分 —— 从 Profile 的 `content` 中提取各种链接和联系方式：

```python
def extract_profile_links(profile):
    """从 Profile 对象提取各种链接和联系方式"""
    data = {
        'Homepage': '',
        'Google Scholar': '',
        'DBLP': '',
        'ORCID': '',
        'GitHub': '',
        'LinkedIn': '',
        'Email': ''
    }

    if not profile or not hasattr(profile, 'content'):
        return data

    content = profile.content

    # -------- 邮箱提取（三级回退） --------
    # 优先用 preferredEmail，其次用 emails 列表第一个
    preferred = content.get('preferredEmail', '')
    emails = content.get('emails', [])
    if preferred:
        data['Email'] = preferred
    elif emails:
        data['Email'] = emails[0]
    else:
        data['Email'] = 'Hidden'  # 用户隐藏了邮箱

    # -------- 个人主页 --------
    data['Homepage'] = content.get('homepage', '')

    # -------- Google Scholar --------
    # ⚠️ OpenReview 字段名不统一！有时叫 gscholar，有时叫 google_scholar
    data['Google Scholar'] = content.get('gscholar', '') or content.get('google_scholar', '')

    # -------- DBLP --------
    data['DBLP'] = content.get('dblp', '')

    # -------- ORCID --------
    # ⚠️ 有时只存了 ORCID ID（纯数字），需要拼接完整 URL
    orcid = content.get('orcid', '')
    if orcid and 'http' not in orcid:
        data['ORCID'] = f"https://orcid.org/{orcid}"
    else:
        data['ORCID'] = orcid

    # -------- GitHub & LinkedIn --------
    data['GitHub'] = content.get('github', '')
    data['LinkedIn'] = content.get('linkedin', '')

    return data
```

**关键踩坑点**:

| 字段 | 问题 | 解决方案 |
|------|------|---------|
| `email` | `preferredEmail` 可能为空 | 三级回退：`preferredEmail → emails[0] → 'Hidden'` |
| `google_scholar` | 字段名不统一 | 同时检查 `gscholar` 和 `google_scholar` |
| `orcid` | 有时只存 ID 不存 URL | 判断是否含 `http`，缺则拼接 `https://orcid.org/` |
| `emails` | 是列表类型 | 取 `emails[0]` 作为主邮箱 |

---

## 华人作者识别

### 简单姓氏匹配法（推荐，速度快）

实际生产中使用的方案 —— 仅靠姓氏判断，简单高效：

```python
# 常见华人姓氏拼音 Top 70
CHINESE_SURNAMES = set([
    'li', 'wang', 'zhang', 'liu', 'chen', 'yang', 'huang', 'zhao', 'wu', 'zhou',
    'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'he', 'gao', 'lin', 'luo', 'cheng',
    'zheng', 'xie', 'tang', 'deng', 'feng', 'han', 'cao', 'zeng', 'peng',
    'xiao', 'cai', 'pan', 'tian', 'dong', 'yuan', 'jiang', 'ye', 'wei', 'su',
    'lu', 'ding', 'ren', 'tan', 'jia', 'liao', 'yao', 'xiong', 'jin', 'wan',
    'xia', 'fu', 'fang', 'bai', 'zou', 'meng', 'qin', 'qiu', 'hou', 'jiang',
    'shi', 'xue', 'mu', 'gu', 'du', 'qian', 'sun', 'song', 'dai', 'fan'
])

def is_likely_chinese(name):
    """判断姓名是否可能是华人（简单姓氏匹配）"""
    if not name:
        return False
    parts = name.strip().lower().split()
    if len(parts) < 2:
        return False
    # 假设姓在最后（英文格式：FirstName LastName）
    return parts[-1] in CHINESE_SURNAMES
```

> **实测效果**: ICML 2025 共 3,257 篇论文，用此方法识别出 8,221 条华人作者记录。

### 多维度评分法（高精度场景）

当需要更精确的识别时，可使用多维度评分，详见 `references/chinese-surnames.md`：

```python
def chinese_score(name, institution='', profile_id=''):
    """多维度华人识别评分 (0.0 - 1.0)"""
    score = 0.0
    # 1. 姓氏匹配 (40%)
    if is_likely_chinese(name): score += 0.4
    # 2. 机构匹配 (35%) - 中国大陆/港澳台高校
    if any(inst in institution.lower() for inst in chinese_institutions): score += 0.35
    # 3. 名字结构 (15%) - 华人名字拼音通常较短
    if len(first_name) <= 4 and first_name.isalpha(): score += 0.15
    # 4. Profile ID 模式 (10%) - ~开头的 OpenReview ID
    if profile_id and profile_id.startswith('~'): score += 0.1
    return min(score, 1.0)  # 阈值 >= 0.5 判定为华人
```

---

## 完整爬取流程

### 端到端示例（基于 ICML 2025 实战代码）

```python
import openreview
import pandas as pd
from tqdm import tqdm
import time

# ============ 配置 ============
VENUE_ID = 'ICML.cc/2025/Conference'
OUTPUT_FILE = 'ICML2025_Chinese_Authors.csv'

# ============ 登录 ============
client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username='...',
    password='...'
)

# ============ 获取论文 ============
submissions = client.get_all_notes(content={'venueid': VENUE_ID})
print(f"共获取到 {len(submissions)} 篇论文")

# ============ 遍历提取 ============
results = []

for note in tqdm(submissions):
    try:
        title = note.content.get('title', {}).get('value', '')
        authors = note.content.get('authors', {}).get('value', [])
        author_ids = note.content.get('authorids', {}).get('value', [])
        paper_link = f"https://openreview.net/forum?id={note.id}"

        # 对齐
        if len(authors) != len(author_ids):
            author_ids += [''] * (len(authors) - len(author_ids))

        for name, uid in zip(authors, author_ids):
            # 筛选华人
            if not is_likely_chinese(name):
                continue

            # Email ID → 直接记录
            if '@' in uid:
                results.append({
                    'Paper Title': title,
                    'Author Name': name,
                    'OpenReview Link': paper_link,
                    'Profile Link': 'N/A (Email User)',
                    'Email': uid,
                    'Homepage': '', 'Google Scholar': '', 'DBLP': '',
                    'ORCID': '', 'GitHub': ''
                })
                continue

            # Profile ID → 查询详情
            profile_link = f"https://openreview.net/profile?id={uid}"
            try:
                profile = client.get_profile(uid)
                links = extract_profile_links(profile)
                results.append({
                    'Paper Title': title,
                    'Author Name': name,
                    'OpenReview Link': paper_link,
                    'Profile Link': profile_link,
                    **links
                })
            except Exception:
                results.append({
                    'Paper Title': title,
                    'Author Name': name,
                    'OpenReview Link': paper_link,
                    'Profile Link': profile_link,
                    'Email': 'Error Fetching Profile',
                    'Homepage': '', 'Google Scholar': '', 'DBLP': '',
                    'ORCID': '', 'GitHub': ''
                })

    except Exception:
        continue

# ============ 保存 ============
df = pd.DataFrame(results)
df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
print(f"总计: {len(df)} 条")
print(f"Homepage: {len(df[df['Homepage'] != ''])}")
print(f"Google Scholar: {len(df[df['Google Scholar'] != ''])}")
```

---

## 性能与优化

### 实测性能基准（ICML 2025）

```
平台: Google Colab (免费版)
论文总数: 3,257 篇
华人作者记录: 8,221 条
处理速度: 4.73 it/s (每篇论文约 0.21 秒)
总耗时: 11 分 29 秒
包含 Homepage: 6,013 (73%)
包含 Google Scholar: 5,891 (72%)
```

### 优化建议

1. **作者缓存**: 同一作者可能出现在多篇论文中，缓存 Profile 可减少 API 调用

```python
profile_cache = {}
if uid not in profile_cache:
    profile_cache[uid] = client.get_profile(uid)
profile = profile_cache[uid]
```

2. **调试模式**: 先用少量论文验证逻辑

```python
# 快速测试 50 篇
target_submissions = submissions[:50]
# 全量运行
target_submissions = submissions
```

3. **速率控制**: OpenReview 有速率限制，建议加 `time.sleep(0.05~0.1)`，但实测不加也能跑通

---

## Google Colab 部署要点

在 Colab 环境下使用有几个特殊注意事项：

```python
# 1. Secrets 管理 (不要硬编码密码！)
from google.colab import userdata
user = userdata.get('OPENREVIEW_USER')
password = userdata.get('OPENREVIEW_PASSWORD')

# 2. 文件下载 (爬取完自动弹出下载)
from google.colab import files
files.download(OUTPUT_FILE)

# 3. CSV 编码 (Excel 兼容)
df.to_csv(OUTPUT_FILE, encoding='utf-8-sig')  # 带 BOM 头
```

---

## 参考脚本

完整的面向对象代码模板请参见 `scripts/openreview_scraper.py`

---

## 相关文档

- [华人姓氏数据库](./chinese-surnames.md) - 200+ 姓氏 + 港台粤语变体
- [URL 过滤与优先级规则](./url-priority-rules.md)
- [候选人去重规则](./deduplication-rules.md)
