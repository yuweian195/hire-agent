# Contributing

## 本地开发

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
pip install -e ".[dev]"
```

## 提交前检查

```bash
ruff check app ui tests scripts
pytest -q
python scripts/evaluate.py
```

## 代码约定

- 业务逻辑放在 `app/services/` 与 `app/graph/`，纯函数工具放在 `app/tools/`。
- 评分规则必须可解释、可单测；不要在没有评估集的情况下调整权重。
- LLM 调用必须允许失败降级，禁止让 LLM 返回的分数直接进入持久化结果。
- 新增接口同步更新 `README.md` 与 `docs/architecture.md`。

## 数据与隐私

仓库内所有简历、岗位与面试回答均为合成数据。请勿提交真实候选人信息、手机号、邮箱或公司内部数据。
