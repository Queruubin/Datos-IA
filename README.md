# Verificador de información pública · San Cristóbal

Asistente de IA que responde preguntas de la ciudadanía sobre la gestión de la Alcaldía Local de San Cristóbal (Bogotá) usando datos oficiales, citando siempre la fuente y la fecha de corte. Cuando un dato no existe, lo dice y lo registra como vacío de información.

Los datos incluyen el **POAI 2025–2026** (lo planeado por meta), el **seguimiento de metas (PMR)**, los **presupuestos participativos** con sus compromisos (CRP), la alineación con los **ODS** y las **PQRS** de la Alcaldía Local, a partir del paquete curado por el equipo en [`curated_data/`](curated_data/README.md), además de la ejecución del PAC del portal de Datos Abiertos Bogotá.

## Cómo ejecutar la aplicación

Solo necesitas hacer esto una vez:

1. Instala **Python 3.12 o superior** desde [python.org](https://www.python.org/downloads/). En Windows, marca la casilla **"Add python.exe to PATH"** durante la instalación.
2. Instala **Node.js (versión LTS)** desde [nodejs.org](https://nodejs.org/).
3. Obtén una clave gratuita de Gemini en [aistudio.google.com](https://aistudio.google.com) con el botón **Get API key**.
4. Dentro de la carpeta `backend`, crea un archivo llamado `.env` con esta línea, reemplazando el texto por tu clave:

   ```
   GEMINI_API_KEY=tu_clave_aqui
   ```

   Si no lo creas, el script lo crea por ti y abre el Bloc de notas para que pegues la clave.

Después, cada vez que quieras usar la aplicación:

- **Windows:** haz doble clic en `iniciar.bat`.
- **macOS o Linux:** en una terminal, dentro de esta carpeta, ejecuta `./iniciar.sh`.

El script revisa que todo esté instalado, prepara el backend, carga los datos y abre la aplicación en el navegador en **http://localhost:5173**.

La **primera vez** tarda varios minutos porque instala dependencias, carga el paquete curado y descarga los datos del portal. Las siguientes veces arranca en segundos. Si los datos de `curated_data/` cambian o la aplicación necesita una versión nueva de la base, el script la reconstruye solo.

En Windows se abren dos ventanas, **Backend** y **Frontend**. No las cierres mientras uses la aplicación; para apagarla, cierra ambas.

### Problemas comunes

| Mensaje o síntoma | Solución |
|---|---|
| "No se encontró Python" | Reinstala Python marcando **"Add python.exe to PATH"** |
| "No se encontró Node.js" | Instala Node.js LTS y vuelve a abrir el script |
| El chat dice que el servicio está ocupado | Gemini está saturado; espera un momento y vuelve a preguntar |
| Faltan datos o quieres volver a descargar los del portal | Borra la carpeta `backend/data` y vuelve a ejecutar el script |
| "El paquete curado no supera la validación" | Algún archivo de `curated_data/` no coincide con su `manifest.json`: revisa el mensaje, que lista cada diferencia |
| "Port 5173 is already in use" | Ya hay una copia abierta: cierra las ventanas Backend y Frontend anteriores |

**Importante:** la clave de Gemini es personal. No la compartas ni la subas a GitHub; el archivo `.env` ya está excluido del repositorio.

## Estructura del proyecto

| Carpeta | Contenido |
|---|---|
| `backend/` | API en Python (FastAPI), ingesta de datos y agente con Gemini. Ver [backend/README.md](backend/README.md) |
| `frontend/` | Interfaz web en React + Tailwind. Ver [frontend/README.md](frontend/README.md) |
| `curated_data/` | Paquete de datos curado por el equipo (POAI, PMR, presupuestos participativos, CRP, ODS, PQRS). Ver [curated_data/README.md](curated_data/README.md) |
| `notebooks/` | Notebook de Colab con la exploración y limpieza de los datos |
| `docs/` | Documentación del proyecto |

## Documentación

- [PRD: requisitos del producto](docs/PRD.md)
- [Flujo de una pregunta, de la ciudadanía a la respuesta](docs/FLUJO_PREGUNTA_RESPUESTA.md)
- [Hallazgos de calidad en los datos](docs/HALLAZGOS_DATOS.md)
