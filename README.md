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

- **App (Android)** — exclusiva para el **paciente**: registro/login, carga de síntomas y documentos, captura de rango de movimiento por cámara y catálogo de ejercicios.
- **Web** — exclusiva para **médico** y **administrador**: el médico ve el dashboard de triage, los resúmenes/prediagnósticos y los síntomas y documentos del paciente; el administrador gestiona usuarios, guías clínicas y el catálogo de ejercicios.

## Cómo levantar el proyecto

Requisitos: [Docker Desktop](https://www.docker.com/products/docker-desktop/) y Python 3.11+.

```bash
git clone <URL_DEL_REPO>
cd arca-med-backend

# 1. Levantar la base de datos
docker compose up -d

# 2. Levantar el backend
cd app
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

Antes de correr el backend, crea un archivo `.env` dentro de `app/` (no viene en el repo) con:
```
DATABASE_URL=postgresql://arca:arca123@localhost:5432/arcamed
SECRET_KEY=cualquier-texto
OPENAI_API_KEY=sk-...
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

> `OPENAI_API_KEY` es una credencial real que cuesta dinero: pídela por un canal privado del equipo. **Nunca** la subas al repo ni la pegues en este README.

Genera los embeddings de las guías clínicas (solo la primera vez, o cuando se agreguen guías por SQL):
```bash
python generar_embeddings_guias.py
```

Corre el servidor:
```bash
uvicorn main:app --reload
```

- API corriendo en: `http://localhost:8000`
- Documentación interactiva (probar todo desde el navegador): `http://localhost:8000/docs`

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
- `404 Not Found` → el recurso no existe (paciente, documento, ejercicio, usuario).
- `422 Unprocessable Entity` → el body no cumple las reglas (campo faltante, contraseña corta, articulación inválida, etc.). La respuesta trae el detalle del error.

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
| POST | `/sintomas` | Registra un síntoma. Body: `{descripcion}`. Devuelve `{id, descripcion}`. Genera automáticamente el prediagnóstico con IA (el paciente no lo ve) |
| POST | `/documentos` | Sube un documento (PDF/JPG/PNG, máx 10MB). Body: `multipart/form-data` con el archivo en el campo `archivo`. Devuelve `{id, nombre_archivo, ruta_archivo}` |
| POST | `/metricas` | Registra una métrica de rango de movimiento. Body: `{articulacion, lado, angulo_maximo, angulo_minimo}` (ver reglas de articulaciones abajo). Devuelve `{id, articulacion, lado, angulo_maximo, angulo_minimo}` |
| GET | `/ejercicios` | Lista el catálogo (también disponible para admin). Filtro opcional: `?articulacion=rodilla`. Devuelve `[{id, nombre_ejercicio, descripcion, articulacion, imagen_url}]` |
| POST | `/ejercicios/{id}/ejecucion` | Registra que el paciente realizó el ejercicio. Body: `{correcto, comentario}` (comentario opcional). Devuelve `{id, ejercicio_id, correcto, comentario}` |

### Médico (Web)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/pacientes/triage` | Pacientes con prediagnóstico pendiente de revisión, ordenados por urgencia (alta → media → baja) |
| GET | `/pacientes/{id}/resumen` | Resumen generado por IA: resumen, diagnósticos diferenciales con probabilidad, urgencia sugerida y métricas físicas |
| POST | `/pacientes/{id}/resumen/revisar` | Marca el prediagnóstico como revisado (sale de la bandeja de triage). Body: `{revisado_por_medico: true}` |
| GET | `/pacientes/{id}/sintomas` | Síntomas escritos por el paciente, texto original, del más reciente al más antiguo: `[{id, descripcion, creado_en}]` |
| GET | `/pacientes/{id}/documentos` | Documentos subidos por el paciente: `[{id, nombre_archivo, tipo_archivo, subido_en}]` |
| GET | `/pacientes/{id}/documentos/{doc_id}/archivo` | Devuelve el archivo (PDF/imagen) para verlo o descargarlo (ver ejemplo arriba) |
| GET | `/medico/dashboard` | Endpoint de ejemplo, solo accesible por médicos |

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

Las guías se cargan con `embedding` vacío porque un SQL no puede llamar a OpenAI. Después de levantar la base, ejecutar una vez `python generar_embeddings_guias.py` (dentro de `app/`). Sin este paso, el prediagnóstico no encuentra guías relevantes.

**Importante:** los scripts de `init/` solo se ejecutan cuando el volumen de la base se crea desde cero. Si ya tenías la base levantada y quieres cargar los datos iniciales, o si `01_schema.sql` cambió desde la última vez que la levantaste (por ejemplo, se agregó una columna):
```bash
docker compose down -v   # borra la base local, incluidos tus datos de prueba
docker compose up -d
```
Después de recrearla, vuelve a correr `python generar_embeddings_guias.py`.

### Usuarios de prueba

Contraseña de todos: **`Arcamed2026`** (solo para desarrollo local).

| Rol | Email |
|---|---|
| admin | `admin@arcamed.com`, `soporte@arcamed.com` |
| medico | `camila.rojas@arcamed.com`, `matias.fuentes@arcamed.com`, `valentina.soto@arcamed.com` |
| paciente | `juan.perez@arcamed.com`, `maria.gonzalez@arcamed.com`, `diego.munoz@arcamed.com`, `fernanda.silva@arcamed.com`, `tomas.contreras@arcamed.com` |

> El contenido de las guías clínicas y del catálogo de ejercicios fue redactado con fines académicos y de demostración. No es material clínico validado.
