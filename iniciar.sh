#!/usr/bin/env bash
# One-command start for macOS and Linux: prepares backend, data and frontend, then runs both.
# Stop everything with Ctrl+C.
set -euo pipefail
cd "$(dirname "$0")"

echo
echo "============================================================"
echo "  Verificador de información pública - San Cristóbal"
echo "============================================================"
echo

PYTHON=$(command -v python3 || command -v python || true)
if [ -z "$PYTHON" ]; then
  echo "[X] No se encontró Python. Instala Python 3.12 o superior: https://www.python.org/downloads/"
  exit 1
fi
if ! "$PYTHON" -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)"; then
  echo "[X] Se necesita Python 3.12 o superior: https://www.python.org/downloads/"
  exit 1
fi
if ! command -v npm >/dev/null; then
  echo "[X] No se encontró Node.js. Instala la versión LTS: https://nodejs.org/"
  exit 1
fi

if [ ! -f backend/.env ]; then
  echo "GEMINI_API_KEY=" > backend/.env
  echo "[!] Se creó backend/.env. Pega tu clave de Gemini después de 'GEMINI_API_KEY=',"
  echo "    guarda el archivo y vuelve a ejecutar ./iniciar.sh"
  echo "    Clave gratis en https://aistudio.google.com"
  exit 1
fi
if ! grep -Eq '^GEMINI_API_KEY=.+' backend/.env; then
  echo "[!] backend/.env no tiene la clave de Gemini. Escríbela después de 'GEMINI_API_KEY='."
  exit 1
fi
echo "[ok] Clave de Gemini encontrada."

if [ ! -x backend/.venv/bin/python ]; then
  echo "[..] Creando entorno de Python (solo la primera vez)..."
  "$PYTHON" -m venv backend/.venv
fi
echo "[..] Instalando o actualizando dependencias del backend..."
backend/.venv/bin/python -m pip install --quiet --disable-pip-version-check -e backend
echo "[ok] Backend listo."

if [ ! -f backend/data/san_cristobal.duckdb ]; then
  echo "[..] Descargando y limpiando los datos (solo la primera vez, puede tardar unos minutos)..."
  (cd backend && .venv/bin/python -m app.cli ingest)
fi
echo "[ok] Datos listos."

echo "[..] Instalando o actualizando dependencias del frontend..."
(cd frontend && npm install --no-audit --no-fund --loglevel=error)
echo "[ok] Frontend listo."

(cd backend && .venv/bin/python -m uvicorn app.api.main:app --port 8000) &
BACKEND_PID=$!
trap 'kill $BACKEND_PID 2>/dev/null || true' EXIT INT TERM

(sleep 6 && { command -v open >/dev/null && open http://localhost:5173 || xdg-open http://localhost:5173 || true; }) >/dev/null 2>&1 &

echo
echo "La aplicación está corriendo en http://localhost:5173 (Ctrl+C para apagarla)"
echo
cd frontend && npm run dev -- --port 5173 --strictPort
