# Leads Generation Scraper (Google Maps + Facebook) con Agente IA

Este proyecto es el núcleo operativo de **Bastión Core** enfocado a la **Generación de Leads B2B**. Es operado por una Inteligencia Artificial (basada en LangGraph y modelos como Gemini, Claude o ChatGPT). Funciona a través de una **interfaz de Chatbot en Telegram**, permitiéndote solicitar búsquedas de prospectos en lenguaje natural usando **texto o notas de voz** (ej. "Busca dentistas en Monterrey").

El Agente de IA interpreta tu petición, extrae las zonas y categorías, y automatiza la extracción de datos desde **Google Maps**. El enriquecimiento secundario de contactos en **Facebook** (Correos y WhatsApp/Teléfonos) es un proceso manual que puedes solicitarle al agente como un paso posterior.

---

## 🚀 Arquitectura "Clean" (Capa por Capa)

A partir de Febrero 2026, el proyecto fue refactorizado siguiendo los principios de Clean Architecture y SOLID:

1. **`src/core/`**: Centraliza configuraciones (`config.py`) leyendo el `.env` una sola vez, y maneja la Lista Blanca de seguridad (`security.py`).
2. **`src/services/`**: Módulos independientes y "stateless" (sin memoria) que ejecutan tareas:
   * `audio_service.py`: Recibe `.ogg` y devuelve texto vía Whisper.
   * `storage_service.py`: Capa de abstracción para guardar y leer archivos Excel/Sistema.
   * `agent_service.py`: Ensambla y ejecuta el Grafo de IA de LangGraph.
3. **`src/interfaces/`**: Adaptadores hacia el mundo exterior. 
   * `telegram_bot.py`: Escucha mensajes de Telegram (texto/audio) y usa los `services` para responder.
4. **`src/scrapers/`**: Herramientas pesadas bajo demanda. Clases stateful (`scraper.py`) conectadas a Playwright.

---

## 🚀 Características Principales

*   **Notas de Voz (Whisper 3)**: Puedes enviarle audios al Bot de Telegram. Utiliza la API de Groq + Whisper-large-v3 para transcribir instantáneamente lo que pides.
*   **Agente Inteligente (LangGraph)**: El "Cerebro" del sistema decide qué herramienta de scraping utilizar basado en tu petición usando Python ReAct agents.
*   **Google Maps Scraping**: Extrae nombres, direcciones, teléfonos, sitios web, calificaciones y cantidad exacta de reseñas comerciales.
*   **Enriquecimiento con Facebook**: Una segunda herramienta que busca en Facebook para recuperar teléfonos o correos faltantes de tus prospectos extraídos. Analiza perfiles y hasta los últimos 3 posts buscando números o enlaces `wa.me`.
*   **Aislamiento de Sesiones**: Los archivos generados no se cruzan entre usuarios de Telegram. Si falla una búsqueda, la carpeta de sesión se limpia sola para no mandar "archivos fantasma".
*   **Inteligencia y Caché (SQLite)**: Una base de datos local (`leads.db`) guarda los prospectos ya extraídos. Al buscar nuevamente, reutiliza los datos existentes de búsquedas exactas para ahorrar tiempo.
*   **Segmentación Automática**: Clasifica y separa automáticamente a los leads válidos en diferentes archivos de Excel (Micro vs Corporate).

---

## 📂 Archivos de Salida (Entregados vía Telegram)

1.  `leads_corporate.xlsx`: Negocios con muchas reseñas o cadenas grandes.
2.  `leads_micro.xlsx`: Negocios pequeños o nuevos con pocas reseñas; estos son el "Target B2B" principal de esta herramienta.
3.  `leads_google_maps.xlsx`: La La lista maestra de TODOS los leads extraídos con un teléfono válido a 10 dígitos.
4.  `leads_pending_lookup.xlsx`: Leads extraídos pero *sin* teléfono válido. Éstos pueden ser reprocesados por la herramienta de Facebook.

---

## ⚙️ Configuración (.env)

Debes crear un archivo `.env` en la raíz del proyecto para conectar las APIs y el Bot:

```env
# Configuración del LLM
LLM_MODEL=gemini # Opciones: gemini, claude, gpt
GOOGLE_API_KEY=tu_api_key_de_gemini
GROQ_API_KEY=tu_api_key_de_groq_para_audios
# ANTHROPIC_API_KEY=... (si usas Claude)
# OPENAI_API_KEY=... (si usas ChatGPT)

# Configuración de Telegram
TELEGRAM_BOT_TOKEN=el_token_de_tu_bot_proveído_por_BotFather
ALLOWED_CHAT_IDS=123456789,987654321 # Lista blanca

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

1.  Instala `uv`: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2.  Sincroniza dependencias: `uv sync`
3.  Instala Playwright: `uv run playwright install chromium`
4.  Levanta el Bot: `uv run main.py`
5.  **Utiliza el Sistema**: Busca tu Bot en Telegram y mándale un Audio o Texto.
