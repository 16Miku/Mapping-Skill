---
name: ai-talent-recruiter
description: Complete AI talent discovery and outreach workflow using BrightData MCP or Python scraping. This skill should be used when users need to find PhD students, researchers, or engineers in AI/ML fields, extract their profiles, identify Chinese candidates, classify by type, deduplicate, and generate personalized outreach emails.
---

# AI Talent Recruiter

A comprehensive skill for AI/ML talent discovery, profiling, and personalized outreach.

## Overview

This skill enables the complete talent recruitment pipeline:
1. **Search**: Generate optimized queries and discover candidates via web search
2. **Extract**: Scrape profile pages and extract structured candidate information
3. **Identify**: Recognize Chinese candidates using surname and institution matching
4. **Classify**: Categorize candidates by type (PhD/PostDoc/Professor/Industry)
5. **Deduplicate**: Remove duplicate candidates using 7-level fingerprinting
6. **Standardize**: Map research fields to 22 standardized categories
7. **Generate**: Create personalized outreach emails using field-specific templates

## Scraping Approach Selection

This skill supports two scraping approaches:

| Approach | Best For | Cost | Success Rate |
|----------|----------|------|--------------|
| **BrightData MCP** (Recommended) | LinkedIn, Twitter, high-anti-scraping sites | Paid | High (99%+) |
| **Python Scraping** | Academic sites (.edu), personal homepages | Free | Medium (70-85%) |

### Selection Guidelines

- **Use Python scraping** for academic websites (.edu, .github.io) - **FREE**
- **Use BrightData MCP** for LinkedIn and sites requiring login - **PAID**
- See `references/python-scraping-guide.md` for detailed implementation

## Prerequisites

### Option A: BrightData MCP (Paid)

This approach requires the BrightData MCP server to be configured in Claude Code.

1. Get your API token from [BrightData](https://brightdata.com)
2. Add the MCP server using Claude CLI:

```bash
claude mcp add --transport sse --scope user brightdata "https://mcp.brightdata.com/sse?token=<your-api-token>"
```

Replace `<your-api-token>` with your actual BrightData API key.

3. Verify the MCP server is connected by checking available tools:
   - `mcp__brightdata__search_engine` - For web searches
   - `mcp__brightdata__scrape_as_markdown` - For page scraping
   - `mcp__brightdata__web_data_linkedin_person_profile` - For LinkedIn profiles

### Option B: Python Scraping (Free)

Requires Python dependencies:

```bash
pip install requests beautifulsoup4 httpx python-dotenv
```

See reference scripts in `scripts/` directory for implementation templates.

## Reference Files

| File | Purpose |
|------|---------|
| `references/search-templates.md` | Search query templates and keywords |
| `references/profile-schema.md` | Candidate profile data structure |
| `references/top-ai-labs.md` | List of top AI research labs |
| `references/field-mappings.md` | 22 standardized research fields |
| `references/talk-tracks.md` | Technical talking points by field |
| `references/email-templates.md` | Personalized email templates |
| `references/chinese-surnames.md` | Chinese surname database |
| `references/deduplication-rules.md` | Candidate deduplication rules |
| `references/candidate-classifier.md` | Candidate type classification |
| **`references/python-scraping-guide.md`** | **Python scraping techniques** |
| **`references/url-priority-rules.md`** | **URL filtering and prioritization** |
| **`references/anti-scraping-solutions.md`** | **Anti-scraping solutions** |
| **`references/conference-paper-scraping.md`** | **Conference paper scraping (OpenReview)** |

## Scripts (Reference Implementations)

| Script | Purpose |
|--------|---------|
| `scripts/serper_search.py` | Serper API search template |
| `scripts/httpx_scraper.py` | Async HTTP scraper |
| `scripts/cloudflare_email_decoder.py` | Cloudflare email decryption |
| `scripts/lab_member_scraper.py` | Lab member batch scraper |
| **`scripts/openreview_scraper.py`** | **OpenReview conference scraper** |
| **`scripts/github_network_scraper.py`** | **GitHub social network scraper (Following/Followers)** |

---

## Complete Workflow

### Step 1: Generate Search Queries

Based on the user's research direction, generate 2-4 search queries using templates from `references/search-templates.md`.

**Query Generation Strategy:**
- Include both English and Chinese keywords
- Target high-quality domains: `github.io`, university sites, LinkedIn
- Combine research direction with role indicators

**Example queries for "Reinforcement Learning":**
```
"reinforcement learning" PhD student site:github.io OR site:stanford.edu
"RLHF" "PPO" PhD researcher personal homepage
强化学习 博士生 清华 OR 北大 个人主页
```

### Step 2: Execute Searches

#### Option A: BrightData MCP (Paid)

Use `mcp__brightdata__search_engine` with parallel execution:

```
Tool: mcp__brightdata__search_engine
Parameters:
  engine: "google"
  query: "<generated_query>"
```

#### Option B: Python + Serper API (Free)

Use `scripts/serper_search.py` template:

```python
from serper_search import serper_search

results = await serper_search(
    query='"reinforcement learning" PhD student site:*.edu',
    api_key="YOUR_SERPER_API_KEY"
)
urls = [item["link"] for item in results.get("organic", [])]
```

**URL Filtering Priority** (see `references/url-priority-rules.md`):
1. Personal pages (`*.github.io`, `sites.google.com`)
2. University domains (see `references/top-ai-labs.md`)
3. LinkedIn profiles (`linkedin.com/in/`)
4. Google Scholar profiles

### Step 3: Scrape Candidate Profiles

#### Option A: BrightData MCP (Paid)

Use `mcp__brightdata__scrape_as_markdown` for general pages:
```
Tool: mcp__brightdata__scrape_as_markdown
Parameters:
  url: "<candidate_url>"
```

For LinkedIn profiles, use the specialized tool:
```
Tool: mcp__brightdata__web_data_linkedin_person_profile
Parameters:
  url: "<linkedin_url>"
```

#### Option B: Python Scraping (Free)

Use `scripts/httpx_scraper.py` or `scripts/lab_member_scraper.py`:

```python
# Simple static pages
from httpx_scraper import batch_scrape

results = await batch_scrape(urls, max_concurrent=5)

# Lab member pages
from lab_member_scraper import LabMemberScraper
scraper = LabMemberScraper()
members = scraper.scrape_lab("https://ai.stanford.edu/people/")
```

**Cloudflare Email Decryption** (see `scripts/cloudflare_email_decoder.py`):
```python
from cloudflare_email_decoder import decode_cloudflare_email
email = decode_cloudflare_email("f493919e85c6c5...")
```

**Scrape in parallel**: Process 2-5 URLs simultaneously for efficiency.

**Anti-scraping solutions**: See `references/anti-scraping-solutions.md` for handling:
- Cloudflare protection
- User-Agent detection
- Rate limiting
- IP blocking

### Step 4: Extract Profile Data

From scraped content, extract fields defined in `references/profile-schema.md`:

**Required fields:**
- `name`: English name
- `name_cn`: Chinese name (if available)
- `title`: Position
- `affiliation`: University/Company
- `email`: Contact email

**Recommended fields:**
- `advisor`: PhD advisor
- `research_interests`: Research areas
- `homepage`, `google_scholar`, `github`, `linkedin`
- `education`, `experience`
- `publications`, `citation_count`, `h_index`

### Step 5: Identify Chinese Candidates (Optional)

Use rules from `references/chinese-surnames.md`:

**Multi-dimensional scoring:**
- Surname match (40%): Check against 100+ Chinese surnames
- Institution match (35%): Check against Chinese universities/labs
- Name structure (15%): Pinyin pattern analysis
- ID pattern (10%): OpenReview ID analysis

**Decision threshold:** Confidence >= 0.5

```python
# Pseudo-code for Chinese detection
is_chinese = (
    surname_score * 0.4 +
    institution_score * 0.35 +
    structure_score * 0.15 +
    id_score * 0.1
) >= 0.5
```

### Step 6: Classify Candidate Type

Use rules from `references/candidate-classifier.md`:

**Priority order:** PhD > PostDoc > Professor > Industry > Master > Unknown

**Classification keywords:**
- **PhD**: "phd student", "doctoral student", "博士生"
- **PostDoc**: "postdoc", "post-doctoral", "博士后"
- **Professor**: "professor", "associate professor", "教授"
- **Industry**: "engineer", "research scientist at [company]", "算法工程师"

### Step 7: Deduplicate Candidates

Use 7-level fingerprinting from `references/deduplication-rules.md`:

**Priority (highest to lowest):**
1. Email (most reliable)
2. Google Scholar URL
3. LinkedIn URL
4. GitHub URL
5. Personal website
6. Composite hash (name + school + field)
7. Source URL hash (last resort)

```python
# Standardization before comparison
email = email.lower().strip()
url = url.lower().replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
```

### Step 8: Standardize Research Field

Use `references/field-mappings.md` to map research directions to 22 standardized fields:

**Standard fields:** RL, NLP, Multimodal, MOE, Pre-training, post-train, Alignment, Reasoning, Agent&RAG, MLSys, LLM4CODE, Computer Vision, Embodiment, Audio, EVAL, data, AI4S, Interpretable AI, Recommendation System, Federated Learning, Trustworthy AI, Pre/Post-train×RL

```python
def get_standardized_field(research_field: str) -> str:
    for standard_field, aliases in FIELD_MAPPING.items():
        for alias in aliases:
            if alias.lower() in research_field.lower():
                return standard_field
    return "default"
```

### Step 9: Generate Personalized Email

Use templates from `references/email-templates.md` and talk tracks from `references/talk-tracks.md`:

**Template structure:**
```
Hi, {{researcher_name}},

[Field-specific opening paragraph referencing their work]

{{technical_hook}}  # Connect their specific work to our interests

{{talk_track_paragraph}}  # 3-4 sentences showing domain depth

[Closing with call to action]

Signature
```

**Key placeholders to fill:**
- `{{technical_hook}}`: Connect candidate's specific work to team interests
- `{{talk_track_paragraph}}`: Domain expertise demonstration

### Step 10: Present Results

Format results as a structured table:

```markdown
## Candidate Profile: [Name]

| Field | Value |
|-------|-------|
| Name | [English Name] ([Chinese Name]) |
| Type | [PhD/PostDoc/Professor/Industry] |
| Affiliation | [University/Lab] |
| Research Field | [Standardized Field] |
| Chinese | [Yes/No (confidence)] |
| Email | [Email] |
| Scholar | [URL] |
| GitHub | [URL] |

**Generated Email:**
[Personalized email based on their field]
```

---

## Usage Examples

### Example 1: Complete PhD Search with Email Generation

**User Request:** "Search for RL PhD students at top universities and generate personalized emails"

**Execution:**
1. Generate queries for "reinforcement learning PhD student"
2. Execute searches, collect URLs
3. Scrape profiles in parallel
4. Extract structured data
5. Identify Chinese candidates (optional)
6. Classify as PhD
7. Deduplicate using email/Scholar URLs
8. Standardize to "RL" field
9. Generate emails using RL template and talk tracks
10. Present results with emails

### Example 2: Lab-Targeted Search (直接爬取实验室页面)

**User Request:** "Find all PhD students at NJU LAMDA lab"

**Execution (两阶段爬取):**
1. Fetch lab people page: `https://www.lamda.nju.edu.cn/CH.PhD_student.ashx`
2. Extract member entries from list page (filter by Chinese name length 2-5 chars)
3. Exclude navigation noise (MainPage, Pub.ashx, etc. via URL keyword filter)
4. For each member detail page (`/Name/`):
   - Extract email with multi-method support: `mailto:` → Cloudflare XOR → `[at]` regex → plain regex
   - Extract English name from URL path as fallback (e.g., `/zhangzn/` → `zhangzn`)
   - Extract publications from "Publications" header + following `ul/ol`
   - Handle SSL errors gracefully (skip `www.nju.edu.cn` etc.)
5. Classify, deduplicate, present results
6. See `scripts/lab_member_scraper.py` for complete implementation

**Practical tips:**
- Chinese lab websites often use `.ashx` (ASP.NET) pages
- Email obfuscation: `[at]` / `(at)` is more common than Cloudflare on Chinese .edu.cn sites
- SSL handshake failures are common on .edu.cn domains - catch and skip
- Use `time.sleep(1.0)` for Chinese university websites (more conservative than global sites)

### Example 3: Conference Paper Author Discovery (OpenReview API)

**User Request:** "Find Chinese researchers who published at ICML 2025"

**Execution (OpenReview API 方案 — 推荐):**
1. Login to OpenReview API (`api2.openreview.net`)
2. Fetch all papers: `client.get_all_notes(content={'venueid': 'ICML.cc/2025/Conference'})`
3. For each paper, extract authors and author IDs
4. Identify Chinese authors using surname matching (`references/chinese-surnames.md`)
5. For Profile IDs (`~Name1`): call `client.get_profile()` to get Email, Homepage, Scholar, DBLP, ORCID, GitHub
6. For Email IDs (`user@email.com`): use directly as contact email
7. Apply three-level email fallback: `preferredEmail → emails[0] → 'Hidden'`
8. Handle Google Scholar field name variants (`gscholar` or `google_scholar`)
9. Construct ORCID URLs from bare IDs if needed
10. Save to CSV with `utf-8-sig` encoding
11. See `references/conference-paper-scraping.md` for complete guide and `scripts/openreview_scraper.py` for code

**Performance benchmark (ICML 2025):**
- 3,257 papers → 8,221 Chinese author records in ~12 min (4.73 it/s)
- Homepage: 73%, Google Scholar: 72%

**Execution (Web 搜索方案 — 备选):**
1. Search: `ICML 2025 "alignment" authors site:openreview.net`
2. Extract author names and affiliations from search results
3. For each author, search for their personal page
4. Scrape profiles and identify Chinese candidates
5. Standardize research field, generate personalized emails

### Example 4: GitHub Social Network Discovery

**User Request:** "Find researchers in AmandaXu97's GitHub Following list"

**Execution (GitHub API 三层数据拼装):**
1. Get Following list via GitHub API: `GET /users/AmandaXu97/following?per_page=100` (paginated)
2. For each user, assemble profile from three layers:
   - Layer 1: `GET /users/{login}` → name, bio, email, company, blog, twitter_username
   - Layer 2: `GET /users/{login}/social_accounts` → dedicated social links
   - Layer 3: `raw.githubusercontent.com/{login}/{login}/main/README.md` → extract Scholar/LinkedIn/知乎 via regex
3. Merge all text sources and extract links using regex patterns
4. Classify candidates, deduplicate, present results
5. See `scripts/github_network_scraper.py` for complete implementation

**Performance benchmark (AmandaXu97):**
- 926 following users processed successfully
- Rate limit: 5,000 requests/hour with Token (vs 60/hour without)
- Each user ≈ 3 API calls → ~2,778 total calls within limits

**Key insight:** Profile README is a hidden goldmine — many researchers put Scholar, personal homepage, and social links there that aren't in the API profile.

---

## Best Practices

1. **Parallel Processing**: Execute independent searches and scrapes in parallel
2. **Domain Prioritization**: Prioritize academic domains over general sites
3. **Progressive Filtering**: Filter aggressively at each step to reduce processing
4. **Error Resilience**: Continue processing if individual scrapes fail
5. **Deduplication Early**: Apply deduplication after extraction, not just at the end
6. **Email Quality**: Always customize `{{technical_hook}}` based on actual candidate work
7. **Field Mapping**: Use standardized fields for consistent categorization
8. **Rate Limiting**: Space out requests if encountering rate limits

---

## Output Format

### Summary Table

| Name | Type | Affiliation | Field | Chinese? | Email |
|------|------|-------------|-------|----------|-------|
| Wei Zhang | PhD | Tsinghua | RL | Yes (0.92) | wei@tsinghua.edu |
| Li Chen | PostDoc | Stanford | Multimodal | Yes (0.87) | li.chen@stanford.edu |

### Detailed Profile (for each candidate)

```markdown
## Wei Zhang (张伟)

**Identity:** PhD Student at Tsinghua University
**Field:** Reinforcement Learning (RL)
**Chinese:** Yes - surname match + institution match (confidence: 0.92)

**Contact:**
- Email: wei.zhang@tsinghua.edu.cn
- Homepage: weizhang.github.io
- Scholar: [Google Scholar link]
- GitHub: [GitHub link]

**Research:** RLHF, reward modeling, policy optimization

**Publications:**
1. "Efficient RLHF for LLMs" (NeurIPS 2024)
2. "Reward Hacking in Practice" (ICML 2024)

**Generated Email:**
[Personalized email using RL template]
```
