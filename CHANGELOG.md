# Changelog

## [0.2.0] - 2026-11-13

### Added

- 面试回答评估 Agent：相关性、深度、结构、表达四维评分，输出通过/待定/不通过、优势、风险与追问建议。
- 批量筛选：一次处理多份简历，按综合评分排名并导出 CSV。
- 候选人流程管理：初筛、面试中、Offer、已淘汰、人才库五种状态。
- 筛选报告与面试报告 Markdown 导出。
- 面试评估独立 LangGraph 子图（5 个节点）。
- 新增 7 个测试，总计 22 个测试。
- 架构文档、面试评估截图、CONTRIBUTING 与 LICENSE。
- Java Spring Boot 3 ATS 集成服务（岗位 / 候选人 / 筛选记录，H2 + MockMvc）。
- Python `AtsClient`：通过 `ATS_BASE_URL` 加载岗位并回写筛选结果，失败自动回退。
- 岗位级评分权重：岗位 JSON 可覆盖六维权重并自动归一化。
- LLM PII 脱敏：默认不把候选人姓名/联系方式写入 Prompt。
- TypeScript + React 招聘看板（Vite 构建，FastAPI `/board` 静态挂载）。

### Changed

- 工作台扩展为 5 个标签页：简历筛选、批量筛选、面试评估、候选人库、岗位库。
- README 补充面试评估、批量筛选、流程状态和 API 说明。

## [0.1.0] - 2026-11-13

### Added

- 简历解析（PDF/DOCX/TXT/Markdown）。
- 六维评分、人岗匹配、JD 合规检查与条件路由。
- 针对性面试题生成。
- FastAPI 服务、Streamlit 工作台、SQLite 持久化。
- 可选 OpenAI-compatible LLM 增强与离线降级。
- 离线评估集与 15 个测试。
