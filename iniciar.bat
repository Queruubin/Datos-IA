@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Verificador San Cristobal - Inicio
cd /d "%~dp0"

echo.
echo ============================================================
echo   Verificador de informacion publica - San Cristobal
echo ============================================================
echo.

rem ---------------------------------------------------------------
rem 1. Required programs
rem ---------------------------------------------------------------
where python >nul 2>nul
if errorlevel 1 goto :no_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>nul
if errorlevel 1 goto :old_python

where npm >nul 2>nul
if errorlevel 1 goto :no_node

rem ---------------------------------------------------------------
rem 2. Gemini key in backend\.env
rem ---------------------------------------------------------------
if not exist "backend\.env" (
    > "backend\.env" echo GEMINI_API_KEY=
    echo [!] Se creo el archivo backend\.env.
    echo     Pega tu clave de Gemini despues de "GEMINI_API_KEY=", guarda el archivo
    echo     y vuelve a ejecutar iniciar.bat.
    echo     Puedes obtener una clave gratis en https://aistudio.google.com
    start "" notepad "backend\.env"
    goto :fail
)
findstr /r /c:"^GEMINI_API_KEY=..*" "backend\.env" >nul
if errorlevel 1 (
    echo [!] El archivo backend\.env no tiene la clave de Gemini.
    echo     Escribe tu clave despues de "GEMINI_API_KEY=", guarda y vuelve a ejecutar.
    start "" notepad "backend\.env"
    goto :fail
)
echo [ok] Clave de Gemini encontrada.

rem ---------------------------------------------------------------
rem 3. Backend: virtual environment and dependencies
rem ---------------------------------------------------------------
if not exist "backend\.venv\Scripts\python.exe" (
    echo [..] Creando entorno de Python ^(solo la primera vez^)...
    python -m venv "backend\.venv"
    if errorlevel 1 goto :step_failed
)
echo [..] Instalando o actualizando dependencias del backend...
"backend\.venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -e backend
if errorlevel 1 goto :step_failed
echo [ok] Backend listo.

rem ---------------------------------------------------------------
rem 4. Data: download and clean the open data (first run only)
rem ---------------------------------------------------------------
if exist "backend\data\san_cristobal.duckdb" goto :data_ready
echo [..] Descargando y limpiando los datos del portal (solo la primera vez, puede tardar unos minutos)...
pushd backend
".venv\Scripts\python.exe" -m app.cli ingest
set "INGEST_RESULT=%errorlevel%"
popd
if not "%INGEST_RESULT%"=="0" goto :step_failed
:data_ready
echo [ok] Datos listos.

rem ---------------------------------------------------------------
rem 5. Frontend dependencies
rem ---------------------------------------------------------------
echo [..] Instalando o actualizando dependencias del frontend...
pushd frontend
call npm install --no-audit --no-fund --loglevel=error
set "NPM_RESULT=%errorlevel%"
popd
if not "%NPM_RESULT%"=="0" goto :step_failed
echo [ok] Frontend listo.

rem ---------------------------------------------------------------
rem 6. Start both servers in their own windows and open the browser
rem ---------------------------------------------------------------
echo [..] Iniciando la aplicacion...
start "Backend - Verificador San Cristobal" /d "%~dp0backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.api.main:app --port 8000"
start "Frontend - Verificador San Cristobal" /d "%~dp0frontend" cmd /k "npm run dev -- --port 5173 --strictPort"

timeout /t 8 /nobreak >nul
start "" "http://localhost:5173"

echo.
echo ============================================================
echo   La aplicacion esta corriendo en http://localhost:5173
echo.
echo   Se abrieron dos ventanas: Backend y Frontend.
echo   No las cierres mientras uses la aplicacion.
echo   Para apagarla, cierra esas dos ventanas.
echo ============================================================
echo.
pause
exit /b 0

rem ---------------------------------------------------------------
rem Error messages
rem ---------------------------------------------------------------
:no_python
echo [X] No se encontro Python.
echo     Instala Python 3.12 o superior desde https://www.python.org/downloads/
echo     y marca la opcion "Add python.exe to PATH" durante la instalacion.
goto :fail

:old_python
echo [X] Tu version de Python es muy antigua. Se necesita Python 3.12 o superior.
echo     Descargala desde https://www.python.org/downloads/
goto :fail

:no_node
echo [X] No se encontro Node.js.
echo     Instala la version LTS desde https://nodejs.org/
goto :fail

:step_failed
echo.
echo [X] Algo fallo en el paso anterior. Revisa el mensaje de arriba.
echo     Si el problema es de internet, vuelve a intentarlo en unos minutos.
goto :fail

:fail
echo.
pause
exit /b 1
