# ATS Service

HireAgent 的 Java Spring Boot 3 集成服务，负责任企岗位、候选人和筛选记录的持久化，模拟企业招聘系统中的 ATS 层。

## 运行

```bash
mvn spring-boot:run
```

- 端口：`8080`
- 数据库：`./data/ats.mv.db`（H2 文件库）
- 健康检查：`GET /api/health`

## 测试

```bash
mvn test
```

使用 MockMvc + H2 内存库，覆盖岗位查询、筛选写入、候选人创建、流程状态更新与错误处理。

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/jobs` | 岗位列表 |
| POST | `/api/jobs` | 创建岗位 |
| GET | `/api/candidates` | 候选人列表 |
| POST | `/api/candidates` | 创建候选人 |
| GET | `/api/screenings?jobId=` | 筛选记录 |
| POST | `/api/screenings` | 写入筛选结果 |
| PATCH | `/api/screenings/{id}/stage` | 更新流程状态 |
| GET | `/api/health` | 服务状态 |

Python Agent 通过 `ATS_BASE_URL` 调用本服务；未配置时使用本地 JSON + SQLite。
