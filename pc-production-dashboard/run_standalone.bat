@echo off
echo Starting Standalone PC Manufacturing Dashboard...
echo Port: 8507
echo URL: http://localhost:8507
echo.
python -m streamlit run standalone_dashboard.py --server.port 8507
pause