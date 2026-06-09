@echo off
cd /d "%~dp0"

echo ============================================
echo   НИХ Байтерек — запуск сервера
echo ============================================

:: Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден. Установите Python 3.10+
    pause
    exit /b
)

:: Устанавливаем зависимости если нужно
echo [1/2] Проверка зависимостей...
pip install -r requirements.txt --quiet

echo [2/2] Запуск сервера на http://10.1.4.54:8000
echo.
echo Для остановки нажмите Ctrl+C
echo ============================================
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000

pause
