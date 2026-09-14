#!/bin/bash
cd /home/heet18/Coding-Workspace/Futuristic/Heet/Github/Bottleneck
exec python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
