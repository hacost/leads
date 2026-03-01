# PROJECT CONTEXT: Bastión Core - Leads Generation Platform

## 1. Visión Holística del Proyecto
Este repositorio forma parte de **Bastión Core**, una startup tecnológica de México enfocada en otorgar créditos/servicios B2B al sector Micro (Ferreterías, Plomeros, Abarrotes, HORECA, etc.). 

**Propósito Específico de esta carpeta (`leads-generation`):**
Es un sistema automatizado inteligente ("Agente Elite B2B") operado 100% por Telegram (texto y voz). Extrae datos de negocios locales en Google Maps y los segmenta para descubrir negocios "Micro" altamente calificados que no tienen una presencia web masiva, listos para campañas de prospección en frío (Outreach).

---

## 2. Decisiones Arquitectónicas Restrictivas (Inquebrantables)
Cualquier Ingeniero / Agente IA que toque este código **debe** apegarse a las siguientes reglas (Establecidas en Febrero 2026):

1. **Clean Architecture Ligera:** 
   El código está estrictamente dividido en `core/` (permisos y config), `services/` (lógica re-utilizable, AI y Storage), `scrapers/` (Playwright puro) y `interfaces/` (el bot de frontend). No se permiten "God Objects" ni monolitos.
2. **Archivos como Salida Principal:**
   El producto final hacia el usuario son **Archivos Excel (`.xlsx`)**, generados explícitamente y enviados. 
3. **Gestión de Sesiones (Aislamiento):**
   Múltiples administradores pueden usar Telegram al mismo tiempo. Nunca se escriben archivos "sueltos". Todo se guarda vía `storage_service.py` en carpetas como `leads/session_[ID]/`. 
4. **Limpieza Rigurosa:**
   Tras enviar los archivos al usuario vía Telegram, u ocurrir cualquier error, la función `eliminar_sesion()` desecha los Exceles. Nunca se deben reciclar datos "fantasmas" viejos de pasadas búsquedas.
5. **No Clases Innecesarias en Servicios:**
   Python funcional es prioridad. Omitir la creación de objetos `class Módulo()` a menos que haya manejo de *State* explícito (Ej. Los Scrapers en Playwright). Los servicios como Telegram o Audio transcribirse usan funciones como ciudadanos de primera clase. 

---

## 3. Tech Stack Autorizado
*   **Gestor (Package Manager):** `uv` (Líder en velocidad, se prohíbe usar `pip` puro o `requirements.txt`).
*   **Agentic Framework:** `langgraph` + `langchain`.
*   **LLMs Soportados:** Google Gemini (Primario), OpenAI, Anthropic.
*   **Audio / STT:** Groq API ejecutando `whisper-large-v3`.
*   **Scraping:** `playwright` (Sincrónico/Asincrónico). `pandas` para estructuración de Tablas.
*   **Base de Datos Nativa:** `sqlite3` (Solo usado para caché histórica de extracción, no es la "fuente de verdad" del CRM del cliente).

---

## 4. Estado Actual (Phase 2 In-Progress)
*   **Logrado (Fase 1):** Scraper Playwright al 100%. Módulos limpios. Bot soporta comandos de voz. Storage Service aísla la carga.
*   **Aprobado (Fase 2 - Outreach):**
    *   Iniciar integración con WAHA (WhatsApp HTTP API) vía Docker OrbStack.
    *   Crear Agente LangGraph capaz de redactar mensajes a los "Micros" extraídos (Outreach Agent).
    *   Enganchar HubSpot CRM para capturar automáticamente Webhooks de WAHA (Sync Agent).
*   **Aprobado (Fase 3 - Alexa Domótica):**
    *   Crear `src/interfaces/alexa_api.py` (FastAPI) para recibir Webhooks HTTPS de Amazon.
    *   Exponer puerto local con Ngrok/Cloudflare Tunnels.
    *   Enrutar voz a `procesar_mensaje_agente()` para lanzar scrapings con comandos de voz de Alexa.
