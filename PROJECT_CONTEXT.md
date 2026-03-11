# PROJECT CONTEXT: Bastión Core - Leads Generation

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
*   **LLMs Soportados:** Llama 3 vía Groq (Primario por velocidad y costo), Google Gemini, OpenAI, Anthropic.
*   **Audio / STT:** Groq API ejecutando `whisper-large-v3`.
*   **Scraping:** `playwright` (Sincrónico/Asincrónico). `pandas` para estructuración de Tablas.
*   **Base de Datos Nativa:** `sqlite3` (Tablas maestras locales y colas de trabajo).
*   **Arquitectura Web (NUEVO):** FastAPI (Backend API Rest) + Next.js (Frontend Dashboard).

---

## 4. Roadmap y Estado Actual
*   **Logrado (Fase 1 - Extracción Básica):** Scraper Playwright al 100%. Módulos limpios. Bot soporta comandos de voz. Storage Service aísla la carga.
*   **Logrado (Fase 2 - Alertas y Herramientas LLM):**
    *   Integración de `APScheduler` para alertas asíncronas agnósticas.
    *   Creación de herramientas estables en LangGraph para listar y agendar tareas superando errores de schema y contexto (Fixes de Marzo 2026 aplicados).
*   **Fase 2.5 (Batch Scraper Queue System & Unificación de Búsquedas) [EN PROGRESO]:**
    *   Normalizar base de datos con tablas globales (`master_cities`) y por usuario (`tenant_categories`). (Realizado)
    *   Crear endpoints CRUD en FastAPI y almacenar intención en tabla `batch_jobs`. (Realizado)
    *   Resolver el fallo de concurrencia aislando Playwright en un "Worker de fondo" autónomo. (Worker Base Realizado)
    *   **Unificar Arquitectura:** Enrutar **todas** las búsquedas (Bot Telegram y Web) hacia la cola `batch_jobs` y delegar las notificaciones push al Worker (Término de refactorización pendiente bajo estricto TDD).
*   **Fase 3 (Admin Dashboard Web - FastAPI + Next.js) [EN PROGRESO]:**
    *   Levantar servidor API local en FastAPI. (Realizado)
    *   Construir aplicación SPA en Next.js para administrar diccionarios de datos y controlar manualmente la Cola del Scraper (Interruptor ON/OFF). (Autenticación implementada, pendiente CRUDs)
    *   Implementar autenticación Passwordless vía Telegram OTP JWT. (Realizado)
    *   Creación de script orquestador `start_dev.sh` para levantar Bot, API y Frontend simultáneamente. (Realizado)
*   **Fase 4 (Outreach Automatizado y CRM):**
    *   Integrar WAHA (WhatsApp HTTP API) vía Docker OrbStack.
    *   Crear Agente LangGraph capaz de redactar mensajes proactivos a los leads extraídos generados por el Worker.
    *   Enganchar HubSpot CRM para capturar Webhooks de WAHA.

---

## 5. Instrucciones para Agentes de IA (CRÍTICO)
**🚨 IMPORTANTE PARA CUALQUIER IA O AGENTE QUE LEA ESTE ARCHIVO 🚨**
Antes de proponer, modificar o generar CUALQUIER línea de código o script en este proyecto, **ESTÁS OBLIGADO a leer el archivo `.agentrules`** ubicado en la raíz del proyecto. Este archivo contiene las directrices de nivel "Developer Senior" (SOLID, Clean Architecture, prohibición de commits automáticos) que rigen este repositorio. Ignorar el archivo `.agentrules` es una violación a las reglas fundamentales de este proyecto.
