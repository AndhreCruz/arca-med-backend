# ARCA Med — Backend

## Sobre el proyecto

ARCA Med es un sistema de pre-consulta asistida por inteligencia artificial, compuesto por una aplicación Android (paciente) y una plataforma web (médico y administrador), diseñado específicamente para el ámbito de kinesiología y traumatología.

El sistema permite al paciente, antes de su consulta presencial:
- Registrar sus síntomas y antecedentes relevantes.
- Subir documentos médicos previos.
- Capturar su rango de movimiento articular mediante la cámara del celular.

A partir de esta información, ARCA Med genera automáticamente un resumen clínico y un prediagnóstico sugerido mediante RAG (Retrieval-Augmented Generation) sobre guías clínicas, que posteriormente es revisado por el profesional de salud desde un dashboard de triage antes de la atención presencial.

### Cómo funciona

1. **Cita:** el paciente tiene una cita en el centro médico (por ejemplo, "Traumatología de Rodilla", el jueves a las 09:00). En el MVP la registra el médico o el administrador.
2. **Pre-consulta (App, opcional pero recomendada):** antes de la cita, el paciente describe sus síntomas (indicando articulación y lado), adjunta exámenes previos y realiza una evaluación articular con la cámara del celular.
3. **IA:** al enviar la pre-consulta, ARCA Med genera un resumen clínico y diagnósticos diferenciales con probabilidad, usando la especialidad, los síntomas anonimizados, la evaluación articular y guías clínicas (RAG).
4. **Médico (Web):** ve sus citas en un calendario y una bandeja de triage ordenada por urgencia, revisa el resumen, los síntomas originales, los documentos y las mediciones, y llega a la consulta preparado.

Todo gira en torno a la **cita**: cada pre-consulta, sus mediciones y su prediagnóstico pertenecen a una cita y a su especialidad.

El objetivo es **apoyar y enriquecer** la consulta, entregando al profesional información estructurada y antecedentes recopilados previamente — nunca reemplazar su criterio clínico (el sistema es un CDSS: sugiere, no diagnostica).

### Plataformas

No es un sistema omnicanal (cada plataforma no ofrece lo mismo) — las funciones están repartidas según el rol:

- **App (Android)** — exclusiva para el **paciente**: registro/login, perfil con foto, sus citas y la pre-consulta de cada una (síntomas, documentos y evaluación articular por cámara), y los ejercicios de su cita.
- **Web** — exclusiva para **médico** y **administrador**: el médico ve su calendario de citas (y puede agendar y modificar las suyas), la bandeja de triage, los resúmenes/prediagnósticos y los síntomas, documentos y mediciones del paciente; el administrador gestiona usuarios, guías clínicas, el catálogo de ejercicios y todas las citas (ver [Citas](#citas)).

## API en producción

La API está desplegada y lista para consumir desde la web y la app:

- **URL base:** `https://arca-med-api.onrender.com`
- **Documentación interactiva:** `https://arca-med-api.onrender.com/docs`

Todos los endpoints de este README funcionan igual en producción: solo cambia la URL base. Los ejemplos usan `http://localhost:8000`; reemplázalo por la URL de producción. Conviene dejar la URL base en un solo lugar de configuración y no repetirla en cada llamada:

- **Web (Vite):** en un archivo `.env` del proyecto web, `VITE_API_URL=https://arca-med-api.onrender.com`, y en el código `import.meta.env.VITE_API_URL`.
- **App (Retrofit):** `.baseUrl("https://arca-med-api.onrender.com/")` (con `/` al final). Como es HTTPS, Android no necesita permitir tráfico sin cifrar (`usesCleartextTraffic`).

**A tener en cuenta:**
- **Primera petición lenta:** el plan gratuito apaga la API tras 15 minutos sin uso, y la siguiente petición tarda alrededor de un minuto en responder mientras se enciende. Después responde normal. Antes de una demo, abre `/docs` unos minutos antes. En la web y la app, conviene mostrar un indicador de carga y no cortar la petición antes de ~60 segundos.
- **CORS:** la API acepta llamadas de la web desplegada (`https://arcamed.vercel.app`) y de `http://localhost:5173` / `http://127.0.0.1:5173` para desarrollo. Las URLs de vista previa de Vercel no están habilitadas: si se necesita una, hay que pedir que se agregue.
- **Datos:** la base de producción tiene los mismos datos de prueba que la local (ver [Usuarios de prueba](#usuarios-de-prueba)). No ingresar datos reales de pacientes.

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

### Subir un archivo (documentos y fotos)

Los endpoints que reciben archivos (`/mis-citas/{id}/documentos`, `/perfil/foto`, `/ejercicios/{id}/imagen`) esperan `multipart/form-data`, no JSON, con el archivo en el campo `archivo`. La forma de mandarlo cambia un poco (ejemplo con documentos):

**Web (React):**
```js
const formData = new FormData();
formData.append("archivo", archivoSeleccionado);

const res = await fetch(`http://localhost:8000/mis-citas/${citaId}/documentos`, {
  method: "POST",
  headers: { Authorization: `Bearer ${token}` }, // NO poner Content-Type aquí, el navegador lo arma solo
  body: formData,
});
```

**App (Kotlin con Retrofit):**
```kotlin
@Multipart
@POST("mis-citas/{id}/documentos")
suspend fun subirDocumento(
    @Header("Authorization") token: String,
    @Path("id") citaId: Int,
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

`imagen_url` es una ruta relativa (ej. `/ejercicios/5/imagen?v=3f9a1c2e`), o `null` si el ejercicio no tiene imagen. Para mostrarla, anteponer la dirección del servidor: `http://localhost:8000` + `imagen_url`. Estas imágenes son públicas y no requieren token, así que sirven directo en un `<img src>` o en Coil/Glide. El `?v=...` cambia cada vez que el admin reemplaza la imagen, para que el navegador o la app no muestren la versión antigua guardada en caché.

### Códigos de error

- `401 Unauthorized` → no se mandó token, es inválido, expiró, o la cuenta fue desactivada → hay que loguear de nuevo.
- `403 Forbidden` → el token es válido, pero el rol del usuario no tiene permiso para ese endpoint (ej. un paciente llamando a un endpoint de médico). En el login, también indica que la cuenta está desactivada.
- `400 Bad Request` → la petición no se puede cumplir por una regla del negocio (ej. una cita en una fecha pasada, una cita ya cancelada que se intenta modificar, una articulación que no corresponde a la especialidad de la cita o un archivo que no es una imagen válida). El mensaje explica el motivo.
- `404 Not Found` → el recurso no existe (paciente, médico, especialidad, documento, ejercicio, usuario, cita, foto de perfil).
- `403 Forbidden` también aparece si un médico intenta agendar una cita para otro médico.
- `409 Conflict` → el médico ya tiene una cita en ese horario.
- `422 Unprocessable Entity` → el body no cumple las reglas (campo faltante, contraseña corta, articulación inválida, fecha sin zona horaria, etc.). La respuesta trae el detalle del error.

## Endpoints disponibles

### Autenticación (público)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/registro` | Crea una cuenta de **paciente** (el rol no se elige). Body: `{nombre, email, password}` y, opcionales, `{fecha_nacimiento, sexo, telefono}` (ver [Perfil](#perfil)). Devuelve `{access_token, rol}` |
| POST | `/auth/inicio-sesion` | Inicia sesión. Body: `{email, password}`. Devuelve `{access_token, rol}` |

### Perfil y catálogos (cualquier usuario logueado)

Cada usuario ve y edita **solo su propio** perfil (el del dueño del token). Detalles y ejemplos en la sección [Perfil](#perfil).

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/perfil` | Devuelve `{id, nombre, email, rol, fecha_nacimiento, edad, sexo, telefono, foto_url}` |
| PATCH | `/perfil` | Edita los datos propios. Se envían **solo** los campos a cambiar: `{nombre, fecha_nacimiento, sexo, telefono}`. Un campo con `null` se borra (salvo `nombre`). Devuelve el perfil actualizado |
| POST | `/perfil/foto` | Sube o reemplaza la foto de perfil (JPG/PNG, máx 5MB, `multipart/form-data`, campo `archivo`). Devuelve el perfil con la nueva `foto_url` |
| GET | `/perfil/foto` | Devuelve la foto de perfil (JPG). **Requiere token** |
| DELETE | `/perfil/foto` | Quita la foto de perfil. Devuelve el perfil con `foto_url: null` |
| GET | `/especialidades` | Catálogo de especialidades: `[{id, nombre, area, articulaciones}]` (ver [Especialidades](#especialidades)) |

### Paciente (App): citas y pre-consulta

El flujo completo está explicado en [Pre-consulta](#pre-consulta). `{id}` es el id de la **cita**.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/mis-citas` | Citas del paciente, de la más próxima a la más lejana, **con el estado de su pre-consulta**. Por defecto solo las próximas; `?solo_proximas=false` incluye también las pasadas |
| POST | `/mis-citas/{id}/sintomas` | **Paso 1 (requerido).** Síntomas de la cita. Body: `{descripcion, articulacion, lado}` (`articulacion` y `lado` según la especialidad). Se pueden corregir mientras la pre-consulta no se haya enviado |
| POST | `/mis-citas/{id}/documentos` | **Paso 2 (opcional).** Documento de antecedentes (PDF/JPG/PNG, máx 10MB, `multipart/form-data`, campo `archivo`). Se pueden subir varios |
| POST | `/mis-citas/{id}/metricas` | **Paso 3 (opcional, recomendado antes de enviar).** Evaluación articular. Body: `{angulo_maximo, angulo_minimo}`. La articulación y el lado se toman de los síntomas |
| POST | `/mis-citas/{id}/preconsulta/enviar` | **Paso 4.** Cierra la pre-consulta y genera el prediagnóstico con IA. Devuelve `{cita_id, preconsulta_enviada_en}` |
| GET | `/mis-citas/{id}/ejercicios` | Ejercicios de la articulación de esa cita: `[{id, nombre_ejercicio, descripcion, articulacion, imagen_url}]` |

### Paciente (App): otros

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/ejercicios` | Catálogo completo (también disponible para médico y admin). Filtro opcional: `?articulacion=rodilla`. Devuelve `[{id, nombre_ejercicio, descripcion, articulacion, imagen_url}]` |
| POST | `/ejercicios/{id}/ejecucion` | Registra que el paciente realizó el ejercicio. Body: `{correcto, comentario}` (comentario opcional). Devuelve `{id, ejercicio_id, correcto, comentario}` |
| POST | `/sintomas` | ⚠️ **Antiguo, sin cita.** Usar `POST /mis-citas/{id}/sintomas`. Se mantiene por compatibilidad |
| POST | `/documentos` | ⚠️ **Antiguo, sin cita.** Usar `POST /mis-citas/{id}/documentos` |
| POST | `/metricas` | ⚠️ **Antiguo, sin cita.** Usar `POST /mis-citas/{id}/metricas`. Body: `{articulacion, lado, angulo_maximo, angulo_minimo}` |

### Médico (Web)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/citas` | Citas **del médico logueado**, para el calendario, con el estado de la pre-consulta de cada una. Filtros opcionales: `?desde=`, `?hasta=`, `?paciente_id=`, `?especialidad_id=`, `?estado=` (ver [Citas](#citas)) |
| POST | `/citas` | Agenda una cita **consigo mismo** (no se envía `medico_id`). Body: `{paciente_id, especialidad_id, fecha_hora, duracion_minutos, motivo}` (`duracion_minutos` y `motivo` opcionales) |
| PATCH | `/citas/{id}` | Reprograma, cancela o completa **sus propias** citas. Se envían **solo** los campos a cambiar: `{fecha_hora, duracion_minutos, motivo, estado}` |
| GET | `/pacientes` | Lista los pacientes activos, ordenados por nombre. Búsqueda opcional: `?nombre=juan`. Devuelve `[{id, nombre, email}]` |
| GET | `/pacientes/triage` | Pacientes con prediagnóstico pendiente de revisión, ordenados por urgencia (alta → media → baja) |
| GET | `/pacientes/{id}/resumen` | Último prediagnóstico generado por IA para el paciente: resumen, diagnósticos diferenciales con probabilidad, urgencia sugerida y métricas físicas (ver [Prediagnóstico con IA](#prediagnóstico-con-ia)) |
| POST | `/pacientes/{id}/resumen/revisar` | Marca el prediagnóstico como revisado (sale de la bandeja de triage). Body: `{revisado_por_medico: true}` |
| GET | `/pacientes/{id}/sintomas` | Síntomas escritos por el paciente, texto original, del más reciente al más antiguo: `[{id, descripcion, creado_en, cita_id, articulacion, lado}]` (`cita_id`, `articulacion` y `lado` vienen cuando el síntoma es de una pre-consulta) |
| GET | `/pacientes/{id}/documentos` | Documentos subidos por el paciente: `[{id, nombre_archivo, tipo_archivo, subido_en}]` |
| GET | `/pacientes/{id}/documentos/{doc_id}/archivo` | Devuelve el archivo (PDF/imagen) para verlo o descargarlo (ver ejemplo arriba) |
| GET | `/guias-clinicas` | Lista las guías clínicas que usa la IA (también disponible para admin): `[{id, titulo, contenido, creado_en}]` |

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
| GET | `/ejercicios/{id}/imagen` | **Público** (sin token). Devuelve la imagen del ejercicio. Normalmente no se llama a mano: se usa la `imagen_url` que trae cada ejercicio |
| GET | `/citas` | Todas las citas. Mismos filtros que el médico, más `?medico_id=` |
| POST | `/citas` | Registra una cita para cualquier médico. Body: `{paciente_id, medico_id, especialidad_id, fecha_hora, duracion_minutos, motivo}` (`duracion_minutos` y `motivo` opcionales) |
| PATCH | `/citas/{id}` | Reprograma, cancela o completa cualquier cita. Se envían **solo** los campos a cambiar: `{fecha_hora, duracion_minutos, motivo, estado}` |

### Auditoría (Administrador)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/auditoria/logs` | Lista los registros de auditoría, del más reciente al más antiguo. Filtros opcionales: `?usuario_id=`, `?usuario_afectado_id=`, `?accion=`, `?limite=` (100 por defecto, máx. 500). Devuelve `[{id, usuario_id, rol, accion, usuario_afectado_id, detalle, ip, fecha}]` |
| GET | `/auditoria/verificar` | Recalcula la cadena de hash y confirma que ningún registro fue alterado. Devuelve `{integra, total_revisados, id_con_error, motivo}` |

**Qué se registra:** cada vez que un médico accede a datos de un paciente (`ver_pacientes`, `ver_triage`, `ver_resumen`, `revisar_prediagnostico`, `ver_sintomas`, `ver_documentos`, `descargar_documento`, `ver_citas`), cada cita creada o modificada por un médico o un admin (`crear_cita`, `editar_cita`) y cada acción de un admin (`crear_usuario`, `editar_usuario`, `crear_guia`, `crear_ejercicio`, `subir_imagen_ejercicio`). Al editar un usuario se guardan solo los nombres de los campos cambiados, nunca sus valores (por ejemplo, nunca la contraseña).

**Cómo se protege:** los registros no se pueden modificar ni borrar (triggers en la base de datos). Además, cada registro guarda el hash SHA-256 del anterior, formando una cadena: si alguien altera un registro directamente en la base, `/auditoria/verificar` lo detecta e indica cuál.

## Perfil

### Datos del perfil

`GET /perfil` devuelve:

```json
{
  "id": 6,
  "nombre": "Juan Pérez",
  "email": "juan.perez@arcamed.com",
  "rol": "paciente",
  "fecha_nacimiento": "1990-05-20",
  "edad": 36,
  "sexo": "masculino",
  "telefono": "+56912345678",
  "foto_url": "/perfil/foto?v=a1b2c3d4"
}
```

- `fecha_nacimiento`, `sexo`, `telefono` y `foto_url` pueden venir en `null` si el usuario no los ha ingresado.
- **`edad` no se envía nunca:** la API la calcula a partir de `fecha_nacimiento`, así siempre está al día.
- **`fecha_nacimiento`:** formato `AAAA-MM-DD` (ej. `"1990-05-20"`). No puede ser futura.
- **`sexo`:** uno de `femenino`, `masculino`, `otro` o `prefiero_no_decir`.
- **`telefono`:** solo números, con o sin `+` al inicio, entre 8 y 15 dígitos. Se aceptan espacios y guiones (`+56 9 1234-5678`), pero se guarda limpio (`+56912345678`).
- Estos tres campos se pueden enviar al registrarse (`POST /auth/registro`) o después con `PATCH /perfil`. Si no cumplen las reglas, la API responde `422`.

Editar (`PATCH /perfil`), solo con lo que cambia:
```json
{"telefono": "+56987654321", "sexo": "femenino"}
```
Para borrar un dato: `{"telefono": null}`. El email y la contraseña no se cambian aquí.

### Foto de perfil

**Subir (`POST /perfil/foto`):** igual que `/documentos`, con `multipart/form-data` y el archivo en el campo `archivo`.

```kotlin
@Multipart
@POST("perfil/foto")
suspend fun subirFotoPerfil(
    @Header("Authorization") token: String,
    @Part archivo: MultipartBody.Part
): PerfilResponse
```

La API recorta la foto al centro para dejarla **cuadrada (512 × 512)**, la comprime a JPG y elimina sus metadatos (por ejemplo, la ubicación GPS que guardan algunas fotos del celular). No hace falta procesarla antes en la app.

**Mostrar:** `foto_url` es una ruta relativa: anteponer la URL base (`https://arca-med-api.onrender.com` + `foto_url`). A diferencia de las imágenes de ejercicios, **la foto es privada**: hay que pedirla con el token. Con Coil:

```kotlin
AsyncImage(
    model = ImageRequest.Builder(LocalContext.current)
        .data(BASE_URL + perfil.foto_url)
        .addHeader("Authorization", "Bearer $accessToken")
        .build(),
    contentDescription = "Foto de perfil",
    modifier = Modifier.size(96.dp).clip(CircleShape),
    contentScale = ContentScale.Crop
)
```

Si `foto_url` es `null`, mostrar un avatar por defecto (por ejemplo, la inicial del nombre). El `?v=...` cambia cada vez que se sube una foto nueva, así la app no muestra la anterior guardada en caché.

## Citas

ARCA Med **no es un sistema de reserva de horas**. En un entorno real, el paciente reserva su hora en el sistema del centro médico, y ese sistema le informa la cita a ARCA Med. La cita es el **centro de la pre-consulta**: todo lo que el paciente envía (síntomas, documentos, evaluación articular) y el prediagnóstico de la IA quedan asociados a una cita concreta, con su especialidad.

En este MVP no existe ese sistema externo, así que lo **simulan el administrador y el médico**: las citas se registran con `POST /citas`. Además, la base trae **citas de prueba** (`init/05_citas.sql`) calculadas desde el día en que se levanta la base, para que siempre haya citas próximas. La integración con el sistema de agenda real del centro médico queda como mejora futura.

### Especialidades

Cada cita tiene una especialidad, y cada especialidad define **qué articulaciones se pueden evaluar** en su pre-consulta. Eso guía los síntomas, la evaluación articular y los ejercicios que ve el paciente.

| Especialidad | Área | Articulaciones |
|---|---|---|
| Traumatología de Rodilla | traumatologia | rodilla |
| Traumatología de Hombro | traumatologia | hombro |
| Traumatología de Cadera | traumatologia | cadera |
| Traumatología de Codo | traumatologia | codo |
| Traumatología de Mano y Muñeca | traumatologia | muneca |
| Traumatología de Pie y Tobillo | traumatologia | tobillo |
| Traumatología de Columna | traumatologia | cervical, lumbar |
| Kinesiología de Columna | kinesiologia | cervical, lumbar |
| Kinesiología Musculoesquelética | kinesiologia | todas |

`GET /especialidades` devuelve este catálogo con sus `id` (necesarios para crear citas).

### Formato de una cita

Todos los endpoints de citas (`/mis-citas`, `/citas`) devuelven el mismo formato:

```json
{
  "id": 1,
  "paciente_id": 6,
  "paciente_nombre": "Juan Pérez",
  "medico_id": 3,
  "medico_nombre": "Camila Rojas",
  "especialidad_id": 1,
  "especialidad_nombre": "Traumatología de Rodilla",
  "articulaciones": ["rodilla"],
  "fecha_hora": "2026-11-21T12:00:00Z",
  "duracion_minutos": 30,
  "motivo": "Primera consulta",
  "estado": "programada",
  "preconsulta": {
    "disponible": true,
    "sintomas_registrados": true,
    "articulacion": "rodilla",
    "lado": "derecho",
    "documentos": 1,
    "evaluaciones": 0,
    "enviada": true,
    "enviada_en": "2026-11-20T21:15:00Z"
  }
}
```

- `estado`: `programada`, `completada` o `cancelada`.
- `articulaciones`: las que permite la especialidad de la cita.
- `motivo` es **administrativo**, no clínico: indica el tipo de consulta ("Primera consulta", "Control", "Evaluación de movilidad", "Revisión de exámenes") y puede venir en `null`. Los detalles clínicos van en los síntomas, que se guardan cifrados.
- `preconsulta`: estado de la pre-consulta de esa cita (ver [Pre-consulta](#pre-consulta)). En la web del médico sirve para mostrar en el calendario si el paciente ya la completó.

### Fechas y zona horaria

- La API **devuelve** las fechas en UTC (terminan en `Z`). `2026-11-21T12:00:00Z` son las **09:00 en Chile**. **Siempre** hay que convertirlas a la hora local antes de mostrarlas:
  - JavaScript: `new Date(cita.fecha_hora)`.
  - Kotlin: `OffsetDateTime.parse(cita.fecha_hora).atZoneSameInstant(ZoneId.systemDefault())`.
- La API **exige** que las fechas que se le envían incluyan zona horaria (`Z` o un desfase como `-03:00`). Sin ella responde `422`, porque `2026-11-21T09:00` sin zona es ambiguo. En JavaScript, `fecha.toISOString()` ya la incluye.

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
    return {
      id: c.id,
      title: `${c.paciente_nombre} · ${c.especialidad_nombre}`,
      start,
      end,
      pacienteId: c.paciente_id,
      preconsultaEnviada: c.preconsulta.enviada,
    };
  });
```

Con `pacienteId` se puede enlazar cada evento al resumen del paciente, y con `preconsultaEnviada` marcar las citas cuyo paciente ya completó su pre-consulta. Para mostrar también las canceladas (por ejemplo, tachadas), basta con no filtrarlas. Otros filtros útiles: `?estado=programada`, `?especialidad_id=1` y `?paciente_id=6`.

### Crear y modificar citas (médico y admin)

Se puede hacer desde la web o desde `/docs`.

**Médico** (`POST /citas`): agenda **consigo mismo**, así que **no** envía `medico_id`:
```json
{
  "paciente_id": 6,
  "especialidad_id": 1,
  "fecha_hora": "2026-11-27T10:00:00-03:00",
  "duracion_minutos": 30,
  "motivo": "Control"
}
```
Si envía el `medico_id` de otro médico, la API responde `403`.

**Admin** (`POST /citas`): igual, pero **debe** indicar `medico_id` (si falta, `422`).

Los ids se obtienen con `GET /pacientes` (médico), `GET /admin/usuarios?rol=...` (admin) y `GET /especialidades`.

**Modificar** (`PATCH /citas/{id}`), solo con los campos a cambiar. El médico solo puede modificar sus propias citas (las de otro médico responden `404`):
- Reprogramar: `{"fecha_hora": "2026-11-27T11:00:00-03:00"}`
- Cancelar: `{"estado": "cancelada"}`
- Marcar como realizada: `{"estado": "completada"}`

### Reglas

- Las citas **no se borran**: se cancelan.
- La fecha debe ser futura (al crear o reprogramar). Si no, responde `400`.
- El médico no puede tener dos citas programadas que se crucen. Si se cruzan, responde `409`.
- La duración va de 10 a 180 minutos (30 por defecto).
- Una cita `cancelada` o `completada` ya no se puede modificar (`400`).
- El paciente debe estar activo; el médico y la especialidad deben existir (`404` si no).

## Pre-consulta

La pre-consulta es **opcional para el paciente, pero recomendada**: permite que el médico llegue a la consulta con los síntomas, los antecedentes y una evaluación de movilidad ya ordenados, más un prediagnóstico sugerido por IA. Cada cita tiene su **propia** pre-consulta, independiente de las demás.

### Flujo en la app

1. **Mis citas** (`GET /mis-citas`): cada cita muestra especialidad, fecha y hora (en hora local), médico y el estado de su pre-consulta. Si `preconsulta.disponible` es `true` y `preconsulta.enviada` es `false`, mostrar el botón "Completar pre-consulta".
2. **Síntomas (requerido)**: `POST /mis-citas/{id}/sintomas`.
3. **Documentos (opcional)**: `POST /mis-citas/{id}/documentos`, uno por archivo.
4. **Evaluación articular (opcional, recomendada ahora)**: `POST /mis-citas/{id}/metricas`.
5. **Enviar**: `POST /mis-citas/{id}/preconsulta/enviar`. Aquí se genera el prediagnóstico con IA.
6. **Después de enviar**: mostrar "Pre-consulta enviada". Si `preconsulta.evaluaciones` es `0`, mostrar que aún puede realizar su evaluación articular (mismo endpoint del paso 4).

### Estado de la pre-consulta

Cada cita trae el objeto `preconsulta`:

| Campo | Significado |
|---|---|
| `disponible` | `true` si la cita está programada y aún no ocurre. Si es `false`, no mostrar los botones de la pre-consulta |
| `sintomas_registrados` | Si ya registró los síntomas (paso 2) |
| `articulacion`, `lado` | Lo que indicó en sus síntomas. Es lo que se va a evaluar con la cámara |
| `documentos` | Cantidad de documentos subidos |
| `evaluaciones` | Cantidad de evaluaciones articulares registradas |
| `enviada`, `enviada_en` | Si ya presionó "Enviar" y cuándo |

### Paso 2: síntomas

`POST /mis-citas/{id}/sintomas`:
```json
{"descripcion": "Me duele la rodilla derecha al subir escaleras hace dos semanas", "lado": "derecho"}
```

Texto sugerido para la app: *"Cuéntanos tus síntomas para tu consulta de {especialidad_nombre}"*.

Qué enviar según la especialidad de la cita (campo `articulaciones` de la cita):
- **`articulacion`**: si `articulaciones` tiene **una sola**, no se envía (se asigna sola). Si tiene **varias** (Columna, Kinesiología Musculoesquelética), mostrar un selector con esas opciones y enviar la elegida.
- **`lado`** (`izquierdo` o `derecho`): obligatorio en todas las articulaciones **excepto** `cervical` y `lumbar`, donde **no** se envía.

Si los síntomas se envían de nuevo antes de "Enviar", **se actualizan** (no se duplican). Después de enviar la pre-consulta ya no se pueden modificar. Tampoco se puede cambiar la articulación o el lado si ya se registró una evaluación articular.

Devuelve `{id, cita_id, descripcion, articulacion, lado, creado_en}`.

### Paso 3: documentos

`POST /mis-citas/{id}/documentos`, igual que el resto de subidas: `multipart/form-data` con el archivo en el campo `archivo` (PDF/JPG/PNG, máx 10MB). Se pueden subir varios, y también después de enviar la pre-consulta (hasta la hora de la cita).

```kotlin
@Multipart
@POST("mis-citas/{id}/documentos")
suspend fun subirDocumentoCita(
    @Header("Authorization") token: String,
    @Path("id") citaId: Int,
    @Part archivo: MultipartBody.Part
): DocumentoResponse
```

### Paso 4: evaluación articular

La app **no pregunta qué articulación evaluar**: usa `preconsulta.articulacion` y `preconsulta.lado` de la cita y envía solo los ángulos medidos:

`POST /mis-citas/{id}/metricas`:
```json
{"angulo_maximo": 120, "angulo_minimo": 15}
```

- Requiere que los síntomas ya estén registrados (si no, `400`).
- La API guarda la medición con la articulación y el lado de los síntomas, así siempre coinciden con lo que el paciente declaró.
- Ángulos entre 0 y 180, y `angulo_minimo` no puede ser mayor que `angulo_maximo` (`422`).
- Se puede hacer antes o después de enviar, hasta la hora de la cita. **Si se hace antes de enviar, la IA la considera en el prediagnóstico**; si se hace después, solo la ve el médico. Por eso conviene recomendarla en el momento ("Te recomendamos hacerla ahora: así tu médico recibe un análisis más completo"), con la opción "Más tarde".

### Paso 5: enviar

`POST /mis-citas/{id}/preconsulta/enviar` (sin body). Requiere los síntomas registrados. Marca la pre-consulta como enviada y genera el prediagnóstico con IA en segundo plano (ver [Prediagnóstico con IA](#prediagnóstico-con-ia)). Solo se puede enviar una vez.

### Ejercicios de la cita

`GET /mis-citas/{id}/ejercicios` devuelve los ejercicios de la articulación indicada en los síntomas; si aún no hay síntomas, los de todas las articulaciones de la especialidad. Funciona también después de la cita.

### Ejemplo en Kotlin

```kotlin
data class PreconsultaEstado(
    val disponible: Boolean,
    val sintomas_registrados: Boolean,
    val articulacion: String?,
    val lado: String?,
    val documentos: Int,
    val evaluaciones: Int,
    val enviada: Boolean,
    val enviada_en: String?
)

data class CitaResponse(
    val id: Int,
    val medico_nombre: String,
    val especialidad_nombre: String,
    val articulaciones: List<String>,
    val fecha_hora: String,
    val duracion_minutos: Int,
    val motivo: String?,
    val estado: String,
    val preconsulta: PreconsultaEstado
)

interface ApiService {
    @GET("mis-citas")
    suspend fun misCitas(
        @Header("Authorization") token: String,
        @Query("solo_proximas") soloProximas: Boolean = true
    ): List<CitaResponse>

    @POST("mis-citas/{id}/sintomas")
    suspend fun registrarSintomas(
        @Header("Authorization") token: String,
        @Path("id") citaId: Int,
        @Body datos: SintomasRequest   // {descripcion, articulacion?, lado?}
    ): SintomaResponse

    @POST("mis-citas/{id}/metricas")
    suspend fun registrarMetrica(
        @Header("Authorization") token: String,
        @Path("id") citaId: Int,
        @Body datos: MetricaRequest    // {angulo_maximo, angulo_minimo}
    ): MetricaResponse

    @POST("mis-citas/{id}/preconsulta/enviar")
    suspend fun enviarPreconsulta(
        @Header("Authorization") token: String,
        @Path("id") citaId: Int
    ): PreconsultaEnviadaResponse

    @GET("mis-citas/{id}/ejercicios")
    suspend fun ejerciciosCita(
        @Header("Authorization") token: String,
        @Path("id") citaId: Int
    ): List<EjercicioResponse>
}
```

### Errores frecuentes de la pre-consulta

| Código | Mensaje (resumido) | Qué hacer |
|---|---|---|
| `404` | Cita no encontrada | La cita no existe o es de otro paciente |
| `400` | La pre-consulta solo está disponible para citas programadas que aún no ocurren | La cita pasó o fue cancelada (`preconsulta.disponible` es `false`) |
| `400` | Debes indicar la articulación / el lado | Mostrar el selector correspondiente |
| `400` | Para {especialidad} solo se puede evaluar: [...] | La articulación no corresponde a la especialidad |
| `400` | Primero registra tus síntomas para esta cita | Llamar antes a `/sintomas` |
| `400` | La pre-consulta ya fue enviada | Ya no se pueden editar los síntomas ni volver a enviar |

## Prediagnóstico con IA

### Cuándo se genera

Al **enviar la pre-consulta** (`POST /mis-citas/{id}/preconsulta/enviar`). Se genera en segundo plano: la API responde al instante y el prediagnóstico aparece en la bandeja de triage del médico unos segundos después. El paciente **no** ve el prediagnóstico.

### Qué recibe la IA

1. **Especialidad** de la cita.
2. **Articulación y lado** indicados por el paciente.
3. **Edad y sexo**, si están en su perfil.
4. **Síntomas, anonimizados** (sin RUT, email ni teléfono).
5. **Evaluación articular**, si se hizo **antes** de enviar. Si no, se le indica que no se realizó.
6. **Guías clínicas relevantes** (RAG): se buscan por similitud usando la especialidad, la articulación y los síntomas.

**Nunca** se envían el nombre, el email, el teléfono ni los documentos del paciente.

### Qué devuelve

```json
{
  "resumen": "Paciente de 36 años, sexo masculino, consulta por dolor en hombro izquierdo de un mes de evolución, que aumenta al elevar el brazo y al acostarse sobre ese lado. La evaluación articular muestra un ángulo máximo de 95°, lo que sugiere una limitación de la elevación respecto del rango habitual. Se sugiere evaluar el manguito rotador y descartar una capsulitis adhesiva.",
  "diagnosticos_diferenciales": [
    {"diagnostico": "Tendinopatía del manguito rotador", "probabilidad": 50},
    {"diagnostico": "Síndrome de pinzamiento subacromial", "probabilidad": 30},
    {"diagnostico": "Capsulitis adhesiva (hombro congelado)", "probabilidad": 20}
  ],
  "urgencia_sugerida": "media"
}
```

- **`resumen`**: 3 a 5 frases con el motivo de consulta, las características de los síntomas, los hallazgos de la evaluación articular (si existe) y aspectos a considerar en la consulta.
- **`diagnosticos_diferenciales`**: entre 2 y 4, **nunca uno solo**, para no anclar el criterio del médico a una única opción. Las probabilidades son orientativas y no necesitan sumar 100.
- **`urgencia_sugerida`**: `baja`, `media` o `alta`. `alta` se reserva para señales de alarma (trauma reciente con incapacidad de apoyar o mover, deformidad, fiebre, déficit neurológico, dolor nocturno intenso o alteración del control de esfínteres). Ordena la bandeja de triage.

La evaluación articular es **referencial**: son ángulos medidos con la cámara del celular, no una goniometría clínica, y la IA lo considera así.

### Cómo lo ve el médico

- `GET /pacientes/triage`: pacientes con prediagnóstico pendiente, ordenados por urgencia.
- `GET /pacientes/{id}/resumen`: el prediagnóstico más reciente del paciente, con sus métricas.
- `POST /pacientes/{id}/resumen/revisar`: lo marca como revisado y sale de la bandeja.

El sistema **sugiere, no diagnostica**: la decisión clínica siempre es del médico.

## Seguridad de los datos

- **Contraseñas:** se guardan con hash bcrypt, nunca en texto plano.
- **Acceso por rol:** cada endpoint exige un token JWT y valida el rol (paciente, médico o admin).
- **Cifrado en la base (AES-256-GCM):** se guardan cifrados el texto de los síntomas, el resumen generado por la IA, los comentarios de las ejecuciones de ejercicios, los documentos (nombre y contenido), el teléfono y la foto de perfil. El cifrado y descifrado es automático: la API siempre responde con los datos legibles, pero quien acceda directamente a la base solo ve bytes ilegibles. Además, GCM detecta si un dato cifrado fue alterado.
- **Datos que no se cifran:** ángulos, urgencia, diagnósticos diferenciales, fechas (incluida la de nacimiento), sexo, ids, guías clínicas, ejercicios y el motivo de las citas. No identifican al paciente por sí solos y se necesitan para filtrar y ordenar.
- **Fotos de perfil:** al subirlas se eliminan sus metadatos EXIF (que pueden incluir la ubicación GPS donde se tomó la foto).
- **IA:** a OpenAI se envían los síntomas anonimizados (sin RUT, email ni teléfono), la especialidad, la articulación y el lado, la edad y el sexo, y los ángulos de la evaluación articular. **Nunca** el nombre, el email, el teléfono ni los documentos del paciente (ver [Prediagnóstico con IA](#prediagnóstico-con-ia)).
- **Auditoría:** los accesos de médicos a datos de pacientes y las acciones de administradores quedan registrados en una bitácora inmutable (ver [Auditoría](#auditoría-administrador)).

## Registro y gestión de usuarios

- El registro público (`/auth/registro`, usado por la app) **siempre crea pacientes**.
- Médicos y administradores los crea un admin con `POST /admin/usuarios`, indicando `rol`: `paciente`, `medico` o `admin`.
- Contraseña: mínimo 8 caracteres.
- El email se guarda en minúsculas, así que el login no distingue mayúsculas.
- Los usuarios **no se borran, se desactivan** (`PATCH` con `{"activo": false}`), para conservar su historial clínico. Una cuenta desactivada no puede iniciar sesión y sus tokens dejan de funcionar de inmediato. Se puede reactivar con `{"activo": true}`.
- Un admin no puede cambiar su propio rol ni desactivar su propia cuenta.

## Articulaciones válidas

Se usan los mismos valores en la pre-consulta, en `/metricas` y en `/ejercicios`:

`rodilla`, `tobillo`, `hombro`, `codo`, `muneca`, `cadera`, `cervical`, `lumbar`

Las articulaciones que se pueden evaluar en cada cita dependen de su especialidad (ver [Especialidades](#especialidades)).

Reglas del lado (en `/mis-citas/{id}/sintomas` y en el antiguo `/metricas`):
- Articulaciones con dos lados (todas menos `cervical` y `lumbar`): `lado` es **obligatorio** y debe ser `izquierdo` o `derecho`.
- `cervical` y `lumbar`: **no** se envía `lado`.
- `angulo_minimo` no puede ser mayor que `angulo_maximo`.

Si alguna regla no se cumple, la API responde `400` (pre-consulta) o `422` (`/metricas`) con el detalle del error. En `/ejercicios` no existe `lado`: un mismo ejercicio sirve para ambos lados.

## Datos iniciales

Al levantar la base por primera vez, los scripts de `init/` se ejecutan en orden y cargan:

| Archivo | Contenido |
|---|---|
| `01_schema.sql` | Estructura de todas las tablas y las 9 especialidades |
| `02_usuarios.sql` | 10 usuarios de prueba |
| `03_guias_clinicas.sql` | 16 guías clínicas de kinesiología/traumatología (sin embedding; ver abajo) |
| `04_ejercicios.sql` | 29 ejercicios (3-4 por articulación, sin imagen) |
| `05_citas.sql` | 9 citas de prueba con especialidad: 7 programadas en los próximos días, 1 cancelada y 1 completada. `camila.rojas` atiende traumatología; `matias.fuentes` y `valentina.soto`, kinesiología |

Las guías se cargan con `embedding` vacío porque un SQL no puede llamar a OpenAI. Después de levantar la base, ejecutar una vez `docker compose exec api python generar_embeddings_guias.py` (o `python generar_embeddings_guias.py` dentro de `app/` si corres el backend sin Docker). Sin este paso, el prediagnóstico no encuentra guías relevantes.

**Importante:** los scripts de `init/` solo se ejecutan cuando el volumen de la base se crea desde cero. Si ya tenías la base levantada y quieres cargar los datos iniciales, o si `01_schema.sql` cambió desde la última vez que la levantaste (por ejemplo, se agregó una columna):
```bash
docker compose down -v   # borra la base local, incluidos tus datos de prueba
docker compose up -d --build
docker compose exec api python generar_embeddings_guias.py
```

### Usuarios de prueba

Contraseña de todos: **`Arcamed2026`**, en local y en producción. En producción, las contraseñas de los **admin** son distintas y se comparten por un canal privado del equipo.

| Rol | Email |
|---|---|
| admin | `admin@arcamed.com`, `soporte@arcamed.com` |
| medico | `camila.rojas@arcamed.com`, `matias.fuentes@arcamed.com`, `valentina.soto@arcamed.com` |
| paciente | `juan.perez@arcamed.com`, `maria.gonzalez@arcamed.com`, `diego.munoz@arcamed.com`, `fernanda.silva@arcamed.com`, `tomas.contreras@arcamed.com` |

> El contenido de las guías clínicas y del catálogo de ejercicios fue redactado con fines académicos y de demostración. No es material clínico validado.