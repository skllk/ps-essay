# ps-essay

本仓库收集“留学文书评测器”产品文档、原型与实现代码。

## 目录

- [`docs/product_spec.md`](docs/product_spec.md)：产品规格与路线图。
- [`backend/`](backend/)：FastAPI 实现的初版评分与检测服务，包含自动化测试与运行指引。

## 快速开始（服务端）

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

运行后访问 `http://localhost:8000/docs` 可查看 API Swagger UI。

## 测试

```bash
cd backend
pytest
```
