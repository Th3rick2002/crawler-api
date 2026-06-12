# University Career Web Crawler & Analytics System

Este proyecto es un sistema modular e inteligente de rastreo web (Web Crawler), extracción de datos (Scraper) y análisis de información de ofertas académicas y carreras universitarias. Utiliza una arquitectura basada en el patrón de base de datos Medallion (utilizando SQLite) y proporciona una interfaz web interactiva tipo Dashboard para visualizar las métricas y exportar reportes.

---

## 🚀 Descripción General

El **University Career Web Crawler & Analytics System** realiza las siguientes tareas principales:
1. **Rastreo Web Inteligente (Crawling):** Explora de forma autónoma y asíncrona (utilizando `BackgroundTasks` de FastAPI) sitios web universitarios en búsqueda de planes de estudio y páginas de carreras empleando un algoritmo BFS (Breadth-First Search). Implementa políticas de cortesía web para evitar baneos (tiempos de espera aleatorios entre 1.5 y 3.5 segundos y rotación de User-Agent).
2. **Extracción y Limpieza (Scraping):** Analiza el contenido HTML de las páginas usando BeautifulSoup4, aislando el contenido semántico principal (como `<main>` o `<article>`) y descartando cabeceras, menús laterales y pies de página redundantes.
3. **Procesamiento de Datos y Análisis (Mining):** Limpia el texto en español (remoción de signos de puntuación y stopwords o palabras vacías) y procesa los datos con Pandas para calcular la frecuencia de palabras y descubrir métricas clave.
4. **Inferencia de Filtros Dinámicos (Clasificación):** Clasifica automáticamente los registros según palabras clave para determinar el área académica (ej. *Ingeniería, Ciencias de la Salud, Ciencias Sociales*) y el nivel del título (ej. *Licenciatura, Ingeniería, Técnico, Maestría*).
5. **Dashboard e Interfaz de Usuario:** Muestra métricas agregadas mediante gráficos de Chart.js y una tabla interactiva con filtros dinámicos. Permite la exportación de los datos limpios a formatos Excel, PDF o la descarga directa de la base de datos Gold.

---

## 🧹 Filtros de Refinamiento y Control de Ruido

Para garantizar que solo la oferta académica legítima llegue al nivel **Gold DB**, el sistema implementa tres niveles de filtros estrictos:

1. **Filtro de URLs (Lista Negra Estricta):** Bloquea de forma proactiva rutas no deseadas que no corresponden a programas de estudio, tales como `['/noticia/', '/noticias/', '/blog/', '/evento/', '/eventos/', '/calendario/', '/contacto/', '/about/', '/servicios/', '/category/', '/tag/']`.
2. **Limpieza Avanzada de HTML (BeautifulSoup):** Antes de procesar el texto, destruye las etiquetas de ruido estructural (`nav`, `footer`, `header`, `aside`, `script`, `style`, `form`, `iframe`) y extrae el texto únicamente de los contenedores semánticos principales (`<main>`, `<article>`, o divs con clase `main`, `content`, `contenido`).
3. **Filtros Vectoriales en Pandas (Pipeline de Silver/Gold):**
   * **Filtro de Plantillas (Lorem Ipsum):** Elimina registros cuyas descripciones contengan textos de plantilla o relleno como `"Lorem ipsum"` u `"odio dignissimos"`.
   * **Filtro de Longitud de Título:** Elimina registros cuyo título contenga más de 10 palabras (típico de artículos de noticias y blogs).
   * **Filtro de Prefijo Académico (Regex):** Asegura que el título comience obligatoriamente con un prefijo de grado/título académico válido: `^(?:Ingeniería|Licenciatura|Técnico|Maestría|Doctorado|Profesorado)`.

---

## 🛠️ Arquitectura Medallion (SQLite)

El sistema aísla sus cargas de trabajo y etapas de procesamiento utilizando tres bases de datos SQLite independientes almacenadas en la carpeta `data/`:

*   **Bronze DB (`1_bronze_raw.db`):** Almacena la ingesta bruta del crawler (URLs visitadas, estado HTTP, HTML original y un log de URLs que fallaron).
*   **Silver DB (`2_silver_analytics.db`):** Contiene la información procesada (carreras detectadas, descripción limpia, recuentos de palabras y términos frecuentes).
*   **Gold DB (`3_gold_delivery.db`):** Estructura los datos limpios y clasificados listos para ser consumidos por el panel web o exportados en reportes.

---

## 📂 Estructura del Proyecto

A continuación se detalla la estructura modular del proyecto. Puede hacer clic en los enlaces de los archivos para acceder a ellos directamente:

*   [requirements.txt](file:///home/erick/PycharmProjects/crawler/requirements.txt): Archivo de dependencias y librerías del proyecto.
*   [LICENSE](file:///home/erick/PycharmProjects/crawler/LICENSE): Licencia pública general GNU GPL v3.0.
*   [GEMINI.md](file:///home/erick/PycharmProjects/crawler/GEMINI.md): Especificaciones de diseño y requerimientos del sistema.
*   `src/`: Directorio principal del código fuente.
    *   [src/main.py](file:///home/erick/PycharmProjects/crawler/src/main.py): Punto de entrada e inicialización de la aplicación FastAPI.
    *   `src/crawler/`: Módulo encargado de la ingesta y rastreo web.
        *   [src/crawler/__init__.py](file:///home/erick/PycharmProjects/crawler/src/crawler/__init__.py): Archivo de inicialización del paquete.
        *   [src/crawler/database.py](file:///home/erick/PycharmProjects/crawler/src/crawler/database.py): Gestión de esquemas y conexiones de la base de datos Bronze.
        *   [src/crawler/engine.py](file:///home/erick/PycharmProjects/crawler/src/crawler/engine.py): Núcleo del Crawler BFS, manejo de cola y descargas.
        *   [src/crawler/utils.py](file:///home/erick/PycharmProjects/crawler/src/crawler/utils.py): Funciones de soporte (validación de URLs, User-Agents y retrasos).
    *   `src/analyzer/`: Módulo encargado de la minería de texto y análisis de datos.
        *   [src/analyzer/__init__.py](file:///home/erick/PycharmProjects/crawler/src/analyzer/__init__.py): Archivo de inicialización del paquete.
        *   [src/analyzer/database.py](file:///home/erick/PycharmProjects/crawler/src/analyzer/database.py): Gestión de esquemas y conexiones de la base de datos Silver.
        *   [src/analyzer/dynamic_filters.py](file:///home/erick/PycharmProjects/crawler/src/analyzer/dynamic_filters.py): Lógica de clasificación e inferencia de tipos de título y áreas académicas.
        *   [src/analyzer/pipeline.py](file:///home/erick/PycharmProjects/crawler/src/analyzer/pipeline.py): Limpieza de texto, filtrado de stopwords y carga hacia Gold.
    *   `src/delivery/`: Módulo encargado de la visualización, API y exportación de datos.
        *   [src/delivery/__init__.py](file:///home/erick/PycharmProjects/crawler/src/delivery/__init__.py): Archivo de inicialización del paquete.
        *   [src/delivery/database.py](file:///home/erick/PycharmProjects/crawler/src/delivery/database.py): Gestión de esquemas y conexiones de la base de datos Gold.
        *   [src/delivery/reporting.py](file:///home/erick/PycharmProjects/crawler/src/delivery/reporting.py): Lógica para generar archivos Excel (`.xlsx`) y PDF (`.pdf`).
        *   [src/delivery/routes.py](file:///home/erick/PycharmProjects/crawler/src/delivery/routes.py): Controladores y rutas HTTP (Páginas del frontend y APIs).
    *   `src/templates/`: Vistas y plantillas HTML integradas con Jinja2 y Tailwind CSS.
        *   [src/templates/base.html](file:///home/erick/PycharmProjects/crawler/src/templates/base.html): Estructura base que contiene el Sidebar, Navbar y estilos.
        *   [src/templates/index.html](file:///home/erick/PycharmProjects/crawler/src/templates/index.html): Panel principal (Dashboard) con estadísticas generales y gráficos.
        *   [src/templates/explore.html](file:///home/erick/PycharmProjects/crawler/src/templates/explore.html): Interfaz interactiva para buscar y filtrar carreras con opciones de exportación.

---

## 🛠️ Tecnologías Utilizadas

Las tecnologías principales implementadas en el desarrollo de este proyecto son:

1.  **Python (v3.x):** Lenguaje de programación base.
2.  **FastAPI:** Framework de alto rendimiento para construir APIs web y renderizar plantillas de forma rápida e intuitiva.
3.  **Uvicorn:** Servidor ASGI rápido que ejecuta y sirve la aplicación FastAPI.
4.  **Jinja2:** Motor de plantillas de Python utilizado para renderizar dinámicamente las vistas del frontend.
5.  **Tailwind CSS (CDN):** Framework de CSS utilitario para el diseño de una interfaz moderna, limpia y responsive.
6.  **Pandas:** Librería de análisis de datos utilizada para la transformación, filtrado de texto y cálculos estadísticos en la etapa de analítica.
7.  **BeautifulSoup4 & Requests:** Librerías fundamentales para realizar las peticiones HTTP a los portales universitarios y parsear las páginas web.
8.  **openpyxl:** Generación y exportación de hojas de cálculo de Excel (`.xlsx`).
9.  **fpdf2:** Generación y diseño de reportes descargables en PDF.
10. **SQLite:** Motor de base de datos ligero que almacena los tres niveles del modelo Medallion de forma local en archivos independientes.

---

## 📥 Instrucciones de Instalación y Ejecución

Sigue estos pasos para configurar y correr el proyecto localmente:

### 1. Clonación del Repositorio e Inicialización del Entorno Virtual

Navega a la carpeta de tu proyecto y crea un entorno virtual de Python:

```bash
# Crear el entorno virtual en la carpeta .venv
python3 -m venv .venv

# Activar el entorno virtual en Linux/macOS
source .venv/bin/activate

# O activar en Windows (PowerShell)
# .venv\Scripts\Activate.ps1
```

### 2. Instalación de Dependencias

Con el entorno virtual activo, instala todas las librerías necesarias mediante `pip`:

```bash
pip install -r requirements.txt
```

### 3. Ejecución del Servidor de Desarrollo

Inicia la aplicación FastAPI utilizando Uvicorn. Tienes dos formas de hacerlo:

*   **Opción A (Recomendada):** Ejecutando directamente el script principal:
    ```bash
    python src/main.py
    ```

*   **Opción B:** Ejecutando Uvicorn desde la terminal:
    ```bash
    uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
    ```

Una vez ejecutado, puedes acceder a la aplicación en tu navegador web a través de la dirección:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

Para explorar la documentación interactiva de la API, dirígete a:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 📄 Licencia

Este proyecto está licenciado bajo la **Licencia Pública General de GNU v3.0 (GPL-3.0)** - una licencia de código abierto fuerte y no permisiva. Esto significa que cualquier software derivado de este crawler debe ser también de código abierto y distribuirse bajo la misma licencia. Para más detalles, consulta el archivo [LICENSE](file:///home/erick/PycharmProjects/crawler/LICENSE).
