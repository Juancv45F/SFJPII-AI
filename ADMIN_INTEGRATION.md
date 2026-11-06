# Integración con el panel de la farmacia

El panel recupera el listado con `GET /admin/conversations?offset=0` y los mensajes con `GET /admin/conversations/{conversation_id}`. Ambas rutas requieren `X-Service-Key` y `X-Admin-Id`, y filtran MongoDB por administrador. La conversación inexistente o ajena devuelve 404. El listado devuelve `items` y `has_more`, ordenado por actualización, con 30 elementos por página.

`DELETE /admin/conversations/{conversation_id}` elimina la conversación únicamente cuando pertenece al `X-Admin-Id` recibido. Devuelve 204 al eliminar y 404 si no se encontró dentro de ese administrador.

Cada turno completo se guarda en una sola actualización, incluyendo la gráfica de la respuesta. Los mensajes nuevos ya no se recortan a 12; ese límite solo se utiliza como contexto enviado al modelo. El historial descartado por versiones previas no es recuperable. Reinicia la IA y el backend para habilitar las rutas nuevas.

El navegador se comunica con SFJPII-back, que valida sesión y rol `admin`/`super_admin` antes de llamar a `POST /admin/chat` con `{ "mensaje": "..." }`. El contrato de respuesta existente se mantiene: `respuesta`, `tools_utilizadas` y `grafica` opcional.

Configura `SFJPII_AI_SERVICE_KEY` en el entorno de este servicio y el mismo valor privado en SFJPII-back. El backend configura además `SFJPII_AI_URL` con la URL base de este servicio. Conserva las variables actuales de MongoDB y configura el proveedor de IA con `AI_PROVIDER` y su clave (`DEEPSEEK_API_KEY`, `DASHSCOPE_API_KEY` u `OPENAI_API_KEY`). Reinicia ambos procesos tras cambiar su configuración.

Para comparar proveedores o modelos basta cambiar `AI_PROVIDER` y `AI_MODEL`. Al cambiar de proveedor, vacía o actualiza también `AI_MODEL` y `AI_BASE_URL`, porque un valor anterior sigue aplicándose. Este servicio usa Chat Completions con tools: en OpenAI funcionan `gpt-6-luna` (valor por defecto) y `gpt-6-sol`, siempre con `reasoning_effort` en `none`, que es lo que se envía. `gpt-6-astra`, `gpt-6.1-sol` y `gpt-6.1-terra` exigen la Responses API para tools y no son compatibles. `AI_REASONING_EFFORT=off` omite el parámetro para modelos que no lo aceptan.

Las rutas administrativas y de prueba requieren la cabecera `X-Service-Key`. Sin clave configurada devuelven 503; con clave ausente o incorrecta, 401. La clave es exclusiva de los servidores, nunca del frontend. Las herramientas de prueba también requieren esta cabecera para evitar exponer datos administrativos por otra ruta.

Para desarrollo local: `uvicorn main:app --host 127.0.0.1 --port 8000`. El backend puede usar `http://127.0.0.1:8000` cuando comparte equipo. Para producción configura la URL HTTPS correspondiente.

Ejecuta `python -m unittest test_admin_integration` para comprobar autorización, contrato y manejo de errores con un agente simulado, sin MongoDB ni consumo de IA.

## Consultas administrativas avanzadas

El asistente dispone de herramientas para:

- Priorizar reabastecimiento cruzando stock actual, unidades vendidas e ingresos. Los productos exclusivos por encargo quedan fuera porque mantienen stock cero por diseño.
- Consultar productos líderes por unidades o por ingresos, incluyendo stock actual, categoría actual y existencia en el catálogo.
- Calcular ingresos totales, por categoría y por día, además de comparar dos periodos.
- Resumir pedidos por estado, completados, cancelados, ingresos y ticket promedio, y consultar su evolución diaria.
- Resumir encargos por estado y tipo de entrega, separados de los pedidos de compra inmediata.
- Crear gráficas de barras o dona para los resultados anteriores con el contrato existente de `grafica`.

Los ingresos consideran únicamente pedidos `pagado`, `en_camino` y `entregado`. Los pendientes y cancelados se incluyen en métricas operativas, pero no como ventas realizadas. La agrupación diaria usa `America/Mexico_City`. Como los pedidos históricos no guardan una copia de la categoría, los artículos cuyo producto fue eliminado se agrupan como `Fuera del catálogo / sin categoría`.

Todas las consultas de inventario físico excluyen `solo_encargo`: stock bajo, resumen de inventario, baja rotación, oportunidades de oferta y prioridades de reabastecimiento. Las fechas se normalizan a UTC y todos los periodos y límites utilizan los validadores comunes de `tools/validators.py`. Los estados que generan ingresos, el filtro de inventario y la zona horaria están centralizados en `tools/constants.py`.

Cada gráfica incluye `unidad`: `MXN`, `unidades`, `pedidos`, `productos` o `encargos`. El campo es obligatorio para respuestas nuevas; el frontend admite historiales anteriores sin unidad.

Al iniciar el servicio, y antes de guardar un turno si aún no se han creado en esa instancia, se crean índices para propietario/conversación (único), historial por propietario/fecha e índice TTL. Un fallo al crearlos se registra como `conversation_indexes_failed` y no impide el arranque. `CHAT_RETENTION_DAYS` controla la vigencia desde la última actividad (180 días por defecto y 0 para no añadir vencimiento a los chats nuevos). La retención se aplica o renueva cuando se guarda un turno; los documentos antiguos sin `expiresAt` no se eliminan automáticamente hasta que vuelvan a actualizarse. Los logs de la IA usan JSON y omiten mensajes, respuestas y credenciales. Los errores distinguen validación, límite de API, timeout, conexión y MongoDB sin exponer detalles internos.

Ejecuta `python -m unittest discover -p "test*.py"` para validar herramientas, gráficas, seguridad, persistencia y el escenario conversacional encadenado. Las pruebas no llaman al modelo. Las agregaciones también fueron verificadas directamente contra las colecciones configuradas, sin mostrar datos sensibles.

## Despliegue en Vercel

Vercel detecta la app `app` de `main.py` y la ejecuta como una sola función. `vercel.json` fija `maxDuration` en 300 s, el máximo de Hobby. Pro y Enterprise admiten hasta 800 s. `AI_REQUEST_TIMEOUT_SECONDS` y `AI_TURN_TIMEOUT_SECONDS` mantienen el turno por debajo de ese límite y devuelven 504 en lugar de un corte de la plataforma; si subes uno, revisa los demás. El timeout de `SFJPII-back` hacia este servicio debe ser igual o mayor.

Configura las variables en el proyecto de Vercel y vuelve a desplegar tras cambiarlas: no se aplican a despliegues existentes. El archivo `.env` no se sube (`.vercelignore`).

El sistema de archivos es de solo lectura salvo `/tmp`, que es efímero. Este servicio no escribe en disco. Para cambiar `data/informacion_farmacia.docx` hay que hacer commit y desplegar de nuevo; guardarlo en el servidor no es posible. `actualizado_en` refleja la fecha del archivo en el despliegue, no necesariamente la última edición.

MongoDB Atlas debe aceptar conexiones desde las IP de Vercel, que son dinámicas salvo con Static IPs. Conviene elegir la región de la función más cercana al clúster.
