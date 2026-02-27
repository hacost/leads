# Leads Generation Scraper (Google Maps + Facebook) con Agente IA

Este proyecto es un sistema avanzado de **Generación de Leads B2B** operado por una Inteligencia Artificial (basada en LangGraph y modelos como Gemini, Claude o ChatGPT). Funciona a través de una **interfaz de Chatbot en Telegram**, permitiéndote solicitar búsquedas de prospectos en lenguaje natural (ej. "Busca dentistas en Monterrey").

El Agente de IA interpreta tu petición, extrae las zonas y categorías, y automatiza la extracción de datos desde **Google Maps**. El enriquecimiento de contactos en **Facebook** (Correos y WhatsApp/Teléfonos) es un proceso que puedes solicitarle al agente como un paso posterior.

## 🚀 Características Principales

*   **Interfaz conversacional (Telegram)**: Pídele a tu asistente virtual los leads que necesitas como si hablaras con un humano. El Agente responde en tiempo real y te envía los archivos Excel directamente por chat.
*   **Agente Inteligente (LangGraph)**: El "Cerebro" del sistema decide qué herramienta de scraping utilizar basado en tu petición (Google Maps por defecto, o Facebook si se lo especificas). 
*   **Google Maps Scraping**: Extrae nombres, direcciones, teléfonos, sitios web, calificaciones y cantidad exacta de reseñas comerciales.
*   **Enriquecimiento con Facebook**: Una segunda herramienta que busca en Facebook para recuperar teléfonos o correos faltantes de tus prospectos extraídos. Analiza perfiles y hasta los últimos 3 posts buscando números o enlaces `wa.me`.
*   **Inteligencia y Caché (SQLite)**: Una base de datos local (`leads.db`) guarda los prospectos ya extraídos. Al buscar nuevamente, reutiliza los datos existentes de búsquedas exactas para ahorrar tiempo y llamadas a la API.
*   **Segmentación Automática**: Clasifica y separa automáticamente a los leads válidos en diferentes archivos de Excel basados en configuraciones predefinidas.

## 📂 Archivos de Salida (Entregados vía Telegram)

El bot te enviará automáticamente los siguientes archivos Excel generados:

1.  `leads_corporate.xlsx`: Negocios con muchas reseñas o cadenas grandes.
2.  `leads_micro.xlsx`: Negocios pequeños o nuevos con pocas reseñas pero buena calificación o métricas aceptables.
3.  `leads_google_maps.xlsx`: La lista maestra de TODOS los leads extraídos con un teléfono válido a 10 dígitos.
4.  `leads_pending_lookup.xlsx`: Leads extraídos pero *sin* teléfono válido. Éstos pueden ser reprocesados por la herramienta de Facebook.

## ⚙️ Configuración

### 1. Variables de Entorno (`.env`)
Debes crear un archivo `.env` en la raíz del proyecto para conectar las APIs y el Bot:

```env
# Configuración del LLM
LLM_MODEL=gemini # Opciones: gemini, claude, gpt
GOOGLE_API_KEY=tu_api_key_de_gemini
# ANTHROPIC_API_KEY=... (si usas Claude)
# OPENAI_API_KEY=... (si usas ChatGPT)

# Configuración de Telegram
TELEGRAM_BOT_TOKEN=el_token_de_tu_bot_proveído_por_BotFather
ALLOWED_CHAT_IDS=123456789,987654321 # Lista blanca de usuarios permitidos

# Personalización del Agente
AGENT_NAME="Agente Elite B2B"
USER_TITLE="CEO"
```

### 2. Reglas del Scraping (`config.json`)
Puedes personalizar las reglas de segmentación sin tocar código Python. Modifica el archivo `config.json` en la raíz:

```json
{
  "segmentation": {
    "micro_max_reviews": 20,
    "good_rating_threshold": 3.5
  },
  "search": {
    "max_scroll_attempts": 5,
    "wait_between_actions_ms": 3000,
    "headless": false
  }
}
```

*   `micro_max_reviews`: Negocios con estas reseñas o menos se clasifican como "Micro".
*   `headless`: Si es `true`, los navegadores (Playwright) se ejecutarán en segundo plano sin abrir ventanas visibles.

## 🛠 Instalación y Uso

Este proyecto requiere **`uv`**, el gestor de paquetes de Python de alta velocidad.

1.  Asegúrate de tener `uv` instalado en tu sistema.
2.  Sincroniza todas las dependencias del proyecto (`pyproject.toml`) automáticamente:
    ```bash
    uv sync
    ```
3.  Instala el navegador requerido para Playwright (los scrapers):
    ```bash
    uv run playwright install chromium
    ```
4.  **Inicia el Asistente Bot**:
    Asegúrate de haber configurado tu archivo `.env` correctamente y ejecuta el servidor principal:
    ```bash
    uv run main.py
    ```
5.  **Utiliza el Sistema**: Busca tu Bot en Telegram, presiona `/start` o envíale un mensaje en lenguaje natural. ¡A disfrutar!
