@echo off
echo Running ingest (force re-build of knowledge base)...
py backend/ingest.py --force
pause
