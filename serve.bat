@echo off
REM RapidWatch local server — serves this folder at http://localhost:8000
cd /d "%~dp0"
echo.
echo  RapidWatch  -  http://localhost:8000/
echo  ------------------------------------------------
echo  Map  :  http://localhost:8000/rapidwatch-gulf-map.html
echo  Site :  http://localhost:8000/rapidwatch-gulf-ri.html
echo.
echo  Press Ctrl+C to stop the server.
echo.
start "" http://localhost:8000/rapidwatch-gulf-map.html
python -m http.server 8000 2>nul || py -m http.server 8000
