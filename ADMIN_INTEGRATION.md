# Integración con el panel de la farmacia

El navegador se comunica con SFJPII-back, que valida sesión y rol `admin`/`super_admin` antes de llamar a `POST /admin/chat` con `{ "mensaje": "..." }`. El contrato de respuesta existente se mantiene: `respuesta`, `tools_utilizadas` y `grafica` opcional.

Configura `SFJPII_AI_SERVICE_KEY` en el entorno de este servicio y el mismo valor privado en SFJPII-back. El backend configura además `SFJPII_AI_URL` con la URL base de este servicio. Conserva las variables actuales de MongoDB y OpenAI. Reinicia ambos procesos tras cambiar su configuración.

Las rutas administrativas y de prueba requieren la cabecera `X-Service-Key`. Sin clave configurada devuelven 503; con clave ausente o incorrecta, 401. La clave es exclusiva de los servidores, nunca del frontend. Las herramientas de prueba también requieren esta cabecera para evitar exponer datos administrativos por otra ruta.

Para desarrollo local: `uvicorn main:app --host 127.0.0.1 --port 8000`. El backend puede usar `http://127.0.0.1:8000` cuando comparte equipo. Para producción configura la URL HTTPS correspondiente.

Ejecuta `python -m unittest test_admin_integration` para comprobar autorización, contrato y manejo de errores con un agente simulado, sin MongoDB ni consumo de IA.
