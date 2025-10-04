# Essay Evaluation Backend

This directory contains a FastAPI application that implements the first iteration of the 留学文书评测器服务端。The API mirrors the product specification by exposing endpoints for综合评分、AI 风险检测与报告拉取。

## 目录结构

- `app/`：服务端源代码。
  - `main.py`：FastAPI 入口，包含 `/api/analyze`、`/api/ai-detect` 和 `/api/report/:id` 三个端点。
  - `scoring.py`：基于启发式的初版评分逻辑，实现内容、结构、语言维度计算。
  - `ai_detection.py`：在无法直接访问 GPTZero 时的本地概率估算器，输出句/段/文档级风险。
  - `storage.py`：内存级报告存储，便于生成报告 ID。
  - `text.py`：分词、句子/段落切分以及音节估算等文本工具函数。
- `tests/`：`pytest` 端到端接口测试。
- `requirements.txt`：运行所需依赖。
- `requirements-dev.txt`：开发与测试依赖。

## 快速开始

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

启动后访问 `http://localhost:8000/docs` 即可查看交互式文档。

## 单元测试

```bash
cd backend
pytest
```

## 后续迭代思路

- 将启发式打分替换为规则+模型混合的可配置引擎。
- 接入 GPTZero 官方 API，并补充鉴权与速率限制。
- 替换内存存储为数据库或对象存储，支持多实例部署。
- 输出 PDF/JSON 报告，与前端可视化对接。
