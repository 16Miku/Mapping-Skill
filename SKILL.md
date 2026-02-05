---
name: Mapping-Skill
description: Complete AI talent discovery and outreach workflow using BrightData MCP. This skill should be used when users need to find PhD students, researchers, or engineers in AI/ML fields, extract their profiles, identify Chinese candidates, classify by type, deduplicate, and generate personalized outreach emails.
---

# AI Talent Recruiter

A comprehensive skill for AI/ML talent discovery, profiling, and personalized outreach using BrightData MCP tools.

## Overview

This skill enables the complete talent recruitment pipeline:
1. **Search**: Generate optimized queries and discover candidates via web search
2. **Extract**: Scrape profile pages and extract structured candidate information
3. **Identify**: Recognize Chinese candidates using surname and institution matching
4. **Classify**: Categorize candidates by type (PhD/PostDoc/Professor/Industry)
5. **Deduplicate**: Remove duplicate candidates using 7-level fingerprinting
6. **Standardize**: Map research fields to 22 standardized categories
7. **Generate**: Create personalized outreach emails using field-specific templates

## Prerequisites

This skill requires the BrightData MCP server to be configured in Claude Code.

### Installing BrightData MCP

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

## Reference Files

| File | Purpose |
|------|---------|
| `references/search-templates.md` | Search query templates and keywords |
| `references/profile-schema.md` | Candidate profile data structure |
| `references/top-ai-labs.md` | List of top AI research labs |
| `references/field-mappings.md` | 22 standardized research fields (NEW) |
| `references/talk-tracks.md` | Technical talking points by field (NEW) |
| `references/email-templates.md` | Personalized email templates (NEW) |
| `references/chinese-surnames.md` | Chinese surname database (NEW) |
| `references/deduplication-rules.md` | Candidate deduplication rules (NEW) |
| `references/candidate-classifier.md` | Candidate type classification (NEW) |

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

Use `mcp__brightdata__search_engine` with parallel execution:

```
Tool: mcp__brightdata__search_engine
Parameters:
  engine: "google"
  query: "<generated_query>"
```

**URL Filtering Priority:**
1. Personal pages (`*.github.io`, `sites.google.com`)
2. University domains (see `references/top-ai-labs.md`)
3. LinkedIn profiles (`linkedin.com/in/`)
4. Google Scholar profiles

### Step 3: Scrape Candidate Profiles

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

**Scrape in parallel**: Process 2-5 URLs simultaneously for efficiency.

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

### Example 2: Lab-Targeted Search

**User Request:** "Find all PhD students at Stanford AI Lab working on multimodal learning"

**Execution:**
1. Generate site-specific queries: `site:ai.stanford.edu "multimodal" PhD`
2. Search and collect Stanford AI Lab profiles
3. Scrape and extract
4. Filter by research field mapping to "Multimodal"
5. Classify and deduplicate
6. Present results

### Example 3: Conference Speaker Discovery

**User Request:** "Find Chinese researchers who presented at NeurIPS 2024 on LLM alignment"

**Execution:**
1. Search: `NeurIPS 2024 "alignment" authors site:neurips.cc`
2. Extract author names and affiliations
3. For each author, search for their personal page
4. Scrape profiles and identify Chinese candidates
5. Standardize to "Alignment" field
6. Generate personalized emails
7. Present results

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
