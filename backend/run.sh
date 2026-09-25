#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# 换机器或换系统后，旧 .venv 里的解释器路径可能已失效（比如从别的平台拷过来的），
# 先验证、不可用就重建，保证任何机器上都按 requirements.txt 装出同一份依赖。
if ! .venv/bin/python --version >/dev/null 2>&1; then
  rm -rf .venv
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
