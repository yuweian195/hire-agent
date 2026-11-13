# 架构说明

本文档说明 HireAgent 的模块边界、数据流与扩展点，作为 README 的补充。

## 1. 总体结构

```text
Streamlit UI ──┐
               ├── ScreeningService ── 筛选 LangGraph ── tools/*
FastAPI ───────┤
               └── InterviewService ── 面试 LangGraph ── tools/*
                                        │
                                        ├── LLMClient（可选）
                                        └── ScreeningRepository（SQLite）
```

设计原则：

1. **业务编排与工具分离**：`services/` 负责加载岗位、生成 ID、调用图、映射响应；`graph/` 只关心状态流转；`tools/` 是无状态的可测试函数。
2. **规则与 LLM 解耦**：所有分数由规则计算，LLM 只生成文本反馈。关闭 LLM 不影响主流程。
3. **仓储可替换**：服务通过 `ScreeningRepository` 访问 SQLite，后续替换 PostgreSQL 不需要改图节点。

## 2. 筛选链路

```text
parse_resume
  → extract_skills
  → evaluate_dimensions
  → calculate_total_score
  → match_jd
  → compliance_check
  → generate_recommendation
      ├─ recommend → generate_questions
      └─ hold / reject ──────────────┐
                                      ↓
                                  save_results
```

### 状态

`ScreeningState` 中的字段按阶段写入：

| 字段 | 写入节点 | 说明 |
|---|---|---|
| `parsed_resume` | parse_resume | 结构化简历 |
| `skills` | extract_skills | 技能词典命中结果 |
| `skill_match` | evaluate_dimensions | 必备/加分技能命中率 |
| `dimension_scores` | evaluate_dimensions | 六维评分与理由 |
| `total_score` | calculate_total_score | 加权总分 |
| `job_match` | match_jd | 匹配度与缺口 |
| `compliance` | compliance_check | JD 合规问题 |
| `recommendation` | generate_recommendation | recommend / hold / reject |
| `questions` | generate_questions | 仅推荐候选人生成 |
| `trace` | 每个节点 | 节点耗时与摘要 |

### 评分权重

| 维度 | 权重 |
|---|---:|
| 学历 | 15% |
| 经验 | 25% |
| 技能 | 25% |
| 项目 | 15% |
| 稳定性 | 10% |
| 潜力 | 10% |

## 3. 面试评估链路

```text
prepare_context
  → evaluate_answers
  → aggregate
  → generate_summary
  → save_report
```

单题评分：

| 维度 | 权重 | 规则信号 |
|---|---:|---|
| 相关性 | 35% | 岗位技能命中、问题关键词重合、行为题长度 |
| 深度 | 30% | 回答长度、量化数字、技术词、机制性表达 |
| 结构 | 20% | STAR/分点/首先其次等结构标记 |
| 表达 | 15% | 句长、口头语、冗余程度 |

面试结论：`≥ 7.5 通过`、`≥ 6.0 待定`、`< 6.0 不通过`。

## 4. 数据模型

SQLite 两张表：

### screenings

| 列 | 说明 |
|---|---|
| `id` | 12 位筛选编号 |
| `candidate_name` | 候选人姓名 |
| `job_id` / `job_title` | 岗位 |
| `total_score` | 综合评分 |
| `recommendation` | 筛选结论 |
| `match_rate` | 人岗匹配度 |
| `stage` | 流程阶段 |
| `created_at` | 创建时间 |
| `payload` | 完整响应 JSON（含评分、技能、面试题、trace） |

### interview_reports

| 列 | 说明 |
|---|---|
| `id` | 报告编号 |
| `candidate_name` | 候选人 |
| `job_id` / `job_title` | 岗位 |
| `overall_score` | 面试平均分 |
| `recommendation` | pass / hold / reject |
| `created_at` | 创建时间 |
| `payload` | 完整报告 JSON（含逐题评分、反馈、trace） |

## 5. 扩展点

- **新增评分维度**：在 `app/tools/scorer.py` 增加函数，并在 `WEIGHTS` 中注册；同步更新评估集。
- **接入向量检索**：新增 `app/tools/retriever.py`，在 `match_jd` 前增加语义召回节点；技能匹配仍保留规则命中列表。
- **替换数据库**：实现同样的仓储接口（`save`、`get`、`list_recent`、`update_stage`、`save_interview`、`get_interview`）。
- **接入真实 LLM**：配置 `.env` 即可；如需多模型路由，在 `LLMClient` 内按任务选择模型。
- **异步批处理**：`screen_batch` 目前同步执行，后续可替换为任务队列（Celery/RQ），API 返回任务 ID。

## 6. 部署

- 单机：`streamlit run ui/streamlit_app.py` + `uvicorn app.main:app`。
- 容器：`docker compose up --build`，API 8000，UI 8501。
- 数据：默认 `data/hire_agent.db`，生产环境建议挂载持久卷并替换为 PostgreSQL。
