@echo off
echo Running ingest (force re-build of knowledge base)...
"C:\Users\AL HAMD TRADERS\AppData\Local\Python\bin\python.exe" backend/ingest.py --force
pause
