# Leads Generation Scraper (Google Maps + Facebook) con Agente IA

Este proyecto es el núcleo operativo de **Bastión Core** enfocado a la **Generación de Leads B2B**. Es operado por una Inteligencia Artificial (basada en LangGraph y modelos como Gemini, Claude o ChatGPT). Funciona a través de una **interfaz de Chatbot en Telegram**, permitiéndote solicitar búsquedas de prospectos en lenguaje natural usando **texto o notas de voz** (ej. "Busca dentistas en Monterrey").

El Agente de IA interpreta tu petición, extrae las zonas y categorías, y automatiza la extracción de datos desde **Google Maps**. El enriquecimiento secundario de contactos en **Facebook** (Correos y WhatsApp/Teléfonos) es un proceso manual que puedes solicitarle al agente como un paso posterior.

---

## 🚀 Arquitectura "Clean" Basada en DDD (Domain-Driven Design)

El proyecto está estructurado estrictamente en 5 capas:

1. **`src/domain/`**: El núcleo absoluto. Contiene las entidades, interfaces y modelos de estado (Pydantic Models y Enums). Sin dependencias externas.
2. **`src/application/`**: Casos de uso de la aplicación, como la orquestación de Agentes de IA (`agent_service.py`), lógica de scraping puro y el motor del Scheduler asíncrono.
3. **`src/core/`**: Centraliza configuraciones técnicas genéricas (`config.py`) y reglas de negocio transversales globales conectadas al `.env`.
4. **`src/infrastructure/`**: Implementaciones técnicas (Adaptadores). Contiene la conexión a la base de datos local SQLite (`storage_service.py`), procesadores abstractos de mensajería externa y servicios de audio (`whisper`).
5. **`src/presentation/`**: Puertos de entrada/salida. Aquí viven las rutas de la API (`api/` con FastAPI), el adaptador del Bot de Telegram (`telegram_bot/`) y los workers programados.

---

## 🚀 Características Principales

*   **Notas de Voz (Whisper 3)**: Puedes enviarle audios al Bot de Telegram. Utiliza la API de Groq + Whisper-large-v3 para transcribir instantáneamente.
*   **Agente Inteligente (LangGraph)**: El "Cerebro" del sistema decide qué herramienta de scraping usar basado en tu petición, usando LLM de código abierto hiper-rápidos (Groq/Llama3).
*   **Google Maps Scraping Asíncrono**: Extrae negocios, direcciones, teléfonos y reseñas.
*   **Enriquecimiento con Facebook**: Busca teléfonos faltantes de prospectos navegando en Facebook y analizando posteos recientes.
*   **Aislamiento de Sesiones**: Los archivos generados no se cruzan entre usuarios de Telegram.
*   **Dashboard Web Integrado (FastAPI + Next.js)**: Acceso a un panel web con Login Passwordless (OTP vía Telegram) para administrar colas de trabajos y categorías, totalmente desacoplado del Bot.

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

Este proyecto requiere **`uv`**, el gestor de paquetes de Python de alta velocidad, y **`npm`** para el frontend.

1.  Instala `uv`: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2.  Sincroniza dependencias del backend: `uv sync`
3.  Instala Playwright: `uv run playwright install chromium`
4.  Instala dependencias del frontend: `cd frontend && npm install`
5.  **Entorno de Desarrollo Unificado:** 
    Ejecuta el script orquestador desde la raíz para levantar simultáneamente el Bot de Telegram, la API FastAPI y el Dashboard frontend Next.js:
    ```bash
    ./start_dev.sh
    ```
6.  **Uso:** 
    *   **Dashboard:** Ingresa a `http://localhost:3000` y loguéate usando tu ID de Telegram (recibirás un OTP vía Telegram).
    *   **Bot:** Busca tu Bot en Telegram y mándale un Audio o Texto para iniciar el scraping.
