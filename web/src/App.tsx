import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchScreening, fetchScreenings, updateStage } from "./api";
import type { Recommendation, ScreeningDetail, ScreeningItem, Stage } from "./types";

const STAGES: { key: Stage; label: string; hint: string }[] = [
  { key: "screening", label: "初筛", hint: "待处理" },
  { key: "interview", label: "面试中", hint: "已推进" },
  { key: "offer", label: "Offer", hint: "待发放" },
  { key: "rejected", label: "已淘汰", hint: "归档" },
  { key: "talent_pool", label: "人才库", hint: "长期跟进" },
];

const STAGE_ORDER = STAGES.map((stage) => stage.key);
const RECOMMENDATION_LABEL: Record<Recommendation, string> = {
  recommend: "推荐",
  hold: "待定",
  reject: "淘汰",
};

function scoreTone(score: number): string {
  if (score >= 8) return "good";
  if (score >= 6) return "mid";
  return "bad";
}

function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export default function App() {
  const [items, setItems] = useState<ScreeningItem[]>([]);
  const [detail, setDetail] = useState<ScreeningDetail | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchScreenings();
      setItems(data);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "无法连接 FastAPI");
    } finally {
      setLoading(false);
    }
  }, []);

  const select = useCallback(async (id: string) => {
    setSelectedId(id);
    try {
      setDetail(await fetchScreening(id));
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "加载候选人详情失败");
    }
  }, []);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 30000);
    return () => window.clearInterval(timer);
  }, [load]);

  const move = async (item: ScreeningItem, direction: -1 | 1) => {
    const index = STAGE_ORDER.indexOf(item.stage);
    const next = STAGE_ORDER[index + direction];
    if (!next) return;
    try {
      await updateStage(item.id, next);
      await load();
      if (selectedId === item.id) {
        setDetail(await fetchScreening(item.id));
      }
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "更新流程状态失败");
    }
  };

  const filtered = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    if (!keyword) return items;
    return items.filter(
      (item) =>
        item.candidate_name.toLowerCase().includes(keyword) ||
        item.job_title.toLowerCase().includes(keyword),
    );
  }, [items, query]);

  const recommendCount = items.filter((item) => item.recommendation === "recommend").length;
  const activeCount = items.filter((item) => ["screening", "interview", "offer"].includes(item.stage)).length;

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <div className="eyebrow">HIREAGENT / TALENT PIPELINE</div>
          <h1>
            Hire<span>Agent</span> 招聘看板
          </h1>
          <div className="subline">候选人流程 · 评分 · 面试推进</div>
        </div>
        <div className="top-metrics">
          <div>
            <b>{items.length}</b>
            <span>候选人</span>
          </div>
          <div>
            <b>{recommendCount}</b>
            <span>推荐</span>
          </div>
          <div>
            <b>{activeCount}</b>
            <span>推进中</span>
          </div>
          <button type="button" onClick={() => void load()}>
            刷新
          </button>
        </div>
      </header>

      {error && <div className="error">数据加载失败：{error}</div>}

      <div className="toolbar">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="搜索候选人 / 岗位"
          aria-label="搜索候选人"
        />
        <span>{loading ? "同步中…" : "每 30 秒自动刷新"}</span>
      </div>

      <div className={`workspace ${detail ? "with-detail" : ""}`}>
        <main className="board">
          {STAGES.map((stage) => {
            const stageItems = filtered.filter((item) => item.stage === stage.key);
            return (
              <section className="column" key={stage.key}>
                <div className="column-head">
                  <span>{stage.label}</span>
                  <b>{stageItems.length}</b>
                  <small>{stage.hint}</small>
                </div>
                <div className="cards">
                  {stageItems.map((item) => (
                    <article
                      className={`card ${selectedId === item.id ? "selected" : ""}`}
                      key={item.id}
                      onClick={() => void select(item.id)}
                    >
                      <div className="card-head">
                        <div>
                          <strong>{item.candidate_name}</strong>
                          <div className="job">{item.job_title}</div>
                        </div>
                        <span className={`score ${scoreTone(item.total_score)}`}>
                          {item.total_score.toFixed(1)}
                        </span>
                      </div>
                      <div className="card-meta">
                        <span className={`rec ${item.recommendation}`}>
                          {RECOMMENDATION_LABEL[item.recommendation]}
                        </span>
                        <span>匹配 {Math.round(item.match_rate * 100)}%</span>
                      </div>
                      <div className="card-actions">
                        <button
                          type="button"
                          aria-label="退回上一阶段"
                          onClick={(event) => {
                            event.stopPropagation();
                            void move(item, -1);
                          }}
                        >
                          ←
                        </button>
                        <span>{formatTime(item.created_at)}</span>
                        <button
                          type="button"
                          aria-label="推进下一阶段"
                          onClick={(event) => {
                            event.stopPropagation();
                            void move(item, 1);
                          }}
                        >
                          →
                        </button>
                      </div>
                    </article>
                  ))}
                  {stageItems.length === 0 && <div className="column-empty">—</div>}
                </div>
              </section>
            );
          })}
        </main>

        {detail && (
          <aside className="detail">
            <div className="detail-head">
              <div>
                <div className="eyebrow">CANDIDATE DETAIL</div>
                <h2>{detail.candidate_name}</h2>
                <div className="job">{detail.job_title}</div>
              </div>
              <button type="button" className="close" onClick={() => setDetail(null)} aria-label="关闭详情">
                ×
              </button>
            </div>
            <div className="detail-score">
              <span className={scoreTone(detail.total_score)}>{detail.total_score.toFixed(1)}</span>
              <div>
                <span className={`rec ${detail.recommendation}`}>
                  {RECOMMENDATION_LABEL[detail.recommendation]}
                </span>
                <div className="muted">JD 匹配 {Math.round(detail.job_match.overall_rate * 100)}%</div>
              </div>
            </div>
            <p className="summary">{detail.summary}</p>

            <div className="detail-section">
              <h3>六维评分</h3>
              {detail.dimension_scores.map((dimension) => (
                <div className="dimension" key={dimension.key}>
                  <div>
                    <span>{dimension.label}</span>
                    <b>{dimension.score.toFixed(1)}</b>
                  </div>
                  <div className="track">
                    <i style={{ width: `${Math.min(100, dimension.score * 10)}%` }} />
                  </div>
                  <small>{dimension.reason}</small>
                </div>
              ))}
            </div>

            <div className="detail-section">
              <h3>技能覆盖</h3>
              <div className="chips">
                {detail.skill_match.matched.map((skill) => (
                  <span className="chip ok" key={skill}>
                    {skill}
                  </span>
                ))}
                {detail.skill_match.missing.map((skill) => (
                  <span className="chip miss" key={skill}>
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            <div className="detail-section">
              <h3>建议面试题</h3>
              {detail.questions.map((question, index) => (
                <div className="question" key={`${question.question}-${index}`}>
                  <div className="q-meta">
                    {question.category} · {question.difficulty}
                  </div>
                  <div>{question.question}</div>
                </div>
              ))}
            </div>

            <details className="trace">
              <summary>Agent 执行轨迹</summary>
              {detail.trace.map((step) => (
                <div className="trace-step" key={`${step.node}-${step.duration_ms}`}>
                  <b>{step.node}</b>
                  <span>{step.summary}</span>
                  <i>{step.duration_ms} ms</i>
                </div>
              ))}
            </details>
          </aside>
        )}
      </div>

      <footer>HireAgent · Python Agent + Java ATS + TypeScript Pipeline Board</footer>
    </div>
  );
}
