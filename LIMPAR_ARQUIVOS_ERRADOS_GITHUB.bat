@echo off
chcp 65001 >nul
echo Limpando arquivos temporarios e duplicados do repositorio...
cd /d "%~dp0"

if exist manage.py del /f /q manage.py
if exist build.sh del /f /q build.sh
if exist requirements.txt del /f /q requirements.txt
if exist corrigir_migrations_postgres_neon_v2.ps1 del /f /q corrigir_migrations_postgres_neon_v2.ps1

for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc >nul 2>nul
del /s /q *.pyo >nul 2>nul

if exist backend\staticfiles rmdir /s /q backend\staticfiles
if exist backend\db.sqlite3 del /f /q backend\db.sqlite3

echo.
echo OK: limpeza concluida.
echo Agora abra o GitHub Desktop, faça Commit e Push.
pause
