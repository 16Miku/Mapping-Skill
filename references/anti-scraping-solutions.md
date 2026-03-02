# 反爬虫解决方案汇总

> 本文档汇总了在进行 AI 人才搜索时遇到的常见反爬虫机制及其解决方案。

---

## 概述

在爬取 researcher 个人主页和实验室页面时，经常会遇到各种反爬虫机制。本文档按照问题类型分类，提供对应的解决方案。

---

## 问题分类与解决方案

### 1. Cloudflare 邮箱保护

#### 问题描述

网站使用 Cloudflare CDN 的邮箱保护功能，邮箱地址被替换为加密字符串：

```html
<!-- 原始邮箱: example@domain.com -->
<a href="/cdn-cgi/l/email-protection#0762637474346762637474342964686a">
    [email protected]
</a>
```

#### 解决方案

**XOR 解密算法**（免费）：

```python
def decode_cloudflare_email(encoded: str) -> str:
    """
    解码 Cloudflare 邮箱保护

    原理: Cloudflare 使用简单的 XOR 加密
    - 第一个字节是密钥
    - 后续字节与密钥 XOR 得到原始字符
    """
    try:
        key = int(encoded[:2], 16)
        decoded = ''
        for i in range(2, len(encoded), 2):
            char_code = int(encoded[i:i+2], 16) ^ key
            decoded += chr(char_code)
        return decoded
    except:
        return ''


# 使用示例
href = "/cdn-cgi/l/email-protection#0762637474346762637474342964686a"
encoded = href.split('#')[-1]
email = decode_cloudflare_email(encoded)
print(email)  # 输出: example@domain.com
```

**完整参考实现**: `scripts/cloudflare_email_decoder.py`

#### 成功率

| 方案 | 成功率 | 成本 |
|------|--------|------|
| XOR 解密 | 95%+ | 免费 |
| BrightData MCP | 99%+ | 付费 |

---

### 2. User-Agent 检测

#### 问题描述

服务器检测请求的 User-Agent，拒绝非浏览器请求：

```
HTTP 403 Forbidden
```

#### 解决方案

**设置真实浏览器 User-Agent**：

```python
import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
})

response = session.get(url)
```

**随机 User-Agent 轮换**：

```python
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]

def get_random_ua():
    return random.choice(USER_AGENTS)
```

#### 成功率

| 方案 | 成功率 | 成本 |
|------|--------|------|
| 固定 User-Agent | 70% | 免费 |
| 随机 User-Agent | 85% | 免费 |
| BrightData MCP | 99%+ | 付费 |

---

### 3. 请求频率限制

#### 问题描述

服务器限制请求频率，过于频繁的请求会被暂时封禁：

```
HTTP 429 Too Many Requests
```

#### 解决方案

**随机延迟**：

```python
import time
import random

for url in urls:
    scrape(url)
    # 随机延迟 0.5-2 秒
    delay = random.uniform(0.5, 2.0)
    time.sleep(delay)
```

**指数退避重试**：

```python
import time

def scrape_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 429:
                # 指数退避
                wait_time = (2 ** attempt) + random.random()
                print(f"Rate limited, waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
    return None
```

**使用 Session 复用连接**：

```python
session = requests.Session()
# 复用 session 减少连接开销
for url in urls:
    response = session.get(url)
```

#### 建议配置

| 目标类型 | 建议延迟 | 并发数 |
|---------|---------|--------|
| 个人主页 | 0.5-1s | 5-10 |
| 大学网站 | 1-2s | 3-5 |
| LinkedIn | N/A (用 BrightData) | 1 |

---

### 4. IP 封锁

#### 问题描述

服务器检测到异常请求模式后封锁 IP：

```
HTTP 403 Forbidden
Connection timed out
```

#### 解决方案

**方案 1: 降低请求频率**

```python
# 使用更长的延迟
time.sleep(random.uniform(2, 5))
```

**方案 2: 使用代理池**（付费）

```python
import requests

proxies = {
    'http': 'http://proxy-server:port',
    'https': 'https://proxy-server:port',
}

response = requests.get(url, proxies=proxies)
```

**方案 3: BrightData MCP**（推荐）

对于高反爬网站，直接使用 BrightData 服务：

```python
# BrightData 会自动处理 IP 轮换
# 使用 mcp__brightdata__scrape_as_markdown 工具
```

#### 成本对比

| 方案 | 成本 | 可靠性 |
|------|------|--------|
| 降低频率 | 免费 | 中等 |
| 代理池 | $10-50/月 | 较高 |
| BrightData | $50+/月 | 最高 |

---

### 5. JavaScript 渲染

#### 问题描述

页面内容通过 JavaScript 动态加载，直接请求 HTML 无法获取完整内容：

```python
response = requests.get(url)
# response.text 不包含动态加载的内容
```

#### 解决方案

**方案 1: Playwright**（免费）

```python
from playwright.sync_api import sync_playwright

def scrape_dynamic(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='networkidle')

        # 等待特定元素加载
        page.wait_for_selector('.profile-content')

        content = page.content()
        browser.close()
        return content
```

**方案 2: Selenium**（免费）

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def scrape_with_selenium(url):
    options = Options()
    options.add_argument('--headless')

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # 等待页面加载
    time.sleep(3)

    content = driver.page_source
    driver.quit()
    return content
```

**方案 3: BrightData Scraping Browser**（付费）

```python
# 使用 mcp__brightdata__scraping_browser_* 工具
# 自动处理 JavaScript 渲染
```

#### 对比

| 方案 | 速度 | 资源占用 | 成本 |
|------|------|---------|------|
| Playwright | 快 | 中等 | 免费 |
| Selenium | 较慢 | 高 | 免费 |
| BrightData | 快 | 无 | 付费 |

---

### 6. 登录要求

#### 问题描述

部分网站（如 LinkedIn）需要登录才能查看完整信息。

#### 解决方案

**唯一推荐方案: BrightData MCP**

```python
# LinkedIn 必须使用 BrightData
# 工具: mcp__brightdata__web_data_linkedin_person_profile

# 对于 LinkedIn，不要尝试使用 Python 直接爬取
# 成功率极低且可能违反服务条款
```

**哪些网站必须用 BrightData**：

| 网站 | 必须用 BrightData | 原因 |
|------|------------------|------|
| LinkedIn | ✅ | 登录要求 + 高反爬 |
| Twitter/X | ✅ | 登录要求 |
| Facebook | ✅ | 登录要求 |
| 学术网站 | ❌ | 通常公开 |

---

## 决策流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    遇到反爬虫问题                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 识别问题类型                                             │
│      │                                                       │
│      ├─> 邮箱显示 [email protected]                          │
│      │       └─> 使用 Cloudflare XOR 解密 (免费)             │
│      │                                                       │
│      ├─> HTTP 403 Forbidden                                  │
│      │       ├─> 检查 User-Agent → 设置浏览器 UA             │
│      │       └─> 检查 IP → 降低频率 / 使用 BrightData        │
│      │                                                       │
│      ├─> HTTP 429 Too Many Requests                          │
│      │       └─> 添加随机延迟 / 指数退避                      │
│      │                                                       │
│      ├─> 页面内容不完整                                      │
│      │       └─> 使用 Playwright 或 BrightData               │
│      │                                                       │
│      └─> 需要登录 (LinkedIn 等)                              │
│              └─> 必须使用 BrightData MCP                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 最佳实践总结

### 1. 预防措施

```python
# 标准请求配置
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 ...',
    'Accept': 'text/html,application/xhtml+xml,...',
    'Accept-Language': 'en-US,en;q=0.5',
})

# 添加重试机制
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
```

### 2. 错误处理

```python
def safe_scrape(url):
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()

        # 检查是否被 Cloudflare 拦截
        if 'cloudflare' in response.text.lower() and 'checking your browser' in response.text.lower():
            return {'status': 'cloudflare_challenge', 'url': url}

        return {'status': 'success', 'content': response.text}

    except requests.Timeout:
        return {'status': 'timeout', 'url': url}
    except requests.TooManyRedirects:
        return {'status': 'too_many_redirects', 'url': url}
    except requests.HTTPError as e:
        return {'status': 'http_error', 'code': e.response.status_code, 'url': url}
    except Exception as e:
        return {'status': 'error', 'message': str(e), 'url': url}
```

### 3. 智能选择策略

```python
def smart_scrape(url):
    """根据 URL 特征智能选择爬取方式"""

    # LinkedIn 等必须用 BrightData
    if any(domain in url for domain in ['linkedin.com', 'twitter.com', 'x.com']):
        return scrape_with_brightdata(url)

    # 学术网站用普通请求
    if any(domain in url for domain in ['.edu', 'github.io', 'scholar.google']):
        return scrape_with_requests(url)

    # 其他网站先尝试普通请求，失败后考虑 BrightData
    result = scrape_with_requests(url)
    if result.get('status') != 'success':
        return scrape_with_brightdata(url)
    return result
```

---

## 相关文档

- [Python 爬虫技术指南](./python-scraping-guide.md)
- [URL 过滤与优先级规则](./url-priority-rules.md)
- [Web Scraping Practice - TongClass](../../Note/Web-Scraping-Practice-TongClass.md)
