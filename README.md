# Mapping-Skill - AI 人才招聘技能

> 基于 BrightData MCP 的完整 AI/ML 人才发现、筛选与外联工作流

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude-Code-orange.svg)](https://claude.com/claude-code)

## 简介

Mapping-Skill 是一个专为 AI/ML 领域设计的自动化人才招聘工具。它能够帮助招聘人员和研究团队高效地发现、筛选博士生、博士后、教授和工业界研究人员，并生成个性化的外联邮件。

## 核心功能

| 功能 | 说明 |
|------|------|
| **智能搜索** | 生成优化的中英文搜索查询，发现高质量候选人 |
| **资料提取** | 从个人主页、LinkedIn、Google Scholar 提取结构化信息 |
| **华人识别** | 通过姓氏、机构多维度评分识别中国候选人 |
| **自动分类** | 按博士/博士后/教授/工业界自动分类 |
| **智能去重** | 7级指纹技术确保候选人唯一性 |
| **领域标准化** | 将研究方向映射到 22 个标准领域 |
| **邮件生成** | 根据研究领域生成个性化外联邮件 |

## 前置要求

- **Claude Code** - [下载安装](https://claude.com/claude-code)
- **BrightData API 密钥** - 从 [BrightData](https://brightdata.com) 获取

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/Mapping-Skill.git
cd Mapping-Skill
```

### 2. 安装 BrightData MCP

```bash
claude mcp add --transport sse --scope user brightdata "https://mcp.brightdata.com/sse?token=<你的API密钥>"
```

将 `<你的API密钥>` 替换为实际的 BrightData API 密钥。

### 3. 验证安装

检查 Claude Code 中是否可见以下工具：
- `mcp__brightdata__search_engine` - 网络搜索
- `mcp__brightdata__scrape_as_markdown` - 页面抓取
- `mcp__brightdata__web_data_linkedin_person_profile` - LinkedIn 档案

## 使用方法

### 基础用法

在 Claude Code 中加载技能：

```
/load SKILL.md
```

### 工作流程

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   生成搜索查询   │ -> │   执行网络搜索   │ -> │   抓取候选人资料  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   生成个性化邮件  │ <- │   标准化研究领域  │ <- │   提取结构化数据  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   输出结果报告   │ -> │   智能去重处理   │ -> │   分类与识别     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 使用示例

**示例 1：搜索强化学习博士候选人**
```
Search for RL PhD students at top universities and generate personalized emails
```

**示例 2：特定实验室定向搜索**
```
Find all PhD students at Stanford AI Lab working on multimodal learning
```

**示例 3：会议演讲者发现**
```
Find Chinese researchers who presented at NeurIPS 2024 on LLM alignment
```

## 项目结构

```
Mapping-Skill/
├── SKILL.md                          # 主技能定义文件
├── README.md                         # 项目说明文档
└── references/                       # 参考文档目录
    ├── candidate-classifier.md       # 候选人类型分类规则
    ├── chinese-surnames.md           # 中文姓氏数据库（100+）
    ├── deduplication-rules.md        # 7级去重规则
    ├── email-templates.md            # 个性化邮件模板
    ├── field-mappings.md             # 22个标准研究领域
    ├── profile-schema.md             # 候选人档案数据结构
    ├── search-templates.md           # 搜索查询模板
    ├── talk-tracks.md                # 按领域分类的技术话术
    └── top-ai-labs.md                # 顶级AI研究实验室列表
```

## 支持的研究领域

| 领域 | 说明 |
|------|------|
| RL | 强化学习 |
| NLP | 自然语言处理 |
| Multimodal | 多模态学习 |
| MOE | 混合专家模型 |
| Pre-training | 预训练 |
| post-train | 后训练 |
| Alignment | 模型对齐 |
| Reasoning | 推理能力 |
| Agent&RAG | 智能体与检索增强 |
| MLSys | 机器学习系统 |
| LLM4CODE | 代码大模型 |
| Computer Vision | 计算机视觉 |
| Embodiment | 具身智能 |
| Audio | 音频处理 |
| EVAL | 模型评估 |
| data | 数据工程 |
| AI4S | AI for Science |
| Interpretable AI | 可解释AI |
| Recommendation System | 推荐系统 |
| Federated Learning | 联邦学习 |
| Trustworthy AI | 可信AI |
| Pre/Post-train×RL | 预/后训练与强化学习结合 |

## 输出格式

候选人档案以结构化表格形式呈现：

```markdown
## Wei Zhang (张伟)

**身份**：清华大学博士生
**领域**：强化学习 (RL)
**华人**：是 - 姓氏匹配 + 机构匹配 (置信度: 0.92)

**联系方式**：
- 邮箱：wei.zhang@tsinghua.edu.cn
- 主页：weizhang.github.io
- Scholar：[Google Scholar]
- GitHub：[GitHub]

**研究方向**：RLHF、奖励建模、策略优化

**代表性论文**：
1. "Efficient RLHF for LLMs" (NeurIPS 2024)
2. "Reward Hacking in Practice" (ICML 2024)

**生成邮件**：
[基于 RL 模板的个性化邮件]
```

## 最佳实践

1. **并行处理**：同时执行多个独立搜索和抓取任务以提高效率
2. **域名优先级**：优先处理学术域名（.edu）而非通用网站
3. **渐进过滤**：在每一步都进行过滤以减少后续处理量
4. **错误容忍**：单个抓取失败时继续处理其他任务
5. **早期去重**：提取数据后立即去重，而非等到最后
6. **邮件质量**：始终基于候选人实际工作定制 `{{technical_hook}}`
7. **速率限制**：遇到速率限制时适当延迟请求

## 配置说明

### 自定义搜索模板

编辑 `references/search-templates.md` 添加自定义查询模式

### 添加新的研究领域

在 `references/field-mappings.md` 中映射新的领域别名

### 定制邮件模板

修改 `references/email-templates.md` 中的模板内容

## 常见问题

**Q: 支持哪些数据源？**
A: 个人主页、GitHub Pages、大学官网、LinkedIn、Google Scholar 等

**Q: 如何提高华人识别准确率？**
A: 可通过补充 `chinese-surnames.md` 中的姓氏列表和调整评分权重

**Q: 去重规则可以自定义吗？**
A: 可以，编辑 `deduplication-rules.md` 调整 7 级指纹的优先级

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加某个功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/yourusername/Mapping-Skill/issues)
- 发送邮件至 your.email@example.com

---

**Made with ❤️ for the AI/ML recruitment community**
