# 参考脚本说明

本目录包含可复用的 Python 爬虫脚本模板，供开发者参考和集成到自己的项目中。

---

## 文件说明

| 文件 | 功能 | 依赖 |
|------|------|------|
| `serper_search.py` | Serper API 搜索模板 | httpx, python-dotenv |
| `httpx_scraper.py` | 异步 HTTP 爬虫 | httpx |
| `cloudflare_email_decoder.py` | Cloudflare 邮箱解密 | 无 |
| `lab_member_scraper.py` | 实验室成员批量爬取 | requests, beautifulsoup4 |
| **`openreview_scraper.py`** | **OpenReview 会议论文爬取** | **openreview-py, pandas** |

---

## 使用方式

这些脚本是**参考实现**，不是可执行的包。请根据实际需求：

1. **复制相关代码**到你的项目
2. **根据目标网站**调整解析逻辑
3. **配置环境变量**和 API Keys

---

## 快速开始

### 1. 安装依赖

```bash
pip install requests beautifulsoup4 httpx python-dotenv
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
SERPER_API_KEY=your_serper_api_key
```

### 3. 使用示例

```python
# 使用 Serper 搜索
from serper_search import serper_search
results = await serper_search("reinforcement learning PhD", api_key)

# 使用 Cloudflare 邮箱解密
from cloudflare_email_decoder import decode_cloudflare_email
email = decode_cloudflare_email("f493919e85c6c5...")

# 使用异步爬虫
from httpx_scraper import batch_scrape
results = await batch_scrape(urls, max_concurrent=5)

# 使用 OpenReview 会议爬虫
from openreview_scraper import OpenReviewScraper
scraper = OpenReviewScraper(username, password)
results = scraper.scrape_conference('ICML.cc/2025/Conference')
scraper.save_to_csv('icml2025.csv')
```

---

## 注意事项

1. **遵守网站 robots.txt** - 检查网站是否允许爬取
2. **合理使用数据** - 仅用于人才搜索等正当目的
3. **保护隐私** - 不要公开传播个人联系信息
4. **控制频率** - 添加适当延迟避免对服务器造成压力
5. **遵守法律** - 确保爬取行为符合当地法律法规

---

## 相关文档

- [Python 爬虫技术指南](../references/python-scraping-guide.md)
- [URL 过滤与优先级规则](../references/url-priority-rules.md)
- [反爬虫解决方案](../references/anti-scraping-solutions.md)
- [会议论文爬取指南](../references/conference-paper-scraping.md)
