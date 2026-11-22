# Frontend · Verificador de información pública · San Cristóbal

Interfaz web del agente de verificación: un chat donde cualquier persona pregunta por la gestión de la Alcaldía Local de San Cristóbal y recibe respuestas con evidencia de datos oficiales, y una página de **Fuentes** con la fecha de corte de cada conjunto de datos.

Tecnología: Vite + React + TypeScript + Tailwind CSS v4. Pruebas con Vitest y Testing Library.

## Requisitos

- Node.js 22 y npm 10.
- El backend en ejecución en el puerto 8000. Desde la carpeta `backend/`:

  ```bash
  uvicorn app.api.main:app --reload
  ```

  El backend ya permite solicitudes (CORS) desde `http://localhost:5173`.

## Instalación y uso

```bash
cd frontend
npm install
npm run dev        # abre http://localhost:5173
```

## Variable de entorno

| Variable | Valor por defecto | Uso |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | URL base del backend |

Para cambiarla, crea un archivo `frontend/.env.local` (no se sube al repositorio) con:

```bash
VITE_API_URL=http://localhost:8000
```

O defínela al ejecutar el comando, por ejemplo `VITE_API_URL=https://mi-backend.example npm run build`.

## Scripts

| Comando | Qué hace |
|---|---|
| `npm run dev` | Servidor de desarrollo |
| `npm test` | Pruebas en modo observación (`npm test -- --run` para ejecutarlas una vez) |
| `npm run lint` | Revisión de código con oxlint (el linter que trae la plantilla actual de Vite) |
| `npm run build` | Revisión de tipos y compilación de producción en `dist/` |
| `npm run preview` | Sirve la compilación de `dist/` |

## Estructura

```
src/
  api/          cliente HTTP tipado (tiempo límite de 60 s) y mensajes de error
  hooks/        useChat y useSources: estado y llamadas a la API
  components/   componentes de presentación (MessageBubble, EvidenceCard, VerdictBadge,
                GapCard, ExampleQuestions, ChatInput, SourcesTable, ...)
  pages/        ChatPage y SourcesPage
  lib/          formato de fechas, ejemplos, validación de enlaces
```

La navegación usa el hash de la URL: `#/` para el chat y `#/fuentes` para las fuentes.
