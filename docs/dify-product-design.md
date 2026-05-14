# 金融公司对比分析 Agent Demo｜Dify 实现方案

## 1. Demo 目标

本项目目标是使用 Dify 搭建一个金融公司分析智能体。用户只需要输入公司名称或股票代码，系统即可自动识别对应公司与 ticker，调用金融数据 API 获取核心财务指标，并由大语言模型生成结构化的公司分析结果。

该 Demo 主要展示以下能力：

- 使用 Dify 搭建 AI Agent / Workflow
- 将用户自然语言输入转化为标准化 ticker
- 调用外部金融数据 API
- 获取公司概况、估值、收入、利润、PE、EPS 等核心指标
- 使用 LLM 生成结构化对比分析
- 输出表格、投资解读和风险提示
- 体现 AI 产品经理对业务流程、数据链路和用户体验的设计能力

---

## 2. 目标用户

本 Demo 面向以下用户场景：

1. 普通投资者  
   希望快速了解一家公司的基本面情况。

2. 金融内容创作者  
   希望快速生成公司分析框架。

3. AI 产品经理面试展示  
   用于展示自己对 AI Agent、金融数据、Dify 工作流和结构化输出的理解。

4. 数据分析 / AI 应用开发学习  
   用于练习 API 调用、Prompt 设计、LLM 输出控制和产品化包装。

---

## 3. 核心用户流程

```text
用户输入公司名称 / 股票代码
        ↓
Dify 识别公司和 ticker
        ↓
调用金融数据 API
        ↓
获取公司概况、估值、收入、利润、PE、EPS 等指标
        ↓
LLM 生成结构化对比
        ↓
输出表格 + 解读 + 风险提示
```

---

## 4. 推荐 Demo 名称

可以选择以下名称之一：

### 中文名称

- 金融公司基本面分析 Agent
- AI 股票基本面分析助手
- 公司财务指标对比分析 Agent
- AI 金融分析 Demo
- 智能公司估值分析助手

### 英文名称

- Financial Company Analysis Agent
- AI Stock Fundamental Analysis Agent
- Company Valuation Comparison Agent
- Financial Metrics Comparison Demo
- AI Investment Research Assistant

推荐最终命名：

```text
AI Stock Fundamental Analysis Agent
```

中文展示名称：

```text
AI 股票基本面分析助手
```

---

## 5. Dify 应用类型选择

在 Dify 中建议选择：

```text
Workflow App
```

原因：

- 这个 Demo 不是简单聊天，而是有明确的数据处理流程。
- 需要多个步骤：识别公司、调用 API、清洗数据、生成分析。
- Workflow 更适合展示产品设计能力和工程逻辑。
- 面试时可以清楚说明每个节点的作用。

---

## 6. 整体 Workflow 结构

推荐使用以下节点结构：

```text
Start
  ↓
LLM：识别公司名称和股票代码
  ↓
Code：标准化 ticker
  ↓
HTTP Request：调用金融数据 API
  ↓
Code：清洗和整理 API 返回结果
  ↓
LLM：生成结构化金融分析
  ↓
End：输出最终结果
```

---

## 7. 节点 1：Start 用户输入节点

### 节点名称

```text
Start
```

### 输入变量设计

建议设置以下变量：

| 变量名 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| user_query | text | 是 | 用户输入的公司名称或股票代码 |
| analysis_focus | select | 否 | 分析重点 |
| language | select | 否 | 输出语言 |

---

### user_query 示例

用户可以输入：

```text
Apple
```

或：

```text
AAPL
```

或：

```text
帮我分析一下英伟达
```

或：

```text
Compare Apple and Microsoft
```

---

### analysis_focus 选项

```text
综合分析
估值分析
盈利能力分析
成长性分析
风险分析
公司对比
```

---

### language 选项

```text
中文
English
```

---

## 8. 节点 2：LLM 识别公司名称和 ticker

### 节点名称

```text
Extract Company and Ticker
```

### 节点类型

```text
LLM
```

### 节点作用

将用户输入的自然语言转化为标准化公司名称和股票代码。

例如：

用户输入：

```text
帮我分析一下苹果
```

LLM 输出：

```json
{
  "company_name": "Apple Inc.",
  "ticker": "AAPL",
  "market": "US",
  "analysis_type": "single_company"
}
```

---

### Prompt 示例

```text
你是一个金融数据识别助手。

你的任务是从用户输入中识别公司名称、股票代码和市场信息。

用户输入：
{{user_query}}

请只输出 JSON，不要输出解释文字。

输出格式如下：

{
  "company_name": "标准公司英文名称",
  "ticker": "股票代码",
  "market": "市场，例如 US / HK / CN",
  "analysis_type": "single_company 或 comparison",
  "companies": [
    {
      "company_name": "公司名称",
      "ticker": "股票代码",
      "market": "市场"
    }
  ]
}

规则：
1. 如果用户只输入公司名称，请推断最常见的上市公司 ticker。
2. 如果用户输入的是股票代码，请识别对应公司名称。
3. 如果用户输入多个公司，请在 companies 数组中返回多个对象。
4. 如果无法判断 ticker，请将 ticker 设置为 null。
5. 不要编造不确定的信息。
6. 输出必须是合法 JSON。
```

---

## 9. 节点 3：Code 标准化 ticker

### 节点名称

```text
Normalize Ticker
```

### 节点类型

```text
Code
```

### 节点作用

对 LLM 输出的 ticker 做进一步标准化处理，避免大小写、空格、格式错误。

### Python 示例代码

```python
import json

def main(llm_output: str) -> dict:
    try:
        data = json.loads(llm_output)
    except Exception:
        return {
            "success": False,
            "error": "Failed to parse LLM output as JSON",
            "ticker": None,
            "company_name": None
        }

    ticker = data.get("ticker")

    if ticker:
        ticker = ticker.strip().upper()

    return {
        "success": True,
        "company_name": data.get("company_name"),
        "ticker": ticker,
        "market": data.get("market", "US"),
        "analysis_type": data.get("analysis_type", "single_company"),
        "companies": data.get("companies", [])
    }
```

---

## 10. 节点 4：HTTP Request 调用金融数据 API

### 节点名称

```text
Fetch Financial Data
```

### 节点类型

```text
HTTP Request
```

### 推荐 API 选择

可以使用以下 API 之一：

| API | 优点 | 适合阶段 |
|---|---|---|
| Alpha Vantage | 免费额度、文档清晰 | Demo 初期 |
| Financial Modeling Prep | 财务指标较完整 | 进阶版本 |
| Finnhub | 公司概况和行情数据方便 | Demo 初期 |
| Yahoo Finance 非官方接口 | 数据丰富 | 个人学习 |
| Polygon.io | 专业金融数据 | 高级版本 |

Demo 初期推荐：

```text
Financial Modeling Prep
```

因为它更适合获取：

- Company Profile
- Income Statement
- Balance Sheet
- Key Metrics
- Ratios
- PE
- EPS
- Revenue
- Net Income

---

## 11. API 调用示例

以 Financial Modeling Prep 为例。

### Company Profile

```text
https://financialmodelingprep.com/api/v3/profile/{{ticker}}?apikey=YOUR_API_KEY
```

### Key Metrics

```text
https://financialmodelingprep.com/api/v3/key-metrics-ttm/{{ticker}}?apikey=YOUR_API_KEY
```

### Financial Ratios

```text
https://financialmodelingprep.com/api/v3/ratios-ttm/{{ticker}}?apikey=YOUR_API_KEY
```

### Income Statement

```text
https://financialmodelingprep.com/api/v3/income-statement/{{ticker}}?limit=5&apikey=YOUR_API_KEY
```

---

## 12. Dify HTTP Request 配置方式

### Method

```text
GET
```

### URL

```text
https://financialmodelingprep.com/api/v3/profile/{{ticker}}?apikey=YOUR_API_KEY
```

### Headers

一般可以为空。

如果 API 要求 JSON：

```json
{
  "Content-Type": "application/json"
}
```

### Query Parameters

也可以拆成：

| Key | Value |
|---|---|
| apikey | YOUR_API_KEY |

---

## 13. 节点 5：Code 清洗金融数据

### 节点名称

```text
Clean Financial Data
```

### 节点类型

```text
Code
```

### 节点作用

将 API 返回的复杂 JSON 转化为 LLM 更容易理解的结构化数据。

### 示例输入

API 可能返回：

```json
[
  {
    "symbol": "AAPL",
    "companyName": "Apple Inc.",
    "price": 198.5,
    "mktCap": 2940000000000,
    "industry": "Consumer Electronics",
    "sector": "Technology",
    "description": "Apple Inc. designs, manufactures..."
  }
]
```

### Python 示例代码

```python
def main(api_response: list) -> dict:
    if not api_response or len(api_response) == 0:
        return {
            "success": False,
            "error": "No financial data found."
        }

    company = api_response[0]

    cleaned_data = {
        "symbol": company.get("symbol"),
        "company_name": company.get("companyName"),
        "price": company.get("price"),
        "market_cap": company.get("mktCap"),
        "industry": company.get("industry"),
        "sector": company.get("sector"),
        "description": company.get("description"),
        "beta": company.get("beta"),
        "volume": company.get("volAvg"),
        "exchange": company.get("exchangeShortName")
    }

    return {
        "success": True,
        "cleaned_data": cleaned_data
    }
```

---

## 14. 进阶：合并多个 API 返回结果

如果后续你同时调用：

- Company Profile
- Key Metrics
- Ratios
- Income Statement

可以再增加一个 Code 节点：

```text
Merge Financial Data
```

用于合并所有 API 返回结果。

### 合并后的数据结构示例

```json
{
  "company_profile": {
    "symbol": "AAPL",
    "company_name": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "market_cap": 2940000000000
  },
  "valuation": {
    "pe_ratio": 30.5,
    "price_to_sales": 7.8,
    "price_to_book": 45.2
  },
  "profitability": {
    "eps": 6.43,
    "net_profit_margin": 0.25,
    "roe": 1.45
  },
  "growth": {
    "revenue_latest": 383000000000,
    "net_income_latest": 97000000000
  }
}
```

---

## 15. 节点 6：LLM 生成结构化金融分析

### 节点名称

```text
Generate Financial Analysis
```

### 节点类型

```text
LLM
```

### 节点作用

根据清洗后的金融数据，生成用户可读的结构化分析。

---

### Prompt 示例

```text
你是一名专业但谨慎的金融分析助手。

请基于以下公司金融数据，生成结构化分析报告。

公司数据：
{{cleaned_data}}

用户分析重点：
{{analysis_focus}}

输出语言：
{{language}}

请严格按照以下结构输出：

# 公司基本信息

| 指标 | 内容 |
|---|---|
| 公司名称 |  |
| 股票代码 |  |
| 所属行业 |  |
| 所属板块 |  |
| 当前价格 |  |
| 市值 |  |

# 核心财务指标

| 指标 | 数值 | 简单解释 |
|---|---|---|
| PE Ratio |  |  |
| EPS |  |  |
| Revenue |  |  |
| Net Income |  |  |
| Market Cap |  |  |

# 分析解读

请从以下角度分析：

1. 公司业务基本面
2. 估值水平
3. 盈利能力
4. 成长性
5. 潜在风险

# 简明结论

请用 3-5 条 bullet points 总结。

# 风险提示

必须包含以下免责声明：

本内容仅用于学习和信息参考，不构成任何投资建议。金融市场存在风险，投资决策应结合个人风险承受能力，并咨询专业人士。
```

---

## 16. 最终输出格式示例

```markdown
# Apple Inc. 基本面分析

## 公司基本信息

| 指标 | 内容 |
|---|---|
| 公司名称 | Apple Inc. |
| 股票代码 | AAPL |
| 所属行业 | Consumer Electronics |
| 所属板块 | Technology |
| 当前价格 | 198.50 USD |
| 市值 | 2.94T USD |

## 核心财务指标

| 指标 | 数值 | 解读 |
|---|---|---|
| PE Ratio | 30.5 | 估值处于较高水平 |
| EPS | 6.43 | 每股盈利能力较强 |
| Revenue | 383B USD | 收入规模较大 |
| Net Income | 97B USD | 盈利能力强 |
| Market Cap | 2.94T USD | 全球头部科技公司 |

## 分析解读

Apple 是全球领先的消费电子和科技公司，核心收入来源包括 iPhone、Mac、iPad、服务业务和可穿戴设备。从基本面来看，公司拥有较强的品牌壁垒、稳定的现金流和全球化用户基础。

从估值角度看，如果 PE Ratio 高于行业平均水平，说明市场对公司未来增长仍有较高预期，但也意味着估值回调风险较高。

从盈利能力看，公司 EPS 和净利润水平较高，说明其商业模式成熟且具备较强盈利能力。

## 简明结论

- Apple 具备较强品牌优势和现金流能力。
- 公司盈利能力稳定，但增长速度可能低于早期高速成长阶段。
- 当前估值需要结合行业平均 PE 和未来增长预期判断。
- 适合用于长期基本面观察，但不应仅凭单一指标做投资决策。

## 风险提示

本内容仅用于学习和信息参考，不构成任何投资建议。金融市场存在风险，投资决策应结合个人风险承受能力，并咨询专业人士。
```

---

## 17. Dify 中推荐节点命名

建议在 Dify Workflow 中使用清晰的英文节点名，方便面试展示：

```text
Start
Extract Company and Ticker
Normalize Ticker
Fetch Company Profile
Fetch Key Metrics
Fetch Financial Ratios
Fetch Income Statement
Merge Financial Data
Generate Financial Analysis
End
```

如果是第一版 MVP，可以先简化为：

```text
Start
Extract Company and Ticker
Fetch Company Profile
Generate Financial Analysis
End
```

---

## 18. MVP 版本实现路径

### 第 1 版：最小可用版本

目标：先跑通完整流程。

功能包括：

- 用户输入公司名称或 ticker
- LLM 识别 ticker
- 调用一个金融 API 获取公司概况
- LLM 输出公司基本分析
- 加入风险提示

Workflow：

```text
Start
  ↓
LLM Extract Ticker
  ↓
HTTP Request Company Profile
  ↓
LLM Generate Analysis
  ↓
End
```

---

### 第 2 版：财务指标增强版

新增：

- PE Ratio
- EPS
- Revenue
- Net Income
- Market Cap
- Profit Margin
- ROE

Workflow：

```text
Start
  ↓
LLM Extract Ticker
  ↓
HTTP Request Company Profile
  ↓
HTTP Request Key Metrics
  ↓
HTTP Request Financial Ratios
  ↓
HTTP Request Income Statement
  ↓
Code Merge Data
  ↓
LLM Generate Structured Analysis
  ↓
End
```

---

### 第 3 版：公司对比版本

新增：

- 支持用户输入两个公司
- 自动识别两个 ticker
- 分别调用 API
- 生成对比表格
- 给出优劣势分析

示例输入：

```text
Compare Apple and Microsoft
```

输出：

```markdown
| 指标 | Apple | Microsoft | 简单解读 |
|---|---|---|---|
| Market Cap | ... | ... | ... |
| PE Ratio | ... | ... | ... |
| EPS | ... | ... | ... |
| Revenue | ... | ... | ... |
| Net Income | ... | ... | ... |
```

---

## 19. 公司对比 Prompt 示例

```text
你是一名金融分析助手。

请基于以下两家公司的财务数据，生成结构化对比分析。

公司 A：
{{company_a_data}}

公司 B：
{{company_b_data}}

请输出：

# 公司对比概览

| 指标 | 公司 A | 公司 B | 解读 |
|---|---|---|---|
| 公司名称 |  |  |  |
| 股票代码 |  |  |  |
| 行业 |  |  |  |
| 市值 |  |  |  |
| PE Ratio |  |  |  |
| EPS |  |  |  |
| Revenue |  |  |  |
| Net Income |  |  |  |

# 对比分析

请从以下角度分析：

1. 业务规模
2. 盈利能力
3. 估值水平
4. 成长潜力
5. 风险因素

# 总结

请用简洁语言说明两家公司各自的优势和风险。

# 风险提示

本内容仅用于学习和信息参考，不构成任何投资建议。
```

---

## 20. 产品设计亮点

这个 Demo 不只是一个简单的聊天机器人，而是一个完整的 AI 应用工作流。

它体现了以下产品能力：

### 1. 用户输入理解能力

用户可以输入自然语言，而不是必须输入标准股票代码。

例如：

```text
帮我看看英伟达怎么样
```

系统可以识别为：

```text
NVIDIA / NVDA
```

---

### 2. 外部工具调用能力

通过 HTTP Request 节点调用金融数据 API，说明这个 Agent 不只是依赖模型自身知识，而是可以连接实时或准实时数据源。

---

### 3. 数据结构化能力

API 返回的数据通常比较复杂，Code 节点可以将原始 JSON 清洗为适合分析的数据结构。

---

### 4. Prompt Engineering 能力

通过 Prompt 控制 LLM 输出格式，包括：

- 表格
- 指标解释
- 分析结论
- 风险提示
- 免责声明

---

### 5. 金融业务理解能力

Demo 涉及：

- 公司概况
- 市值
- PE
- EPS
- 收入
- 利润
- 盈利能力
- 估值水平
- 风险因素

这比普通 AI 聊天 Demo 更有业务价值。

---

## 21. 面试中可以这样介绍这个项目

```text
我做了一个基于 Dify 的金融公司基本面分析 Agent。用户输入公司名称或股票代码后，系统会先识别公司和 ticker，然后调用金融数据 API 获取公司概况、估值、收入、利润、PE、EPS 等指标。之后我通过 Prompt 设计，让大模型生成结构化的分析报告，包括指标表格、业务解读、估值分析和风险提示。

这个项目的重点不是简单地让大模型回答问题，而是把用户输入、数据 API、数据清洗、结构化生成和风险控制串成一个完整的 AI 应用流程。它可以展示我对 AI Agent、Workflow、Prompt Engineering、金融数据和产品体验设计的理解。
```

---

## 22. GitHub README 展示结构

如果后续要放到 GitHub，可以按下面结构写 README：

```markdown
# AI Stock Fundamental Analysis Agent

## Overview

This project is a Dify-based AI workflow that helps users analyze listed companies based on financial fundamentals. Users can enter a company name or ticker symbol, and the system automatically retrieves financial data and generates a structured analysis report.

## Features

- Natural language company recognition
- Ticker extraction
- Financial data API integration
- Company profile analysis
- Valuation metrics analysis
- PE, EPS, revenue and net income interpretation
- Structured markdown report generation
- Risk disclaimer generation

## Tech Stack

- Dify Workflow
- LLM
- HTTP Request Node
- Python Code Node
- Financial Modeling Prep API
- Prompt Engineering

## Workflow

User Input → Ticker Extraction → Financial Data API → Data Cleaning → LLM Analysis → Structured Report

## Disclaimer

This project is for educational and demonstration purposes only. It does not provide financial advice.
```

---

## 23. 推荐完成顺序

建议不要一开始做得太复杂，而是分阶段完成。

### Step 1

先完成：

```text
输入 Apple → 识别 AAPL → 调用 Company Profile API → 输出公司介绍
```

### Step 2

增加：

```text
PE / EPS / Market Cap / Revenue / Net Income
```

### Step 3

增加：

```text
Apple vs Microsoft 对比分析
```

### Step 4

增加：

```text
中英文切换
```

### Step 5

增加：

```text
风险等级 / 分析重点选择
```

### Step 6

整理 GitHub README 和截图，作为求职作品展示。

---

## 24. 当前 Demo 的核心价值

这个 Demo 对 AI 产品经理求职有价值，因为它可以体现：

- 你理解 AI Agent 的工作流设计
- 你会用 Dify 搭建可运行的 AI 应用
- 你知道如何连接外部 API
- 你理解金融分析场景中的核心指标
- 你能设计结构化输出，而不是只做普通问答
- 你有产品意识，知道加入风险提示和免责声明
- 你可以把技术 Demo 包装成面试作品

---

## 25. 最终作品展示建议

最终展示时建议准备以下材料：

```text
1. Dify Workflow 截图
2. 用户输入示例
3. 最终输出结果截图
4. API 数据调用说明
5. Prompt 设计说明
6. GitHub README
7. 一页项目介绍图
```

项目介绍图可以使用以下结构：

```text
用户问题
   ↓
公司识别
   ↓
金融数据 API
   ↓
数据清洗
   ↓
LLM 分析
   ↓
结构化报告
```

---

## 26. 项目一句话总结

```text
这是一个基于 Dify Workflow 的金融公司基本面分析 Agent，可以将用户输入的公司名称或股票代码转化为结构化金融分析报告，展示了 AI Agent、API 调用、Prompt Engineering 和金融业务理解的综合能力。
```
