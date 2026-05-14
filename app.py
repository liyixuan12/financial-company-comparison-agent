"""
金融公司基本面对比分析 — Streamlit 纯前端
==========================================
纯前端应用，调用 Dify Workflow API 获取结构化数据并渲染可视化报告。
前端不包含任何数据获取、清洗或评分逻辑——这些全部由 Dify Workflow 后端完成。

运行模式：
  1. Dify API       — 调用运行中的 Dify Workflow（后端处理数据+LLM 报告）
  2. 离线演示       — 使用缓存数据展示完整 UI（用于无 Dify 环境下的作品集演示）
"""

import json
import os
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# ──────────────────────────── page config ────────────────────────────

st.set_page_config(
    page_title="金融公司基本面对比分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────── custom css ─────────────────────────────

st.markdown(
    """
<style>
html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans SC', sans-serif; }

.hero {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 40%, #2c5364 100%);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    margin-bottom: 1.5rem;
    color: #ffffff;
}
.hero h1 { margin: 0 0 .6rem 0; font-size: 2rem; font-weight: 700; }
.hero p  { margin: 0; font-size: 1.05rem; opacity: .88; line-height: 1.6; }

.metric-card {
    background: #ffffff;
    border: 1px solid #e8ecf1;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.metric-card .label { font-size: .78rem; color: #6b7280; margin-bottom: .3rem; }
.metric-card .value { font-size: 1.45rem; font-weight: 700; color: #111827; }

.step-flow {
    display: flex; flex-wrap: wrap; gap: .5rem;
    align-items: center; margin: 1rem 0;
}
.step-badge {
    background: #e0f2fe; color: #0369a1;
    border-radius: 20px; padding: .35rem .9rem;
    font-size: .82rem; font-weight: 600;
    white-space: nowrap;
}
.step-arrow { font-size: 1rem; color: #9ca3af; }

.disclaimer {
    background: #fef3c7; border-left: 4px solid #f59e0b;
    border-radius: 8px; padding: 1rem 1.2rem;
    font-size: .85rem; color: #92400e;
    margin-top: 2rem;
}

section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label {
    font-weight: 600;
}
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────── cached demo response (offline fallback) ────────────
# Mirrors the structured JSON that Dify Workflow would return,
# allowing the full UI to render without a running Dify instance.

_CACHED_COMPANY_DATA: list[dict[str, Any]] = [
    {
        "symbol": "NVDA", "name": "NVIDIA Corporation", "status": "success",
        "sector": "TECHNOLOGY", "industry": "SEMICONDUCTORS",
        "country": "USA", "currency": "USD", "latest_quarter": "2026-01-31",
        "market_cap": "5.23T", "revenue_ttm": "215.94B",
        "gross_profit_ttm": "153.46B", "ebitda": "133.23B",
        "pe_ratio": "43.83", "forward_pe": "26.53", "peg_ratio": "0.683",
        "price_to_sales": "24.22", "price_to_book": "30.36",
        "eps": "4.91", "profit_margin": "55.60%", "operating_margin": "65.00%",
        "roe": "101.50%", "roa": "51.20%",
        "revenue_growth_yoy": "73.20%", "earnings_growth_yoy": "95.60%",
        "analyst_target_price": "269.17",
        "analyst_rating_strong_buy": "9", "analyst_rating_buy": "48",
        "analyst_rating_hold": "2", "analyst_rating_sell": "1",
        "analyst_rating_strong_sell": "0",
        "week_52_high": "217.8", "week_52_low": "120.25", "beta": "2.244",
        "description": "NVIDIA Corporation is a technology company focused on GPUs, accelerated computing, and AI infrastructure.",
    },
    {
        "symbol": "AAPL", "name": "Apple Inc", "status": "success",
        "sector": "TECHNOLOGY", "industry": "CONSUMER ELECTRONICS",
        "country": "USA", "currency": "USD", "latest_quarter": "2026-03-31",
        "market_cap": "4.31T", "revenue_ttm": "451.44B",
        "gross_profit_ttm": "216.07B", "ebitda": "159.98B",
        "pe_ratio": "35.47", "forward_pe": "33.44", "peg_ratio": "2.571",
        "price_to_sales": "9.54", "price_to_book": "39.19",
        "eps": "8.27", "profit_margin": "27.20%", "operating_margin": "32.30%",
        "roe": "141.50%", "roa": "26.20%",
        "revenue_growth_yoy": "16.60%", "earnings_growth_yoy": "21.80%",
        "analyst_target_price": "303.38",
        "analyst_rating_strong_buy": "7", "analyst_rating_buy": "25",
        "analyst_rating_hold": "14", "analyst_rating_sell": "1",
        "analyst_rating_strong_sell": "1",
        "week_52_high": "294.76", "week_52_low": "192.87", "beta": "1.065",
        "description": "Apple Inc is a consumer electronics and software company with hardware, services, and ecosystem-driven revenue streams.",
    },
    {
        "symbol": "MSFT", "name": "Microsoft Corporation", "status": "success",
        "sector": "TECHNOLOGY", "industry": "SOFTWARE - INFRASTRUCTURE",
        "country": "USA", "currency": "USD", "latest_quarter": "2026-03-31",
        "market_cap": "3.15T", "revenue_ttm": "261.80B",
        "gross_profit_ttm": "182.30B", "ebitda": "128.50B",
        "pe_ratio": "34.21", "forward_pe": "30.10", "peg_ratio": "2.15",
        "price_to_sales": "12.03", "price_to_book": "11.52",
        "eps": "12.41", "profit_margin": "36.40%", "operating_margin": "44.60%",
        "roe": "38.20%", "roa": "19.80%",
        "revenue_growth_yoy": "15.20%", "earnings_growth_yoy": "18.40%",
        "analyst_target_price": "490.00",
        "analyst_rating_strong_buy": "12", "analyst_rating_buy": "32",
        "analyst_rating_hold": "5", "analyst_rating_sell": "0",
        "analyst_rating_strong_sell": "0",
        "week_52_high": "468.35", "week_52_low": "385.58", "beta": "0.896",
        "description": "Microsoft Corporation develops software, cloud services, and AI products including Azure, Office 365, and Copilot.",
    },
]

_CACHED_SCORED: list[dict[str, Any]] = [
    {"symbol": "NVDA", "name": "NVIDIA Corporation",
     "growth_score": 100.0, "profitability_score": 92.3, "valuation_score": 65.0, "risk_score": 0.0, "total_score": 73.9},
    {"symbol": "MSFT", "name": "Microsoft Corporation",
     "growth_score": 0.0, "profitability_score": 21.0, "valuation_score": 58.6, "risk_score": 100.0, "total_score": 36.0},
    {"symbol": "AAPL", "name": "Apple Inc",
     "growth_score": 3.4, "profitability_score": 24.1, "valuation_score": 30.4, "risk_score": 87.4, "total_score": 29.0},
]

_CACHED_REPORT = """\
# 金融公司基本面对比报告

> 此为离线演示缓存数据。连接 Dify Workflow 后将生成完整的 AI 分析报告。

## 摘要

本报告对 NVIDIA (NVDA)、Apple (AAPL)、Microsoft (MSFT) 三家科技公司进行基本面对比。

- **NVDA** 在成长性维度表现突出（Revenue Growth YoY 73.20%，Earnings Growth YoY 95.60%），盈利能力指标同样领先（Profit Margin 55.60%，Operating Margin 65.00%）。但 Beta 为 2.244，历史波动较大。
- **AAPL** 拥有最高的 ROE（141.50%），反映出资本效率优势，但 PEG Ratio 为 2.571，估值与成长性的匹配关系需要结合行业背景进一步分析。
- **MSFT** 在 Beta（0.896）和估值指标上表现相对稳健，PE Ratio 34.21 为三者最低。

## 免责声明

本报告仅用于公开金融信息整理和学习参考，不构成投资建议、买卖建议或收益承诺。研究优先级评分仅用于帮助用户确定后续研究顺序，不代表投资价值判断。
"""

CACHED_DEMO_RESPONSE: dict[str, Any] = {
    "company_data": _CACHED_COMPANY_DATA,
    "scored": _CACHED_SCORED,
    "report_text": _CACHED_REPORT,
    "success_count": 3,
    "failed_count": 0,
}

# ──────────────────────────── helpers ────────────────────────────────


def _to_float(value: Any) -> float | None:
    if value in (None, "", "None", "N/A", "-"):
        return None
    try:
        return float(str(value).replace("%", "").replace("T", "").replace("B", "").replace("M", ""))
    except (ValueError, TypeError):
        return None


def _dify_config_from_deploy() -> tuple[str, str]:
    """供公开部署使用：从环境变量或 Streamlit Secrets 读取 Dify，访客无需在页面填写 API Key。"""
    url = (os.environ.get("DIFY_API_URL") or "").strip()
    key = (os.environ.get("DIFY_API_KEY") or "").strip()
    if url and key:
        return url, key
    try:
        cfg = st.secrets
    except (FileNotFoundError, RuntimeError, AttributeError, TypeError):
        return url, key
    if not url:
        url = str(cfg.get("DIFY_API_URL", "") or "").strip()
    if not key:
        key = str(cfg.get("DIFY_API_KEY", "") or "").strip()
    if (not url or not key):
        sub = cfg.get("dify")
        if isinstance(sub, dict):
            url = url or str(sub.get("api_url", "") or "").strip()
            key = key or str(sub.get("api_key", "") or "").strip()
    return url, key


# ──────────────── Dify API integration ───────────────────────────────


def call_dify_workflow(
    base_url: str,
    api_key: str,
    symbols: str,
    analysis_focus: str,
    language: str,
    data_mode: str,
) -> dict[str, Any]:
    """Call Dify Workflow and return structured response.

    Returns dict with keys: company_data, scored, report_text,
    success_count, failed_count.
    """
    url = f"{base_url.rstrip('/')}/v1/workflows/run"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {
            "symbols": symbols,
            "analysis_focus": analysis_focus,
            "language": language,
            "data_mode": data_mode,
        },
        "response_mode": "blocking",
        "user": "streamlit-frontend",
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()

    outputs = resp.json().get("data", {}).get("outputs", {})

    company_data_raw = outputs.get("company_data_json", "[]")
    scored_raw = outputs.get("scored_json", "[]")

    try:
        company_data = json.loads(company_data_raw) if isinstance(company_data_raw, str) else company_data_raw
    except (json.JSONDecodeError, TypeError):
        company_data = []

    try:
        scored = json.loads(scored_raw) if isinstance(scored_raw, str) else scored_raw
    except (json.JSONDecodeError, TypeError):
        scored = []

    return {
        "company_data": company_data,
        "scored": scored,
        "report_text": outputs.get("report_text", ""),
        "success_count": outputs.get("success_count", 0),
        "failed_count": outputs.get("failed_count", 0),
    }


# ──────────────── chart builders ─────────────────────────────────────

CHART_COLORS = ["#0ea5e9", "#f97316", "#8b5cf6", "#10b981", "#ef4444", "#ec4899", "#6366f1"]


def build_radar(scored: list[dict]) -> go.Figure:
    categories = ["成长性", "盈利能力", "估值匹配", "波动风险"]
    fig = go.Figure()
    for i, s in enumerate(scored):
        vals = [s["growth_score"], s["profitability_score"], s["valuation_score"], s["risk_score"]]
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=f'{s["symbol"]}',
            line=dict(color=CHART_COLORS[i % len(CHART_COLORS)]),
            opacity=0.75,
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True, height=420,
        margin=dict(l=60, r=60, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    return fig


def build_bar_metrics(companies: list[dict], metric_key: str, title: str) -> go.Figure:
    symbols = [c["symbol"] for c in companies]
    values = [_to_float(c.get(metric_key)) for c in companies]
    colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(symbols))]
    fig = go.Figure(go.Bar(x=symbols, y=values, marker_color=colors, text=values, textposition="outside"))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        yaxis_title="", height=340, margin=dict(l=40, r=20, t=50, b=30),
    )
    return fig


def build_analyst_stacked(companies: list[dict]) -> go.Figure:
    symbols = [c["symbol"] for c in companies]
    categories = [
        ("analyst_rating_strong_buy", "Strong Buy", "#047857"),
        ("analyst_rating_buy", "Buy", "#10b981"),
        ("analyst_rating_hold", "Hold", "#fbbf24"),
        ("analyst_rating_sell", "Sell", "#f97316"),
        ("analyst_rating_strong_sell", "Strong Sell", "#ef4444"),
    ]
    fig = go.Figure()
    for key, name, color in categories:
        vals = [_to_float(c.get(key)) or 0 for c in companies]
        fig.add_trace(go.Bar(name=name, x=symbols, y=vals, marker_color=color))
    fig.update_layout(
        barmode="stack", title=dict(text="分析师评级分布", font=dict(size=14)),
        height=360, margin=dict(l=40, r=20, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )
    return fig


# ──────────────── sidebar ────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ 设置")

    run_mode = st.selectbox(
        "运行模式",
        ["离线演示（无需后端）", "Dify API"],
        help="离线演示使用缓存数据展示完整 UI；Dify API 连接后端获取实时数据",
    )

    deploy_url, deploy_key = _dify_config_from_deploy()
    has_server_dify = bool(deploy_url and deploy_key)

    dify_url = dify_key = ""
    dify_data_mode = "Demo Mode"
    if run_mode == "Dify API":
        if has_server_dify:
            dify_url, dify_key = deploy_url, deploy_key
            st.success("部署模式：已使用服务器上的 Dify 配置，访客无需填写 API Key。")
            st.caption(
                "密钥来自环境变量 `DIFY_API_URL` / `DIFY_API_KEY` 或 `.streamlit/secrets.toml`（勿提交到 Git）。"
            )
        else:
            dify_url = st.text_input(
                "Dify Base URL",
                value="http://localhost",
                help="不含路径前缀，例如 https://api.dify.ai 或本地 http://127.0.0.1:5001",
            )
            dify_key = st.text_input(
                "Dify API Key",
                type="password",
                help="Dify 控制台 → 该 Workflow 应用 → API 访问 → 复制「API 密钥」",
            )
            st.caption("须同时填写 Base URL 与 API Key 后，再点击主区域「开始分析」。")
        dify_data_mode = st.selectbox(
            "Dify 数据源",
            ["Demo Mode", "FMP", "Live API Mode"],
            help="Demo Mode 使用内置样本数据；FMP 调用 Financial Modeling Prep；Live API Mode 调用 Alpha Vantage",
        )
        if dify_data_mode == "FMP":
            st.caption("⚠️ FMP 需要在 Dify 环境变量中配置 FMP_API_KEY（免费额度 250 次/天）")
        elif dify_data_mode == "Live API Mode":
            st.caption("⚠️ Alpha Vantage 需要在 Dify 环境变量中配置 ALPHA_VANTAGE_API_KEY（免费额度 25 次/天）")

    st.markdown("---")
    st.markdown("### 📐 架构说明")
    st.markdown(
        "**前端** (Streamlit) 负责用户交互与可视化。\n\n"
        "**后端** (Dify Workflow) 负责数据获取、清洗、评分和 LLM 报告生成。\n\n"
        "前端通过 Dify API 获取结构化 JSON，渲染图表和报告。"
    )

    st.markdown("---")
    st.markdown("### 🔗 Workflow 架构")
    steps = ["用户输入", "解析代码", "数据获取", "指标清洗", "评分计算", "LLM 报告", "结构化输出"]
    flow_html = '<div class="step-flow">'
    for i, s in enumerate(steps):
        flow_html += f'<span class="step-badge">{s}</span>'
        if i < len(steps) - 1:
            flow_html += '<span class="step-arrow">→</span>'
    flow_html += "</div>"
    st.markdown(flow_html, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📌 关于")
    st.markdown(
        "基于 **Dify Workflow** 的金融公司基本面对比助手。"
        "输入美股代码，后端自动获取数据并生成结构化对比报告。"
    )
    st.caption("内容仅用于公开信息整理和学习参考，不构成投资建议。")

# ──────────────── hero ───────────────────────────────────────────────

st.markdown(
    '<div class="hero">'
    "<h1>📊 金融公司基本面对比分析</h1>"
    "<p>输入 2–5 个美股股票代码，Dify Workflow 后端自动获取公开金融数据，生成估值、盈利能力、成长性和风险维度的结构化对比报告。</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ──────────────── input form ─────────────────────────────────────────

col_input1, col_input2, col_input3 = st.columns([3, 2, 1])

with col_input1:
    default_symbols = "NVDA, AAPL, MSFT" if "离线" in run_mode else ""
    symbols_raw = st.text_input(
        "股票代码（英文逗号分隔）",
        value=default_symbols,
        placeholder="例如 AAPL, MSFT, NVDA",
    )

with col_input2:
    analysis_focus = st.selectbox(
        "分析重点",
        ["综合对比", "估值分析", "盈利能力分析", "成长性分析", "风险分析"],
    )

with col_input3:
    language = st.selectbox("输出语言", ["中文", "English"])

if "离线" in run_mode:
    st.caption("🔒 离线演示模式：使用缓存数据（NVDA, AAPL, MSFT），展示完整 UI 效果。")

run_btn = st.button("🚀 开始分析", type="primary", use_container_width=True)

# ──────────────── main logic ─────────────────────────────────────────

if run_btn:
    if not symbols_raw.strip():
        st.warning("请输入至少一个股票代码。")
        st.stop()

    # ── fetch data from backend (or use cache) ──
    if "离线" in run_mode:
        result = CACHED_DEMO_RESPONSE
    else:
        url_ok = bool(dify_url and str(dify_url).strip())
        key_ok = bool(dify_key and str(dify_key).strip())
        if not url_ok and not key_ok:
            st.error("请在左侧边栏填写 **Dify Base URL** 与 **Dify API Key**（当前两项均为空）。")
            st.stop()
        if not url_ok:
            st.error("请在左侧边栏填写 **Dify Base URL**（当前为空）。")
            st.stop()
        if not key_ok:
            st.error("请在左侧边栏填写 **Dify API Key**（当前为空）。密钥在 Dify：该应用 → **API 访问** → 复制 API 密钥。")
            st.stop()
        with st.spinner("正在调用 Dify Workflow 后端 …"):
            try:
                result = call_dify_workflow(
                    dify_url.strip(), dify_key.strip(),
                    symbols_raw.strip(), analysis_focus, language, dify_data_mode,
                )
            except Exception as exc:
                st.error(f"Dify API 调用失败：{exc}")
                st.stop()

    company_data: list[dict] = result["company_data"]
    scored: list[dict] = result["scored"]
    report_text: str = result["report_text"]

    success = [c for c in company_data if c.get("status") == "success"]
    failed = [c for c in company_data if c.get("status") != "success"]

    # ── Section 1: data status ──
    st.markdown("---")
    st.markdown("## 1. 数据获取状态")
    status_rows = []
    for c in company_data:
        status_rows.append({
            "股票代码": c.get("symbol", "?"),
            "公司名称": c.get("name", "N/A"),
            "状态": "✅ 成功" if c.get("status") == "success" else "❌ 失败",
            "说明": c.get("error", "-") if c.get("status") != "success" else "-",
        })
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)

    if not success:
        st.error("没有成功获取到任何公司数据，无法继续分析。")
        st.stop()

    # ── Section 2: company overview cards ──
    st.markdown("## 2. 对比对象概览")
    card_cols = st.columns(len(success))
    for col, c in zip(card_cols, success):
        with col:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="label">{c["symbol"]}</div>'
                f'<div class="value">{c["name"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.caption(f'{c.get("sector", "")} · {c.get("industry", "")}')
            st.metric("Market Cap", c.get("market_cap", "N/A"))
            st.metric("Revenue TTM", c.get("revenue_ttm", "N/A"))

    # ── Section 3: key metrics ──
    st.markdown("## 3. 核心指标对比")

    tab_val, tab_grow, tab_analyst = st.tabs(["估值 & 盈利能力", "成长性 & 波动", "分析师评级"])

    with tab_val:
        val_rows = []
        for c in success:
            val_rows.append({
                "股票代码": c["symbol"],
                "PE Ratio": c.get("pe_ratio", "N/A"),
                "Forward PE": c.get("forward_pe", "N/A"),
                "PEG Ratio": c.get("peg_ratio", "N/A"),
                "EPS": c.get("eps", "N/A"),
                "Profit Margin": c.get("profit_margin", "N/A"),
                "Operating Margin": c.get("operating_margin", "N/A"),
                "ROE": c.get("roe", "N/A"),
                "ROA": c.get("roa", "N/A"),
            })
        st.dataframe(pd.DataFrame(val_rows), use_container_width=True, hide_index=True)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.plotly_chart(build_bar_metrics(success, "pe_ratio", "PE Ratio 对比"), use_container_width=True)
        with col_c2:
            st.plotly_chart(build_bar_metrics(success, "profit_margin", "Profit Margin (%) 对比"), use_container_width=True)

    with tab_grow:
        grow_rows = []
        for c in success:
            grow_rows.append({
                "股票代码": c["symbol"],
                "Revenue Growth YoY": c.get("revenue_growth_yoy", "N/A"),
                "Earnings Growth YoY": c.get("earnings_growth_yoy", "N/A"),
                "52W High": c.get("week_52_high", "N/A"),
                "52W Low": c.get("week_52_low", "N/A"),
                "Beta": c.get("beta", "N/A"),
            })
        st.dataframe(pd.DataFrame(grow_rows), use_container_width=True, hide_index=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.plotly_chart(build_bar_metrics(success, "revenue_growth_yoy", "Revenue Growth YoY (%) 对比"), use_container_width=True)
        with col_g2:
            st.plotly_chart(build_bar_metrics(success, "beta", "Beta 对比"), use_container_width=True)

    with tab_analyst:
        st.plotly_chart(build_analyst_stacked(success), use_container_width=True)

    # ── Section 4: scoring ──
    st.markdown("## 4. 研究优先级评分")

    if scored:
        col_radar, col_table = st.columns([1, 1])

        with col_radar:
            st.plotly_chart(build_radar(scored), use_container_width=True)

        with col_table:
            score_rows = []
            for idx, s in enumerate(scored, 1):
                score_rows.append({
                    "排名": idx,
                    "公司": s["name"],
                    "代码": s["symbol"],
                    "综合评分": s["total_score"],
                    "成长性": s["growth_score"],
                    "盈利能力": s["profitability_score"],
                    "估值匹配": s["valuation_score"],
                    "波动风险": s["risk_score"],
                })
            st.dataframe(pd.DataFrame(score_rows), use_container_width=True, hide_index=True)

        st.info(
            "⚠️ 研究优先级评分由 Dify Workflow 后端基于公开 API 指标计算，不是主观判断。"
            "综合评分越高仅说明在当前指标维度下更值得后续研究，不代表投资建议。",
            icon="ℹ️",
        )
    else:
        st.warning("后端未返回评分数据。")

    # ── Section 5: per-company detail ──
    st.markdown("## 5. 逐家公司详情")

    for c in success:
        with st.expander(f"🏢 {c['name']} ({c['symbol']})", expanded=False):
            st.markdown(f"**Sector:** {c.get('sector', 'N/A')} · **Industry:** {c.get('industry', 'N/A')}")
            st.markdown(f"> {c.get('description', 'N/A')}")

            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Market Cap", c.get("market_cap", "N/A"))
            d2.metric("PE Ratio", c.get("pe_ratio", "N/A"))
            d3.metric("EPS", c.get("eps", "N/A"))
            d4.metric("Beta", c.get("beta", "N/A"))

            d5, d6, d7, d8 = st.columns(4)
            d5.metric("Profit Margin", c.get("profit_margin", "N/A"))
            d6.metric("ROE", c.get("roe", "N/A"))
            d7.metric("Revenue Growth", c.get("revenue_growth_yoy", "N/A"))
            d8.metric("Earnings Growth", c.get("earnings_growth_yoy", "N/A"))

    # ── Section 6: AI report ──
    st.markdown("## 6. AI 分析报告")
    st.caption("由 Dify Workflow 后端的 LLM 节点生成")

    if report_text:
        with st.expander("📄 查看完整 AI 报告", expanded=True):
            st.markdown(report_text, unsafe_allow_html=True)
    else:
        st.warning("后端未返回 AI 报告文本。")

    # ── disclaimer ──
    st.markdown(
        '<div class="disclaimer">'
        "<strong>⚠️ 风险提示与免责声明</strong><br>"
        "• 数据由 Dify Workflow 后端从公开金融 API（Alpha Vantage）获取，可能存在延迟、缺失或字段异常。<br>"
        "• 免费 API 存在调用频率和每日额度限制。<br>"
        "• 单一 API 数据不足以支持完整投资决策。<br>"
        "• 当前分析未纳入宏观经济、竞争格局、管理层讨论、财报原文和最新新闻。<br>"
        "• 研究优先级评分仅为辅助排序，不代表投资建议。<br>"
        "<strong>本报告仅用于公开金融信息整理和学习参考，不构成投资建议、买卖建议或收益承诺。</strong>"
        "</div>",
        unsafe_allow_html=True,
    )
