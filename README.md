# ARCA Med — Backend

## Sobre el proyecto

ARCA Med es un sistema de pre-consulta asistida por inteligencia artificial, compuesto por una aplicación Android (paciente) y una plataforma web (médico y administrador), diseñado específicamente para el ámbito de kinesiología y traumatología.

El sistema permite al paciente, antes de su consulta presencial:
- Registrar sus síntomas y antecedentes relevantes.
- Subir documentos médicos previos.
- Capturar su rango de movimiento articular mediante la cámara del celular.

A partir de esta información, ARCA Med genera automáticamente un resumen clínico y un prediagnóstico sugerido mediante RAG (Retrieval-Augmented Generation) sobre guías clínicas, que posteriormente es revisado por el profesional de salud desde un dashboard de triage antes de la atención presencial.

El objetivo es **apoyar y enriquecer** la consulta, entregando al profesional información estructurada y antecedentes recopilados previamente — nunca reemplazar su criterio clínico (el sistema es un CDSS: sugiere, no diagnostica).

### Plataformas

No es un sistema omnicanal (cada plataforma no ofrece lo mismo) — las funciones están repartidas según el rol:

- **App (Android)** — exclusiva para el **paciente**: registro/login, carga de síntomas y documentos, captura de rango de movimiento por cámara, catálogo de ejercicios y sus próximas citas.
- **Web** — exclusiva para **médico** y **administrador**: el médico ve el dashboard de triage, los resúmenes/prediagnósticos, los síntomas y documentos del paciente y su calendario de citas; el administrador gestiona usuarios, guías clínicas, el catálogo de ejercicios y registra las citas (ver [Citas](#citas)).

## Cómo levantar el proyecto

Requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/) abierto y corriendo.

### 1. Clonar y crear el `.env`

```bash
git clone <URL_DEL_REPO>
cd arca-med-backend
```

Crea un archivo `.env` dentro de `app/` (no viene en el repo) con:
```
DATABASE_URL=postgresql://arca:arca123@localhost:5432/arcamed
SECRET_KEY=cualquier-texto
OPENAI_API_KEY=sk-...
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ENCRYPTION_KEY=...
```

> `OPENAI_API_KEY` es una credencial real que cuesta dinero: pídela por un canal privado del equipo. **Nunca** la subas al repo ni la pegues en este README.

`ENCRYPTION_KEY` es la clave con que se cifran los datos clínicos en la base (ver [Seguridad de los datos](#seguridad-de-los-datos)). Debe ser de 32 bytes codificados en base64. Para generar una (con cualquier Python, o pídela al equipo):
```bash
python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
```
Sin esta variable el backend no arranca. Igual que `OPENAI_API_KEY`, **nunca** se sube al repo. Si se pierde, los datos cifrados con ella no se pueden recuperar (en local basta con recrear la base).

`CORS_ORIGINS` indica desde qué direcciones puede llamar la web a la API (separadas por coma, sin espacios). Si la web corre en otro puerto, agrégalo aquí. La app Android no necesita esta configuración.

### 2. Levantar todo con Docker (recomendado)

Desde la raíz del proyecto (`arca-med-backend/`):

```bash
docker compose up -d --build
```

Esto levanta dos contenedores: `db` (PostgreSQL + pgvector, con los datos iniciales) y `api` (el backend). La primera vez tarda un par de minutos. No hace falta instalar Python.

Solo la primera vez (o después de recrear la base), genera los embeddings de las guías clínicas:
```bash
docker compose exec api python generar_embeddings_guias.py
```

- API corriendo en: `http://localhost:8000`
- Documentación interactiva (probar todo desde el navegador): `http://localhost:8000/docs`

Dentro de Docker la API se conecta a la base por el nombre del servicio (`db`), no por `localhost`: el `docker-compose.yml` reemplaza `DATABASE_URL` automáticamente, así que el `.env` no se toca.

**Comandos útiles:**

| Comando | Para qué |
|---|---|
| `docker compose ps` | Ver si los contenedores están corriendo (`db` debe estar `healthy`) |
| `docker compose logs api` | Ver los logs o errores del backend (`-f` para seguirlos en vivo) |
| `docker compose up -d --build` | Aplicar cambios de código (hay que hacer `git pull` primero si los cambios son de otro) |
| `docker compose stop` | Apagar todo sin borrar datos |
| `docker compose down -v` | Borrar todo, **incluida la base** (ver [Datos iniciales](#datos-iniciales)) |

### Alternativa: correr el backend sin Docker (para desarrollo)

Útil para desarrollar el backend, porque `--reload` aplica los cambios al guardar. Requiere Python 3.11+. La base sigue en Docker:

```bash
docker compose up -d db      # solo la base
docker compose stop api      # si la API de Docker está corriendo, libera el puerto 8000

cd app
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

python generar_embeddings_guias.py   # solo la primera vez
uvicorn main:app --reload
```

## Cómo integrar la autenticación (Web / App)

La mayoría de los endpoints requieren estar logueado. El flujo general, sin importar la plataforma:

1. Llamar a `POST /auth/registro` o `POST /auth/inicio-sesion` → la API devuelve `{ "access_token": "...", "rol": "..." }`.
2. Guardar ese `access_token` localmente (no se pierde al cerrar la app/pestaña si se guarda bien).
3. En **cada** petición a un endpoint protegido, agregar el header:
   ```
   Authorization: Bearer <access_token>
   ```

### Web (React)

Guardar el token después del login (ej. en `localStorage`):
```js
const res = await fetch("http://localhost:8000/auth/inicio-sesion", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password }),
});
const data = await res.json();
localStorage.setItem("token", data.access_token);
```

Usarlo en peticiones posteriores:
```js
const token = localStorage.getItem("token");

const res = await fetch("http://localhost:8000/perfil", {
  headers: { Authorization: `Bearer ${token}` },
});
```

### App (Android / Kotlin con Retrofit)

Definir el header en la interfaz de Retrofit:
```kotlin
interface ApiService {
    @POST("auth/inicio-sesion")
    suspend fun login(@Body datos: LoginRequest): TokenResponse

    @GET("perfil")
    suspend fun getMe(@Header("Authorization") token: String): UsuarioResponse
}
```

Al llamar, el token se pasa con el prefijo `"Bearer "`:
```kotlin
val response = apiService.getMe("Bearer $accessToken")
```

Guardar el token entre sesiones con `DataStore` o `SharedPreferences` (evitar guardarlo en una variable en memoria simple, se perdería al cerrar la app).

### Subir un archivo (`/documentos`)

Este endpoint espera `multipart/form-data`, no JSON — la forma de mandarlo cambia un poco:

**Web (React):**
```js
const formData = new FormData();
formData.append("archivo", archivoSeleccionado);

const res = await fetch("http://localhost:8000/documentos", {
  method: "POST",
  headers: { Authorization: `Bearer ${token}` }, // NO poner Content-Type aquí, el navegador lo arma solo
  body: formData,
});
```

**App (Kotlin con Retrofit):**
```kotlin
@Multipart
@POST("documentos")
suspend fun subirDocumento(
    @Header("Authorization") token: String,
    @Part archivo: MultipartBody.Part
): DocumentoResponse
```

### Ver un documento del paciente (web del médico)

Los documentos médicos no son públicos: el endpoint exige token de médico. Por eso **no** sirve un `<a href="...">` normal (el navegador no manda el header `Authorization` al seguir un link). Hay que pedir el archivo con `fetch` y abrirlo así:

```js
const res = await fetch(
  `http://localhost:8000/pacientes/${pacienteId}/documentos/${docId}/archivo`,
  { headers: { Authorization: `Bearer ${token}` } }
);
const blob = await res.blob();
window.open(URL.createObjectURL(blob), "_blank");
```

### Mostrar imágenes de ejercicios

`imagen_url` es una ruta relativa (ej. `/static/ejercicios/abc.png`). Para mostrarla, anteponer la dirección del servidor: `http://localhost:8000` + `imagen_url`. Estas imágenes son públicas y no requieren token.

### Códigos de error

- `401 Unauthorized` → no se mandó token, es inválido, expiró, o la cuenta fue desactivada → hay que loguear de nuevo.
- `403 Forbidden` → el token es válido, pero el rol del usuario no tiene permiso para ese endpoint (ej. un paciente llamando a un endpoint de médico). En el login, también indica que la cuenta está desactivada.
- `400 Bad Request` → la petición no se puede cumplir por una regla del negocio (ej. una cita en una fecha pasada o una cita ya cancelada que se intenta modificar). El mensaje explica el motivo.
- `404 Not Found` → el recurso no existe (paciente, médico, documento, ejercicio, usuario, cita).
- `409 Conflict` → el médico ya tiene una cita en ese horario.
- `422 Unprocessable Entity` → el body no cumple las reglas (campo faltante, contraseña corta, articulación inválida, fecha sin zona horaria, etc.). La respuesta trae el detalle del error.

## Endpoints disponibles

### Autenticación (público)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/registro` | Crea una cuenta de **paciente** (el rol no se elige). Body: `{nombre, email, password}`. Devuelve `{access_token, rol}` |
| POST | `/auth/inicio-sesion` | Inicia sesión. Body: `{email, password}`. Devuelve `{access_token, rol}` |
| GET | `/perfil` | Cualquier usuario logueado. Devuelve los datos del dueño del token |

### Paciente (App)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/sintomas` | Registra un síntoma. Body: `{descripcion}`. Devuelve `{id, descripcion}` al instante. El prediagnóstico con IA se genera en segundo plano y aparece en la bandeja del médico unos segundos después (el paciente no lo ve) |
| POST | `/documentos` | Sube un documento (PDF/JPG/PNG, máx 10MB). Body: `multipart/form-data` con el archivo en el campo `archivo`. Devuelve `{id, nombre_archivo, tipo_archivo, subido_en}`. El archivo se guarda cifrado en la base de datos |
| POST | `/metricas` | Registra una métrica de rango de movimiento. Body: `{articulacion, lado, angulo_maximo, angulo_minimo}` (ver reglas de articulaciones abajo). Devuelve `{id, articulacion, lado, angulo_maximo, angulo_minimo}` |
| GET | `/ejercicios` | Lista el catálogo (también disponible para médico y admin). Filtro opcional: `?articulacion=rodilla`. Devuelve `[{id, nombre_ejercicio, descripcion, articulacion, imagen_url}]` |
| POST | `/ejercicios/{id}/ejecucion` | Registra que el paciente realizó el ejercicio. Body: `{correcto, comentario}` (comentario opcional). Devuelve `{id, ejercicio_id, correcto, comentario}` |
| GET | `/mis-citas` | Citas del paciente logueado, de la más próxima a la más lejana. Por defecto solo las próximas; `?solo_proximas=false` incluye también las pasadas (ver sección [Citas](#citas)) |

### Médico (Web)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/pacientes` | Lista los pacientes activos, ordenados por nombre. Búsqueda opcional: `?nombre=juan`. Devuelve `[{id, nombre, email}]` |
| GET | `/pacientes/triage` | Pacientes con prediagnóstico pendiente de revisión, ordenados por urgencia (alta → media → baja) |
| GET | `/pacientes/{id}/resumen` | Resumen generado por IA: resumen, diagnósticos diferenciales con probabilidad, urgencia sugerida y métricas físicas |
| POST | `/pacientes/{id}/resumen/revisar` | Marca el prediagnóstico como revisado (sale de la bandeja de triage). Body: `{revisado_por_medico: true}` |
| GET | `/pacientes/{id}/sintomas` | Síntomas escritos por el paciente, texto original, del más reciente al más antiguo: `[{id, descripcion, creado_en}]` |
| GET | `/pacientes/{id}/documentos` | Documentos subidos por el paciente: `[{id, nombre_archivo, tipo_archivo, subido_en}]` |
| GET | `/pacientes/{id}/documentos/{doc_id}/archivo` | Devuelve el archivo (PDF/imagen) para verlo o descargarlo (ver ejemplo arriba) |
| GET | `/guias-clinicas` | Lista las guías clínicas que usa la IA (también disponible para admin): `[{id, titulo, contenido, creado_en}]` |
| GET | `/citas` | Citas **del médico logueado**, para el calendario. Filtros opcionales: `?desde=`, `?hasta=`, `?paciente_id=`, `?estado=` (ver sección [Citas](#citas)) |

### Administrador (Web)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/admin/usuarios` | Lista usuarios. Filtro opcional: `?rol=medico`. Devuelve `[{id, nombre, email, rol, activo}]` |
| GET | `/admin/usuarios/{id}` | Devuelve un usuario |
| POST | `/admin/usuarios` | Crea un usuario de cualquier rol. Body: `{nombre, email, password, rol}`. Devuelve `{id, nombre, email, rol, activo}` |
| PATCH | `/admin/usuarios/{id}` | Edita un usuario. Se envían **solo** los campos a cambiar: `{nombre, email, password, rol, activo}`. Para desactivar: `{"activo": false}` |
| POST | `/guias-clinicas` | Carga una guía clínica (genera su embedding automáticamente). Body: `{titulo, contenido}`. Devuelve `{id, titulo}` |
| POST | `/ejercicios` | Crea un ejercicio del catálogo. Body: `{nombre_ejercicio, descripcion, articulacion}`. Devuelve el ejercicio creado |
| POST | `/ejercicios/{id}/imagen` | Sube o reemplaza la imagen del ejercicio (JPG/PNG, `multipart/form-data`, campo `archivo`). Devuelve el ejercicio con `imagen_url` |
| GET | `/citas` | Todas las citas. Mismos filtros que el médico, más `?medico_id=` |
| POST | `/citas` | Registra una cita. Body: `{paciente_id, medico_id, fecha_hora, duracion_minutos, motivo}` (`duracion_minutos` y `motivo` opcionales) |
| PATCH | `/citas/{id}` | Reprograma, cancela o completa una cita. Se envían **solo** los campos a cambiar: `{fecha_hora, duracion_minutos, motivo, estado}` |

### Auditoría (Administrador)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/auditoria/logs` | Lista los registros de auditoría, del más reciente al más antiguo. Filtros opcionales: `?usuario_id=`, `?usuario_afectado_id=`, `?accion=`, `?limite=` (100 por defecto, máx. 500). Devuelve `[{id, usuario_id, rol, accion, usuario_afectado_id, detalle, ip, fecha}]` |
| GET | `/auditoria/verificar` | Recalcula la cadena de hash y confirma que ningún registro fue alterado. Devuelve `{integra, total_revisados, id_con_error, motivo}` |

**Qué se registra:** cada vez que un médico accede a datos de un paciente (`ver_pacientes`, `ver_triage`, `ver_resumen`, `revisar_prediagnostico`, `ver_sintomas`, `ver_documentos`, `descargar_documento`) y cada acción de un admin (`crear_usuario`, `editar_usuario`, `crear_guia`, `crear_ejercicio`, `subir_imagen_ejercicio`, `crear_cita`, `editar_cita`). También se registra cuando el médico consulta su calendario (`ver_citas`). Al editar un usuario se guardan solo los nombres de los campos cambiados, nunca sus valores (por ejemplo, nunca la contraseña).

**Cómo se protege:** los registros no se pueden modificar ni borrar (triggers en la base de datos). Además, cada registro guarda el hash SHA-256 del anterior, formando una cadena: si alguien altera un registro directamente en la base, `/auditoria/verificar` lo detecta e indica cuál.

## Citas

ARCA Med **no es un sistema de reserva de horas**. En un entorno real, el paciente reserva su hora en el sistema del centro médico, y ese sistema le informa la cita a ARCA Med. ARCA Med usa la cita como contexto de la pre-consulta:

- **Paciente (App):** ve su próxima cita y sabe hasta cuándo tiene para enviar síntomas, documentos y mediciones.
- **Médico (Web):** ve sus citas en un calendario y, desde cada una, puede abrir el resumen del paciente.

En este MVP no existe ese sistema externo, así que lo **simula el administrador**: las citas se registran con `POST /citas`. Además, la base trae **citas de prueba** (`init/05_citas.sql`) calculadas desde el día en que se levanta la base, para que el calendario siempre tenga citas próximas. La integración con el sistema de agenda real del centro médico queda como mejora futura.

### Formato de una cita

Todos los endpoints de citas devuelven el mismo formato:

```json
{
  "id": 1,
  "paciente_id": 6,
  "paciente_nombre": "Juan Pérez",
  "medico_id": 3,
  "medico_nombre": "Camila Rojas",
  "fecha_hora": "2026-11-10T12:00:00Z",
  "duracion_minutos": 30,
  "motivo": "Dolor de rodilla derecha al subir escaleras",
  "estado": "programada"
}
```

- `estado`: `programada`, `completada` o `cancelada`.
- `motivo` es **administrativo**, no clínico: indica el tipo de consulta ("Primera consulta", "Control", "Evaluación de movilidad", "Revisión de exámenes") y puede venir en `null`. Los detalles clínicos van en los síntomas, que se guardan cifrados.

### Fechas y zona horaria

- La API **devuelve** las fechas en UTC (terminan en `Z`). `2026-11-10T12:00:00Z` son las 09:00 en Chile. Para mostrarlas hay que convertirlas a la hora local: en JavaScript basta con `new Date(cita.fecha_hora)`.
- La API **exige** que las fechas que se le envían incluyan zona horaria (`Z` o un desfase como `-03:00`). Sin ella responde `422`, porque `2026-11-10T09:00` sin zona es ambiguo. En JavaScript, `fecha.toISOString()` ya la incluye.

### Web: calendario del médico (`GET /citas`)

El médico solo recibe **sus propias** citas. Para llenar el calendario, pedir el rango visible con `desde` (incluido) y `hasta` (excluido). Ejemplo para la semana actual:

```js
// Lunes 00:00 de esta semana, en la hora local del navegador
const inicio = new Date();
inicio.setHours(0, 0, 0, 0);
inicio.setDate(inicio.getDate() - ((inicio.getDay() + 6) % 7));

const fin = new Date(inicio);
fin.setDate(fin.getDate() + 7);

const params = new URLSearchParams({
  desde: inicio.toISOString(),
  hasta: fin.toISOString(),
});

const res = await fetch(`http://localhost:8000/citas?${params}`, {
  headers: { Authorization: `Bearer ${token}` },
});
const citas = await res.json();

// Convertir a eventos de calendario (inicio y fin en hora local)
const eventos = citas
  .filter((c) => c.estado !== "cancelada")
  .map((c) => {
    const start = new Date(c.fecha_hora);
    const end = new Date(start.getTime() + c.duracion_minutos * 60000);
    return { id: c.id, title: c.paciente_nombre, start, end, pacienteId: c.paciente_id };
  });
```

Con `pacienteId` se puede enlazar cada evento al resumen del paciente (`/pacientes/{id}/resumen`). Para mostrar también las canceladas (por ejemplo, tachadas), basta con no filtrarlas. Otros filtros útiles: `?estado=programada` y `?paciente_id=6` (todas las citas de un paciente).

### App: citas del paciente (`GET /mis-citas`)

```kotlin
@GET("mis-citas")
suspend fun misCitas(
    @Header("Authorization") token: String,
    @Query("solo_proximas") soloProximas: Boolean = true
): List<CitaResponse>

data class CitaResponse(
    val id: Int,
    val medico_nombre: String,
    val fecha_hora: String,
    val duracion_minutos: Int,
    val motivo: String?,
    val estado: String
)
```

Para mostrar la fecha en la hora del celular:

```kotlin
val fechaLocal = OffsetDateTime.parse(cita.fecha_hora)
    .atZoneSameInstant(ZoneId.systemDefault())
```

Por defecto solo vienen las citas próximas, de la más cercana a la más lejana: la primera de la lista es la próxima cita. Con `solo_proximas = false` vienen también las pasadas (historial).

### Admin: registrar y modificar citas

Probablemente no tenga interfaz en la web (lo haría el sistema del centro médico), pero se puede usar desde `/docs`.

Crear (`POST /citas`):
```json
{
  "paciente_id": 6,
  "medico_id": 3,
  "fecha_hora": "2026-11-12T10:00:00-03:00",
  "duracion_minutos": 30,
  "motivo": "Control"
}
```
Los ids se obtienen con `GET /admin/usuarios?rol=paciente` y `GET /admin/usuarios?rol=medico`.

Modificar (`PATCH /citas/{id}`), solo con los campos a cambiar:
- Reprogramar: `{"fecha_hora": "2026-11-12T11:00:00-03:00"}`
- Cancelar: `{"estado": "cancelada"}`
- Marcar como realizada: `{"estado": "completada"}`

### Reglas

- Las citas **no se borran**: se cancelan.
- La fecha debe ser futura (al crear o reprogramar). Si no, responde `400`.
- El médico no puede tener dos citas programadas que se crucen. Si se cruzan, responde `409`.
- La duración va de 10 a 180 minutos (30 por defecto).
- Una cita `cancelada` o `completada` ya no se puede modificar (`400`).
- El paciente debe estar activo, y el médico, existir y estar activo.

## Seguridad de los datos

- **Contraseñas:** se guardan con hash bcrypt, nunca en texto plano.
- **Acceso por rol:** cada endpoint exige un token JWT y valida el rol (paciente, médico o admin).
- **Cifrado en la base (AES-256-GCM):** se guardan cifrados el texto de los síntomas, el resumen generado por la IA, los comentarios de las ejecuciones de ejercicios y los documentos (nombre y contenido). El cifrado y descifrado es automático: la API siempre responde con los datos legibles, pero quien acceda directamente a la base solo ve bytes ilegibles. Además, GCM detecta si un dato cifrado fue alterado.
- **Datos que no se cifran:** ángulos, urgencia, diagnósticos diferenciales, fechas, ids, guías clínicas, ejercicios y el motivo de las citas. No identifican al paciente por sí solos y se necesitan para filtrar y ordenar.
- **IA:** a OpenAI solo se envía el texto de los síntomas anonimizado (sin RUT, email ni teléfono).
- **Auditoría:** los accesos de médicos a datos de pacientes y las acciones de administradores quedan registrados en una bitácora inmutable (ver [Auditoría](#auditoría-administrador)).

## Registro y gestión de usuarios

- El registro público (`/auth/registro`, usado por la app) **siempre crea pacientes**.
- Médicos y administradores los crea un admin con `POST /admin/usuarios`, indicando `rol`: `paciente`, `medico` o `admin`.
- Contraseña: mínimo 8 caracteres.
- El email se guarda en minúsculas, así que el login no distingue mayúsculas.
- Los usuarios **no se borran, se desactivan** (`PATCH` con `{"activo": false}`), para conservar su historial clínico. Una cuenta desactivada no puede iniciar sesión y sus tokens dejan de funcionar de inmediato. Se puede reactivar con `{"activo": true}`.
- Un admin no puede cambiar su propio rol ni desactivar su propia cuenta.

## Articulaciones válidas

Se usan los mismos valores en `/metricas` y en `/ejercicios`:

`rodilla`, `tobillo`, `hombro`, `codo`, `muneca`, `cadera`, `cervical`, `lumbar`

Reglas para `/metricas`:
- Articulaciones con dos lados (todas menos `cervical` y `lumbar`): `lado` es **obligatorio** y debe ser `izquierdo` o `derecho`.
- `cervical` y `lumbar`: **no** se envía `lado`.
- `angulo_minimo` no puede ser mayor que `angulo_maximo`.

Si alguna regla no se cumple, la API responde `422` con el detalle del error. En `/ejercicios` no existe `lado`: un mismo ejercicio sirve para ambos lados.

## Datos iniciales

Al levantar la base por primera vez, los scripts de `init/` se ejecutan en orden y cargan:

| Archivo | Contenido |
|---|---|
| `01_schema.sql` | Estructura de todas las tablas |
| `02_usuarios.sql` | 10 usuarios de prueba |
| `03_guias_clinicas.sql` | 16 guías clínicas de kinesiología/traumatología (sin embedding; ver abajo) |
| `04_ejercicios.sql` | 29 ejercicios (3-4 por articulación, sin imagen) |
| `05_citas.sql` | 9 citas de prueba: 7 programadas en los próximos días (la mayoría con `camila.rojas@arcamed.com`), 1 cancelada y 1 completada. Con motivo administrativo |

Las guías se cargan con `embedding` vacío porque un SQL no puede llamar a OpenAI. Después de levantar la base, ejecutar una vez `docker compose exec api python generar_embeddings_guias.py` (o `python generar_embeddings_guias.py` dentro de `app/` si corres el backend sin Docker). Sin este paso, el prediagnóstico no encuentra guías relevantes.

**Importante:** los scripts de `init/` solo se ejecutan cuando el volumen de la base se crea desde cero. Si ya tenías la base levantada y quieres cargar los datos iniciales, o si `01_schema.sql` cambió desde la última vez que la levantaste (por ejemplo, se agregó una columna):
```bash
docker compose down -v   # borra la base local, incluidos tus datos de prueba
docker compose up -d --build
docker compose exec api python generar_embeddings_guias.py
```

### Usuarios de prueba

Contraseña de todos: **`Arcamed2026`** (solo para desarrollo local).

| Rol | Email |
|---|---|
| admin | `admin@arcamed.com`, `soporte@arcamed.com` |
| medico | `camila.rojas@arcamed.com`, `matias.fuentes@arcamed.com`, `valentina.soto@arcamed.com` |
| paciente | `juan.perez@arcamed.com`, `maria.gonzalez@arcamed.com`, `diego.munoz@arcamed.com`, `fernanda.silva@arcamed.com`, `tomas.contreras@arcamed.com` |

> El contenido de las guías clínicas y del catálogo de ejercicios fue redactado con fines académicos y de demostración. No es material clínico validado.
