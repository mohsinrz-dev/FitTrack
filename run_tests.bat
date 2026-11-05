@echo off
set USE_FAKE_MONGO=1
call .venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
