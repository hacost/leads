# Estrategia de Pruebas Automatizadas (QA & TDD) - Bastión Core

De acuerdo con las nuevas directivas de la arquitectura (fechadas en Marzo 2026), todo el desarrollo de **Bastión Core** se rige por **TDD (Test-Driven Development)**. No se autoriza escribir código de producción sin antes haber definido su prueba automatizada correspondiente.

El proyecto, al estar dividido en componentes asíncronos distribuidos, requiere un enfoque de pruebas multicapa:

## 1. Stack Tecnológico de Pruebas Obligatorio

*   **Backend (Python/FastAPI/Domain):** `pytest` + `pytest-asyncio` + `httpx` (para API).
*   **Mocks/Stubs (Python):** `unittest.mock` y `responses` (para llamadas externas como Groq/LLM).
*   **Frontend (Next.js/React):** `Jest` + `React Testing Library`.
*   **Scraping (Playwright):** Pruebas E2E nativas con `pytest-playwright`.

---

## 2. Estrategia por Componente Arquitectónico

### A) El Servidor API (`src/presentation/api/` y `src/application/`)
**Tipo de Pruebas:** Unitarias y de Integración.
**Cómo probarlo:**
1.  **Endpoints (Rutas FastAPI):** Usar `TestClient` de FastAPI (basado en `httpx`). Debe haber pruebas para los códigos `200 OK`, `401 Unauthorized` (fallo de JWT OTP), y `400 Bad Request` en todos los CRUDs.
2.  **Domain Models:** Pruebas unitarias directas sobre los modelos Pydantic para asegurar que las validaciones de datos (como la estructura de un `BatchJob`) fallen correctamente cuando reciben datos corruptos.

### B) Bot de Telegram (`src/presentation/telegram_bot/`)
**Tipo de Pruebas:** Unitarias con Mocks.
**Cómo probarlo:**
1.  **Aislamiento:** La API de Telegram NO se llama en las pruebas. Se debe "mockear" (simular) el objeto `Update` y `Context` que envía la librería `python-telegram-bot`.
2.  **Lógica de Comandos:** Comprobar que al inyectar un falso comando `/start` o `/buscar`, la función correspondiente reaccione enviando la cadena de texto esperada al mock del chat.

### C) Agente IA (LangGraph / `agent_service.py`)
**Tipo de Pruebas:** Unitarias Estocásticas (Evaluaciones).
**Cómo probarlo:**
1.  Las pruebas para LLMs son tramposas porque las respuestas varían. El enfoque aquí es: **Mockear la respuesta de la API de Groq** para pruebas de flujo rápido.
2.  Probar que el Grafo de LangGraph toma la **decisión de ruteo correcta**. Ejemplo: Si el mock del LLM devuelve "Requiere extraer mapas", la prueba debe validar que el nodo actual transicionó al nodo `google_maps_node`.

### D) Servicios Externos (Audio, Base de Datos SQLite)
**Tipo de Pruebas:** Integración Aislada.
**Cómo probarlo:**
1.  **`storage_service.py`:** Las pruebas NO deben tocar `leads.db` (producción). Deben usar una base de datos SQLite efímera en memoria (`sqlite:///:memory:`) que se instancie y se destruya con fixtures de `pytest` en cada prueba.
2.  **`audio_service.py`:** Proveer archivos `.ogg` de ejemplo hardcodeados en una carpeta `tests/fixtures/` e invocar el servicio (mockeando la subida a Whisper) para ver si retorna el string de texto correcto.

### E) Scrapers (`src/domain/engine/scrapers/`)
**Tipo de Pruebas:** E2E Sintéticas.
**Cómo probarlo:**
1.  No queremos banear nuestra IP consultando Google Maps en cada corrida de pruebas.
2.  **Solución:** Se debe levantar un micro-servidor de pruebas local (usando `http.server` de Python) que sirva un archivo HTML estático parecido a Google Maps o Facebook.
3.  El Scraper de Playwright navegará a `http://localhost:9999/dummy_map.html` y la prueba verificará si es capaz de extraer el nombre y el teléfono de esa página falsa.

### F) Cliente Frontend (Next.js)
**Tipo de Pruebas:** Unitarias (Componentes) e Integración Continua.
**Cómo probarlo:**
1.  **Estado (Zustand):** Instanciar copias frescas del Store en las pruebas para verificar que llamar a `login()` muta el estado a autenticado y `hasHydrated` cambia de valor.
2.  **Renderizado UI:** Usar React Testing Library para renderizar botones y formularios. Validar accesibilidad buscando elementos por "Rol" (`screen.getByRole('button', { name: /Send Code/i })`) y simulando clicks.

---

## 3. Ejemplo Práctico del Flujo TDD para el Próximo Paso (CRUD de Jobs)

Antes de hacer el endpoint `GET /api/jobs`, mi primera acción de código será crear el archivo `tests/api/test_jobs.py` con este flujo mental:

1.  **Red (Rojo):** Escribir `def test_get_jobs_returns_401_without_token():` y ejecutar pytest. Fallará porque ni el endpoint ni la seguridad existen aún.
2.  **Green (Verde):** Crear el endpoint en FastAPI con la dependencia de autenticación mínima y retornar la respuesta exigida. La prueba pasará.
3.  **Refactor:** Limpiar el código sucio si es que lo hay, sabiendo que la prueba en verde me cuida la espalda.
