# Asistente para clientes

El frontend envía las consultas a `POST /api/cliente/chat` en `SFJPII-back`.
Ese backend valida el token y el rol, elimina cualquier identidad recibida en el
cuerpo y llama a `POST /cliente/chat` de este servicio con dos encabezados
privados: `X-Service-Key` y `X-User-Id`.

Las herramientas disponibles para información privada son:

- `consultar_mis_pedidos`: lista pedidos del usuario autenticado y admite
  filtros opcionales de estado y límite.
- `consultar_mi_pedido`: consulta un pedido mediante `_id` y `userId` en la
  misma operación. Un pedido inexistente o ajeno produce la misma respuesta.
- `consultar_mis_encargos`: lista encargos del usuario autenticado y admite
  filtros opcionales de estado y límite.

La herramienta pública `consultar_informacion_farmacia` lee en cada consulta
`data/informacion_farmacia.docx`. El archivo contiene teléfonos, WhatsApp,
dirección, horario regular y excepciones por fecha. Se puede editar con Word sin
cambiar código; basta guardar el archivo para que la siguiente consulta utilice
su contenido. En producción, `PHARMACY_INFO_DOCX` permite apuntar a una ruta
persistente o montada fuera del repositorio.

Ningún esquema de herramienta contiene `user_id`. `cliente_agent` recibe esa
identidad desde la ruta protegida y la inyecta al ejecutar la herramienta.
Las conversaciones también se consultan y guardan mediante la combinación de
`tipo_usuario`, `user_id` y `conversation_id`.
