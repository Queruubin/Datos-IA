# Frontend · Verificador de información pública · San Cristóbal

Interfaz web del agente de verificación: un chat donde cualquier persona pregunta por la gestión de la Alcaldía Local de San Cristóbal y recibe respuestas con evidencia de datos oficiales, una página de **Fuentes** con la fecha de corte de cada conjunto de datos y una página de **Consumo** con los tokens usados y su costo equivalente.

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
  hooks/        useChat, useSources y useUsage: estado y llamadas a la API
  components/   componentes de presentación (MessageBubble, EvidenceCard, VerdictBadge,
                GapCard, PetitionCard, WelcomeFlow, PlaceScene, ExampleQuestions, ChatInput,
                SourcesTable, UsageReportView, ...)
    charts/     ChartCard, BarChart (barras y barras agrupadas), LineChart (SVG), KpiTiles
  pages/        ChatPage, SourcesPage y UsagePage
  lib/          formato de fechas, valores y costos (es-CO), ejemplos, fotos y créditos (places.ts),
                plantilla del derecho de petición (petition.ts), localStorage seguro, validación de enlaces
```

La navegación usa el hash de la URL: `#/` para el chat, `#/fuentes` para las fuentes y `#/consumo` para el consumo.

## Consumo

- Debajo de cada respuesta aparece una línea discreta con los tokens y el costo, por ejemplo `≈ 3.240 tokens · USD 0,0021 · COP 8`. Los costos muy pequeños se muestran con suficientes decimales para no aparecer como 0; si un costo no se conoce, no se muestra.
- La página **Consumo** (`GET /api/usage`) muestra preguntas, tokens, costo equivalente en USD y COP, costo promedio por pregunta, el desglose por modelo y por día, la TRM usada (valor, fecha y fuente) y la tabla de precios con su enlace oficial.
- Con el plan gratuito de Gemini el costo real es $0; las cifras son el equivalente en el plan pagado.

## Diseño y experiencia

- **Bienvenida en 3 pasos** la primera vez ("Hola. ¿Exploramos la localidad?" → "Pregunta, comprende y actúa." → "¿Qué quieres saber o hacer?"), con *Saltar*. Se recuerda en `localStorage` (si el navegador lo bloquea, simplemente vuelve a aparecer) y se reabre con *Ver introducción* en el encabezado.
- **Fotos de la localidad** de fondo, enlazadas desde Wikimedia Commons (Páramo de Cruz Verde, Iglesia y barrio 20 de Julio, Parque Estadio San Cristóbal Sur). Cada foto muestra su crédito obligatorio: autor, licencia (CC BY-SA) y enlace a Commons. Si la imagen no carga, queda un fondo cálido y se oculta el crédito. Fuentes y Consumo usan fondo liso para leer mejor las tablas.
- **Gráficos** encima del texto de la respuesta. Los arma el backend con código a partir de los datos de las herramientas (nunca Gemini) y solo con evidencia citada. Se dibujan con Tailwind + SVG, sin librería de gráficos: barras horizontales, barras agrupadas con leyenda, línea mensual e indicadores. Cada gráfico tiene título, unidad, fecha de corte, enlace a su evidencia y *Ver datos* con la tabla de valores completos. Los pesos se abrevian (`$25,5 mil M`) y el valor completo está en la tabla y al pasar el cursor. Colores validados para daltonismo.
- **Derecho de petición**: cuando un dato no está publicado, se ofrece un borrador editable hecho con una plantilla fija (sin IA, sin cifras, sin datos personales) para copiar y radicar en Bogotá Te Escucha. Nada se envía automáticamente.
- Accesibilidad: sin desplazamiento horizontal a 375 px, contraste AA, foco visible y animaciones desactivadas con `prefers-reduced-motion`.
