#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# 复用本机虚拟环境；如果 .venv 是别的系统/别的 Python 版本建的（直接拷贝目录常见），
# 里面的解释器无法运行，此时重建，避免“换台机器起不来”。
if [ ! -x .venv/bin/python ] || ! .venv/bin/python -c "import sys" >/dev/null 2>&1; then
  rm -rf .venv
  python3 -m venv .venv
fi

# 依赖版本全部锁在 requirements.txt；已装好就跳过，装也只装锁定版本
if ! .venv/bin/python -c "import fastapi, uvicorn, pydantic" >/dev/null 2>&1; then
  .venv/bin/python -m pip install -r requirements.txt
fi

exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
