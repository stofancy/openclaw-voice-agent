#!/bin/bash
set -a  # 自动导出所有变量
cd ~/workspaces/audio-proxy
source .env
set +a
cd backend
source venv/bin/activate
python -m voice_gateway.main
