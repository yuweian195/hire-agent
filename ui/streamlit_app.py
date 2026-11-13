"""HireAgent Streamlit workbench.

Run from the repository root:
    streamlit run ui/streamlit_app.py
"""

from __future__ import annotations

import csv
import html
import io
import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas import (  # noqa: E402
    BatchScreenRequest,
    BatchScreenResponse,
    InterviewEvaluateRequest,
    InterviewItem,
    InterviewReport,
    Recommendation,
    ScreeningResponse,
    ScreeningStage,
    ScreenRequest,
)
from app.services.interview import get_interview_service  # noqa: E402
from app.services.reporting import interview_markdown, screening_markdown  # noqa: E402
from app.services.screening import get_service  # noqa: E402
from app.tools.resume_parser import decode_text  # noqa: E402

st.set_page_config(
    page_title="HireAgent · 招聘筛选工作台",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
  .stApp { background: #f4f6fb; }
  [data-testid="stHeader"] { background: #f4f6fb; }
  [data-testid="stToolbar"] { visibility: hidden; height: 0; }
  [data-testid="stSidebar"] { background: #0f172a; }
  [data-testid="stSidebar"] * { color: #e2e8f0; }
  [data-testid="stSidebar"] .stSelectbox label { color: #94a3b8; }
  .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1400px; }
  h1, h2, h3 { letter-spacing: -0.02em; }
  .brand { font-size: 1.45rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.03em; }
  .brand span { color: #38bdf8; }
  .brand-sub { color: #94a3b8; font-size: 0.8rem; margin-top: 2px; }
  .side-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 12px 14px; margin: 10px 0; }
  .side-label { color: #94a3b8; font-size: 0.72rem; text-transform: uppercase; letter-spacing: .08em; }
  .side-value { color: #f1f5f9; font-size: 0.9rem; font-weight: 600; margin-top: 3px; }
  .dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 6px; }
  .dot.on { background: #22c55e; box-shadow: 0 0 8px #22c55e; }
  .dot.off { background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }
  .page-title { font-size: 1.9rem; font-weight: 800; color: #0f172a; margin-bottom: 2px; }
  .page-sub { color: #64748b; font-size: 0.92rem; margin-bottom: 20px; }
  .card { background: #ffffff; border: 1px solid #e6eaf2; border-radius: 16px; padding: 20px 22px; box-shadow: 0 1px 2px rgba(15,23,42,.04); }
  .card + .card { margin-top: 14px; }
  .section-label { font-size: 0.74rem; font-weight: 700; color: #64748b; letter-spacing: .1em; text-transform: uppercase; margin-bottom: 8px; }
  .hero-score { font-size: 3.2rem; font-weight: 800; line-height: 1; color: #0f172a; }
  .hero-score small { font-size: 1rem; color: #94a3b8; font-weight: 500; }
  .hero-name { font-size: 1.35rem; font-weight: 800; color: #0f172a; }
  .hero-job { color: #64748b; font-size: 0.86rem; margin-top: 2px; }
  .badge { display: inline-block; padding: 5px 11px; border-radius: 999px; font-size: 0.76rem; font-weight: 700; }
  .badge.recommend { background: #dcfce7; color: #15803d; }
  .badge.pass { background: #dcfce7; color: #15803d; }
  .badge.hold { background: #fef3c7; color: #b45309; }
  .badge.reject { background: #fee2e2; color: #b91c1c; }
  .metric-card { background: #f8fafc; border: 1px solid #edf1f7; border-radius: 12px; padding: 12px 14px; }
  .metric-label { font-size: 0.72rem; color: #64748b; margin-bottom: 4px; }
  .metric-value { font-size: 1.15rem; font-weight: 800; color: #0f172a; }
  .dim-row { margin: 10px 0 12px; }
  .dim-head { display: flex; justify-content: space-between; font-size: 0.82rem; color: #334155; margin-bottom: 5px; }
  .dim-head b { color: #0f172a; }
  .dim-track { height: 7px; background: #eef2f7; border-radius: 99px; overflow: hidden; }
  .dim-fill { height: 100%; border-radius: 99px; }
  .dim-reason { font-size: 0.74rem; color: #94a3b8; margin-top: 4px; }
  .chip { display: inline-block; padding: 4px 9px; margin: 2px 3px 2px 0; border-radius: 7px; font-size: 0.73rem; font-weight: 600; }
  .chip.ok { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
  .chip.miss { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
  .chip.neutral { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
  .summary-box { background: #f0f9ff; border-left: 3px solid #0ea5e9; border-radius: 8px; padding: 12px 14px; color: #0c4a6e; font-size: 0.87rem; line-height: 1.7; }
  .question-item { border: 1px solid #edf1f7; border-radius: 10px; padding: 12px 14px; margin-bottom: 9px; }
  .question-meta { font-size: 0.7rem; color: #0ea5e9; font-weight: 700; letter-spacing: .04em; }
  .question-text { font-size: 0.87rem; color: #1e293b; line-height: 1.65; margin-top: 4px; }
  .question-intent { font-size: 0.72rem; color: #94a3b8; margin-top: 4px; }
  .trace-step { display: flex; gap: 10px; padding: 7px 0; border-bottom: 1px dashed #eef2f7; font-size: 0.78rem; }
  .trace-node { color: #0f172a; font-weight: 700; min-width: 110px; }
  .trace-summary { color: #64748b; flex: 1; }
  .trace-ms { color: #94a3b8; font-variant-numeric: tabular-nums; }
  .empty-state { border: 1px dashed #cbd5e1; border-radius: 16px; padding: 48px 24px; text-align: center; color: #94a3b8; background: #fbfcfe; }
  .empty-state b { display: block; color: #475569; font-size: 1rem; margin-bottom: 6px; }
  .job-card { background: #fff; border: 1px solid #e6eaf2; border-radius: 14px; padding: 18px 20px; margin-bottom: 12px; }
  .job-title { font-size: 1rem; font-weight: 800; color: #0f172a; }
  .job-meta { color: #64748b; font-size: 0.78rem; margin: 3px 0 10px; }
  div[data-testid="stMetricValue"] { font-weight: 800; }
  .stButton > button[kind="primary"] { border-radius: 10px; font-weight: 700; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

REC_LABEL = {
    Recommendation.RECOMMEND: ("推荐", "recommend"),
    Recommendation.HOLD: ("待定", "hold"),
    Recommendation.REJECT: ("淘汰", "reject"),
}
STAGE_LABEL = {
    ScreeningStage.SCREENING: "初筛",
    ScreeningStage.INTERVIEW: "面试中",
    ScreeningStage.OFFER: "Offer",
    ScreeningStage.REJECTED: "已淘汰",
    ScreeningStage.TALENT_POOL: "人才库",
}
INTERVIEW_LABEL = {"pass": ("通过", "pass"), "hold": ("待定", "hold"), "reject": ("不通过", "reject")}
INTERVIEW_SAMPLE = ROOT / "data" / "interviews" / "sample_java.json"
SAMPLES = [
    ("张伟 · 高级 Java（强匹配）", "zhangwei.txt"),
    ("赵敏 · Java（中等匹配）", "zhaomin.txt"),
    ("王强 · 初级 Java（不匹配）", "wangqiang.txt"),
    ("陈晨 · AI 应用（强匹配）", "chenchen.txt"),
]


def load_sample(filename: str) -> None:
    path = ROOT / "data" / "resumes" / filename
    st.session_state.resume_input = path.read_text(encoding="utf-8")
    job = "llm-app" if filename == "chenchen.txt" else "java-senior"
    st.session_state.job_choice = job
    st.session_state.result = None


def reset_result() -> None:
    st.session_state.result = None


def load_interview_sample() -> None:
    data = json.loads(INTERVIEW_SAMPLE.read_text(encoding="utf-8"))
    st.session_state.interview_candidate = data["candidate_name"]
    st.session_state.interview_job = data["job_id"]
    st.session_state.interview_count = len(data["items"])
    for index, item in enumerate(data["items"]):
        st.session_state[f"iq_{index}"] = item["question"]
        st.session_state[f"ia_{index}"] = item["answer"]
        st.session_state[f"ic_{index}"] = item.get("category", "")
    st.session_state.interview_result = None


def score_color(score: float) -> str:
    if score >= 8:
        return "#16a34a"
    if score >= 6:
        return "#d97706"
    return "#dc2626"


def render_badge(rec: Recommendation) -> str:
    label, css = REC_LABEL[rec]
    return f'<span class="badge {css}">{label}</span>'


def render_chips(items: list[str], css: str, empty: str = "无") -> str:
    if not items:
        return f'<span class="chip neutral">{empty}</span>'
    return "".join(
        f'<span class="chip {css}">{html.escape(item)}</span>' for item in items
    )


def render_result(result: ScreeningResponse, key_prefix: str = "main") -> None:
    label, css = REC_LABEL[result.recommendation]
    st.markdown(
        f"""
        <div class="card">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
            <div>
              <div class="hero-name">{html.escape(result.candidate_name)}</div>
              <div class="hero-job">应聘 {html.escape(result.job_title)} · 流程 {STAGE_LABEL[result.stage]} · 筛选编号 {result.id}</div>
            </div>
            <div style="text-align:right;">
              <div class="hero-score">{result.total_score:.1f}<small>/10</small></div>
              <div style="margin-top:6px;"><span class="badge {css}">{label}</span></div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("JD 匹配度", f"{result.job_match.overall_rate:.0%}"),
        ("必备技能", f"{result.skill_match.required_rate:.0%}"),
        ("工作年限", f"{result.parsed_resume.years_experience:g} 年"),
        ("最高学历", result.parsed_resume.education_level or "未识别"),
    ]
    for column, (label, value) in zip((col1, col2, col3, col4), metrics, strict=True):
        with column:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">{label}</div>'
                f'<div class="metric-value">{html.escape(value)}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.05, 1])

    with left:
        rows = []
        for item in result.dimension_scores:
            width = max(2, int(item.score * 10))
            color = score_color(item.score)
            rows.append(
                f'<div class="dim-row">'
                f'<div class="dim-head"><span>{html.escape(item.label)}'
                f'<span style="color:#94a3b8"> · 权重 {item.weight:.0%}</span></span>'
                f'<b>{item.score:.1f}</b></div>'
                f'<div class="dim-track"><div class="dim-fill" '
                f'style="width:{width}%;background:{color};"></div></div>'
                f'<div class="dim-reason">{html.escape(item.reason)}</div>'
                f'</div>'
            )
        st.markdown(
            '<div class="card"><div class="section-label">六维评分</div>'
            + "".join(rows)
            + "</div>",
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            f"""
            <div class="card">
              <div class="section-label">筛选结论</div>
              <div class="summary-box">{html.escape(result.summary)}</div>
              <div style="margin-top:10px;font-size:0.78rem;color:#64748b;">{html.escape(result.recommendation_reason)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="card">
              <div class="section-label">技能覆盖</div>
              <div style="font-size:0.74rem;color:#94a3b8;margin-bottom:4px;">已命中</div>
              <div>{render_chips(result.skill_match.matched, "ok", "无")}</div>
              <div style="font-size:0.74rem;color:#94a3b8;margin:8px 0 4px;">缺失</div>
              <div>{render_chips(result.skill_match.missing, "miss", "无缺口")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if result.compliance.issues:
        st.markdown(
            '<div class="card" style="border-color:#fed7aa;background:#fffbeb;">'
            '<div class="section-label" style="color:#b45309;">JD 合规提示</div>'
            f'<div style="color:#92400e;font-size:0.84rem;">发现：{"、".join(result.compliance.issues)}。相关条件已从评分依据中剔除。</div></div>',
            unsafe_allow_html=True,
        )

    if result.questions:
        questions_html = "".join(
            f'<div class="question-item">'
            f'<div class="question-meta">{html.escape(q.category)} · {html.escape(q.difficulty)}</div>'
            f'<div class="question-text">{html.escape(q.question)}</div>'
            f'<div class="question-intent">考察意图：{html.escape(q.intent)}</div>'
            f'</div>'
            for q in result.questions
        )
        st.markdown(
            '<div class="card"><div class="section-label">针对性面试题</div>'
            + questions_html
            + "</div>",
            unsafe_allow_html=True,
        )

    with st.expander("查看 Agent 执行轨迹", expanded=False):
        steps = "".join(
            f'<div class="trace-step"><div class="trace-node">{html.escape(step.node)}</div>'
            f'<div class="trace-summary">{html.escape(step.summary)}</div>'
            f'<div class="trace-ms">{step.duration_ms} ms</div></div>'
            for step in result.trace
        )
        st.markdown(
            f'<div class="card" style="padding:14px 16px;">{steps}</div>',
            unsafe_allow_html=True,
        )

    st.download_button(
        "下载筛选报告（Markdown）",
        data=screening_markdown(result),
        file_name=f"screening-{result.candidate_name}-{result.id}.md",
        mime="text/markdown",
        key=f"download_screening_{key_prefix}_{result.id}",
    )


def render_interview_report(report: InterviewReport, key_prefix: str = "main") -> None:
    label, css = INTERVIEW_LABEL[report.recommendation.value]
    st.markdown(
        f"""
        <div class="card">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
            <div>
              <div class="hero-name">{html.escape(report.candidate_name)}</div>
              <div class="hero-job">面试评估 · {html.escape(report.job_title)} · 报告编号 {report.id}</div>
            </div>
            <div style="text-align:right;">
              <div class="hero-score">{report.overall_score:.1f}<small>/10</small></div>
              <div style="margin-top:6px;"><span class="badge {css}">{label}</span></div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="card"><div class="section-label">面试结论</div>'
        f'<div class="summary-box">{html.escape(report.summary)}</div></div>',
        unsafe_allow_html=True,
    )

    for index, item in enumerate(report.answer_evaluations, start=1):
        rows = []
        for key, label_text in (
            ("relevance", "相关性"),
            ("depth", "深度"),
            ("structure", "结构"),
            ("communication", "表达"),
        ):
            value = item.dimensions.get(key, 0)
            color = score_color(value)
            rows.append(
                f'<div class="dim-row"><div class="dim-head"><span>{label_text}</span>'
                f'<b>{value:.1f}</b></div>'
                f'<div class="dim-track"><div class="dim-fill" '
                f'style="width:{max(2, int(value * 10))}%;background:{color};"></div></div></div>'
            )
        st.markdown(
            f'<div class="card">'
            f'<div class="section-label">第 {index} 题 · {item.score:.1f}/10</div>'
            f'<div class="question-text" style="font-weight:600;">{html.escape(item.question)}</div>'
            + "".join(rows)
            + f'<div style="font-size:0.76rem;color:#64748b;margin-top:8px;">优势</div>'
            f'<div>{render_chips(item.strengths, "ok")}</div>'
            f'<div style="font-size:0.76rem;color:#64748b;margin-top:8px;">待改进</div>'
            f'<div>{render_chips(item.weaknesses, "miss")}</div>'
            f'<div class="summary-box" style="margin-top:10px;background:#f8fafc;border-left-color:#94a3b8;color:#475569;">'
            f'追问建议：{html.escape(item.follow_up)}</div></div>',
            unsafe_allow_html=True,
        )

    with st.expander("查看面试评估轨迹", expanded=False):
        steps = "".join(
            f'<div class="trace-step"><div class="trace-node">{html.escape(step.node)}</div>'
            f'<div class="trace-summary">{html.escape(step.summary)}</div>'
            f'<div class="trace-ms">{step.duration_ms} ms</div></div>'
            for step in report.trace
        )
        st.markdown(
            f'<div class="card" style="padding:14px 16px;">{steps}</div>',
            unsafe_allow_html=True,
        )

    st.download_button(
        "下载面试报告（Markdown）",
        data=interview_markdown(report),
        file_name=f"interview-{report.candidate_name}-{report.id}.md",
        mime="text/markdown",
        key=f"download_interview_{key_prefix}_{report.id}",
    )


service = get_service()

with st.sidebar:
    st.markdown('<div class="brand">Hire<span>Agent</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">智能招聘筛选工作台</div>', unsafe_allow_html=True)
    mode_class = "on" if service.llm.enabled else "off"
    mode_text = f"在线模型 · {service.llm.settings.llm_model}" if service.llm.enabled else "离线规则模式"
    st.markdown(
        f"""
        <div class="side-card">
          <div class="side-label">运行模式</div>
          <div class="side-value"><span class="dot {mode_class}"></span>{html.escape(mode_text)}</div>
        </div>
        <div class="side-card">
          <div class="side-label">评分阈值</div>
          <div class="side-value">推荐 ≥ 8.0 ｜ 待定 ≥ 6.0</div>
        </div>
        <div class="side-card">
          <div class="side-label">说明</div>
          <div class="side-value" style="font-weight:400;color:#cbd5e1;line-height:1.6;">
            评分由可解释规则计算；配置 API Key 后，评语与面试题可由 LLM 增强。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="page-title">招聘筛选工作台</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">上传或粘贴简历，选择目标岗位，生成可解释的六维评分、技能缺口与面试问题。</div>',
    unsafe_allow_html=True,
)

tab_screen, tab_batch, tab_interview, tab_history, tab_jobs = st.tabs(
    ["简历筛选", "批量筛选", "面试评估", "候选人库", "岗位库"]
)

with tab_screen:
    input_col, result_col = st.columns([0.4, 0.6], gap="large")

    with input_col:
        jobs = service.list_jobs()
        job_map = {job.id: job for job in jobs}
        if "job_choice" not in st.session_state:
            st.session_state.job_choice = jobs[0].id if jobs else None

        st.markdown('<div class="section-label">目标岗位</div>', unsafe_allow_html=True)
        selected_job_id = st.selectbox(
            "目标岗位",
            options=list(job_map.keys()),
            format_func=lambda job_id: f"{job_map[job_id].title} · {job_map[job_id].department}",
            key="job_choice",
            label_visibility="collapsed",
            on_change=reset_result,
        )
        selected_job = job_map[selected_job_id]

        st.markdown('<div class="section-label" style="margin-top:14px;">简历文件</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "上传简历（PDF / DOCX / TXT）",
            type=["pdf", "docx", "txt", "md"],
            label_visibility="collapsed",
        )
        uploaded_text = ""
        if uploaded is not None:
            uploaded_text = decode_text(uploaded.name, uploaded.getvalue())
            st.caption(f"已读取 {uploaded.name}，共 {len(uploaded_text)} 字符")

        st.markdown('<div class="section-label" style="margin-top:14px;">快速载入示例</div>', unsafe_allow_html=True)
        sample_cols = st.columns(2)
        for index, (label, filename) in enumerate(SAMPLES):
            with sample_cols[index % 2]:
                st.button(
                    label,
                    key=f"sample_{filename}",
                    width="stretch",
                    on_click=load_sample,
                    args=(filename,),
                )

        if "resume_input" not in st.session_state:
            st.session_state.resume_input = (
                ROOT / "data" / "resumes" / "zhangwei.txt"
            ).read_text(encoding="utf-8")

        st.markdown('<div class="section-label" style="margin-top:14px;">简历文本</div>', unsafe_allow_html=True)
        resume_text = st.text_area(
            "简历文本",
            key="resume_input",
            height=280,
            label_visibility="collapsed",
        )

        run = st.button("开始筛选", type="primary", width="stretch")

        if run:
            text = uploaded_text or resume_text
            if len(text.strip()) < 10:
                st.error("请上传简历文件或粘贴至少 10 个字符的简历文本。")
            else:
                with st.spinner("Agent 正在解析与评分…"):
                    try:
                        result = service.screen(
                            ScreenRequest(resume_text=text, job_id=selected_job_id)
                        )
                        st.session_state.result = result.model_dump(mode="json")
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"筛选失败：{exc}")

    with result_col:
        stored = st.session_state.get("result")
        if stored:
            render_result(ScreeningResponse.model_validate(stored))
        else:
            st.markdown(
                """
                <div class="empty-state">
                  <b>等待一次筛选</b>
                  左侧载入示例简历或上传文件，点击「开始筛选」查看评分、技能缺口与面试题。
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="card">
                  <div class="section-label">当前岗位要求</div>
                  <div style="font-size:0.86rem;color:#334155;line-height:1.8;">
                    <b>{html.escape(selected_job.title)}</b> · {selected_job.min_years} 年以上 ·
                    {html.escape(selected_job.education)}<br/>
                    必备技能：{html.escape("、".join(selected_job.required_skills))}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

with tab_batch:
    st.markdown('<div class="section-label">批量筛选与排名</div>', unsafe_allow_html=True)
    st.caption("一次上传多份简历，按综合评分自动排名，结果会写入候选人库并支持导出 CSV。")

    batch_jobs = service.list_jobs()
    batch_job_id = st.selectbox(
        "批量目标岗位",
        options=[job.id for job in batch_jobs],
        format_func=lambda job_id: next(
            job.title for job in batch_jobs if job.id == job_id
        ),
        key="batch_job",
    )
    batch_files = st.file_uploader(
        "选择多份简历（PDF / DOCX / TXT）",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
        key="batch_files",
    )
    if st.button("开始批量筛选", type="primary", key="run_batch"):
        if not batch_files:
            st.warning("请先选择至少一份简历。")
        else:
            texts = [decode_text(item.name, item.getvalue()) for item in batch_files]
            texts = [text for text in texts if len(text.strip()) >= 10]
            if not texts:
                st.error("上传的文件中没有解析出有效简历文本。")
            else:
                with st.spinner(f"正在筛选 {len(texts)} 份简历…"):
                    batch = service.screen_batch(
                        BatchScreenRequest(job_id=batch_job_id, resume_texts=texts)
                    )
                    st.session_state.batch_result = batch.model_dump(mode="json")

    stored_batch = st.session_state.get("batch_result")
    if stored_batch:
        batch = BatchScreenResponse.model_validate(stored_batch)
        st.markdown(
            f'<div class="section-label" style="margin-top:16px;">'
            f"{html.escape(batch.job_title)} · 共 {batch.total} 份简历</div>",
            unsafe_allow_html=True,
        )
        rows = [
            {
                "排名": item.rank,
                "候选人": item.screening.candidate_name,
                "评分": round(item.screening.total_score, 2),
                "结论": REC_LABEL[item.screening.recommendation][0],
                "匹配度": f"{item.screening.job_match.overall_rate:.0%}",
                "缺失技能": "、".join(item.screening.skill_match.missing) or "无",
            }
            for item in batch.items
        ]
        st.dataframe(rows, width="stretch", hide_index=True)

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["排名", "候选人", "评分", "结论", "匹配度", "缺失技能", "筛选编号"])
        for item in batch.items:
            screening = item.screening
            writer.writerow(
                [
                    item.rank,
                    screening.candidate_name,
                    f"{screening.total_score:.2f}",
                    screening.recommendation.value,
                    f"{screening.job_match.overall_rate:.0%}",
                    "、".join(screening.skill_match.missing),
                    screening.id,
                ]
            )
        st.download_button(
            "下载排名 CSV",
            data=buffer.getvalue().encode("utf-8-sig"),
            file_name=f"batch-{batch.job_id}.csv",
            mime="text/csv",
            key="download_batch",
        )

with tab_interview:
    interview_service = get_interview_service()
    if "interview_count" not in st.session_state:
        load_interview_sample()

    st.markdown('<div class="section-label">面试回答评估</div>', unsafe_allow_html=True)
    st.caption("逐题评估相关性、深度、结构与表达，输出面试结论、改进建议和追问。")

    interview_jobs = service.list_jobs()
    job_ids = [job.id for job in interview_jobs]
    if st.session_state.get("interview_job") not in job_ids:
        st.session_state.interview_job = job_ids[0] if job_ids else None

    head_col, name_col, sample_col = st.columns([0.45, 0.35, 0.2])
    with head_col:
        st.selectbox(
            "目标岗位",
            options=job_ids,
            format_func=lambda job_id: next(
                job.title for job in interview_jobs if job.id == job_id
            ),
            key="interview_job",
        )
    with name_col:
        st.text_input("候选人", key="interview_candidate")
    with sample_col:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.button("载入示例回答", on_click=load_interview_sample, width="stretch")

    count = int(st.session_state.get("interview_count", 0))
    for index in range(count):
        st.markdown(
            f'<div class="section-label" style="margin-top:14px;">第 {index + 1} 题</div>',
            unsafe_allow_html=True,
        )
        st.text_area("问题", key=f"iq_{index}", height=70)
        st.text_area("回答", key=f"ia_{index}", height=150)

    if st.button("开始面试评估", type="primary", key="run_interview"):
        items = []
        for index in range(count):
            question = st.session_state.get(f"iq_{index}", "").strip()
            answer = st.session_state.get(f"ia_{index}", "").strip()
            if question and answer:
                items.append(
                    InterviewItem(
                        question=question,
                        answer=answer,
                        category=st.session_state.get(f"ic_{index}", ""),
                    )
                )
        if not items:
            st.warning("请至少填写一道题的问题和回答。")
        else:
            with st.spinner("正在评估面试回答…"):
                report = interview_service.evaluate(
                    InterviewEvaluateRequest(
                        job_id=st.session_state.get("interview_job"),
                        candidate_name=st.session_state.get("interview_candidate", ""),
                        items=items,
                    )
                )
                st.session_state.interview_result = report.model_dump(mode="json")

    stored_interview = st.session_state.get("interview_result")
    current_interview_id = stored_interview.get("id") if stored_interview else None
    if stored_interview:
        render_interview_report(
            InterviewReport.model_validate(stored_interview), key_prefix="current"
        )

    recent_interviews = [
        item
        for item in interview_service.list_recent(10)
        if item.id != current_interview_id
    ]
    if recent_interviews:
        st.markdown(
            '<div class="section-label" style="margin-top:20px;">历史面试报告</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            [
                {
                    "时间": item.created_at.strftime("%m-%d %H:%M"),
                    "候选人": item.candidate_name,
                    "岗位": item.job_title,
                    "评分": round(item.overall_score, 2),
                    "结论": INTERVIEW_LABEL[item.recommendation.value][0],
                }
                for item in recent_interviews
            ],
            width="stretch",
            hide_index=True,
        )
        interview_options = {
            f"{item.created_at.strftime('%m-%d %H:%M')} · {item.candidate_name}": item.id
            for item in recent_interviews
        }
        chosen_interview = st.selectbox(
            "查看历史面试报告", options=list(interview_options.keys()), key="history_interview"
        )
        historical = interview_service.get_report(interview_options[chosen_interview])
        if historical:
            render_interview_report(historical, key_prefix="history")

with tab_history:
    items = service.list_recent(50)
    if not items:
        st.markdown(
            '<div class="empty-state"><b>暂无筛选记录</b>完成一次筛选后，记录会自动写入本地数据库。</div>',
            unsafe_allow_html=True,
        )
    else:
        rows = [
            {
                "时间": item.created_at.strftime("%m-%d %H:%M"),
                "候选人": item.candidate_name,
                "岗位": item.job_title,
                "评分": round(item.total_score, 2),
                "结论": REC_LABEL[item.recommendation][0],
                "匹配度": f"{item.match_rate:.0%}",
                "阶段": STAGE_LABEL.get(item.stage, item.stage.value),
            }
            for item in items
        ]
        st.markdown('<div class="section-label">最近筛选记录</div>', unsafe_allow_html=True)
        st.dataframe(rows, width="stretch", hide_index=True)
        options = {f"{item.created_at.strftime('%m-%d %H:%M')} · {item.candidate_name}": item.id for item in items}
        chosen = st.selectbox("查看详情", options=list(options.keys()))
        detail = service.get_screening(options[chosen])
        if detail:
            render_result(detail, key_prefix="history")
            stage_col, button_col = st.columns([0.55, 0.2])
            with stage_col:
                new_stage = st.selectbox(
                    "更新流程状态",
                    options=list(ScreeningStage),
                    format_func=lambda stage: STAGE_LABEL.get(stage, stage.value),
                    index=list(ScreeningStage).index(detail.stage),
                    key=f"stage_select_{detail.id}",
                )
            with button_col:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("保存状态", key=f"stage_save_{detail.id}", width="stretch"):
                    updated = service.update_stage(detail.id, new_stage)
                    if updated:
                        st.success(f"已更新为 {STAGE_LABEL.get(new_stage, new_stage.value)}")
                        st.rerun()
                    else:
                        st.error("更新失败，记录不存在。")

with tab_jobs:
    st.markdown('<div class="section-label">在招岗位</div>', unsafe_allow_html=True)
    for job in service.list_jobs():
        salary = (
            f"{job.salary_min // 1000}-{job.salary_max // 1000}K"
            if job.salary_min and job.salary_max
            else "面议"
        )
        chips = "".join(f'<span class="chip neutral">{html.escape(s)}</span>' for s in job.required_skills)
        st.markdown(
            f"""
            <div class="job-card">
              <div class="job-title">{html.escape(job.title)}</div>
              <div class="job-meta">{html.escape(job.department)} · {job.seniority} · {job.min_years} 年以上 · {salary}</div>
              <div style="font-size:0.82rem;color:#475569;line-height:1.7;">{html.escape(job.description)}</div>
              <div style="margin-top:10px;">{chips}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
