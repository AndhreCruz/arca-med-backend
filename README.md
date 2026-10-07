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

- **App (Android)** — exclusiva para el **paciente**: registro/login, carga de síntomas y documentos, captura de rango de movimiento por cámara.
- **Web** — exclusiva para **médico** y **administrador**: el médico ve el dashboard de triage y los resúmenes/prediagnósticos; el administrador gestiona usuarios y guías clínicas.

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
SECRET_KEY=cualquier-texto-largo-random
OPENAI_API_KEY=sk-...
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
  headers: { Authorization: `Bearer ${token}` }, 
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

### Qué pasa si el token falta o es inválido

La API responde:
- `401 Unauthorized` → no se mandó token, o es inválido/expiró → hay que loguear de nuevo.
- `403 Forbidden` → el token es válido, pero el rol del usuario no tiene permiso para ese endpoint específico (ej. un paciente llamando a un endpoint solo de médico).

## Endpoints disponibles actualmente

| Método | Ruta | Rol requerido | Descripción |
|---|---|---|---|
| POST | `/auth/registro` | — | Crea una cuenta de **paciente** (el rol no se elige). Body: `{nombre, email, password}`. Devuelve `{access_token, rol}` |
| POST | `/auth/inicio-sesion` | — | Inicia sesión. Body: `{email, password}`. Devuelve `{access_token, rol}` |
| GET | `/perfil` | cualquier usuario logueado | Devuelve los datos del usuario dueño del token |
| GET | `/medico/dashboard` | medico | Endpoint de ejemplo, solo accesible por médicos |
| GET | `/admin/usuarios` | admin | Lista todos los usuarios registrados |
| POST | `/admin/usuarios` | admin | Crea un usuario de cualquier rol. Body: `{nombre, email, password, rol}`. Devuelve `{id, nombre, email, rol}` |
| POST | `/sintomas` | paciente | Registra un síntoma. Body: `{descripcion}`. Devuelve `{id, descripcion}` |
| POST | `/documentos` | paciente | Sube un documento (PDF/JPG/PNG, máx 10MB). Body: `multipart/form-data` con el archivo en el campo `archivo`. Devuelve `{id, nombre_archivo, ruta_archivo}` |
| POST | `/metricas` | paciente | Registra una métrica de rango de movimiento. Body: `{articulacion, lado, angulo_maximo, angulo_minimo}` (ver reglas de articulaciones abajo). Devuelve `{id, articulacion, lado, angulo_maximo, angulo_minimo}` |
| POST | `/guias-clinicas` | admin | Carga una guía clínica (genera su embedding automáticamente). Body: `{titulo, contenido}`. Devuelve `{id, titulo}` |
| GET | `/pacientes/triage` | medico | Lista pacientes con prediagnóstico pendiente de revisión, ordenados por urgencia (alta → media → baja) |
| GET | `/pacientes/{id}/resumen` | medico | Devuelve el resumen generado por IA del paciente: resumen, diagnósticos diferenciales con probabilidad, urgencia sugerida y métricas físicas |
| POST | `/pacientes/{id}/resumen/revisar` | medico | Marca el prediagnóstico del paciente como revisado. Body: `{revisado_por_medico: true}` |
| POST | `/ejercicios` | admin | Crea un ejercicio del catálogo. Body: `{nombre_ejercicio, descripcion, articulacion}`. Devuelve el ejercicio creado |
| POST | `/ejercicios/{id}/imagen` | admin | Sube o reemplaza la imagen del ejercicio (JPG/PNG, `multipart/form-data`, campo `archivo`). Devuelve el ejercicio con `imagen_url` |
| GET | `/ejercicios` | paciente, admin | Lista el catálogo. Filtro opcional: `?articulacion=rodilla`. Devuelve `[{id, nombre_ejercicio, descripcion, articulacion, imagen_url}]` |
| POST | `/ejercicios/{id}/ejecucion` | paciente | Registra que el paciente realizó el ejercicio. Body: `{correcto, comentario}` (comentario opcional). Devuelve `{id, ejercicio_id, correcto, comentario}` |

### Mostrar imágenes de ejercicios

`imagen_url` es una ruta relativa (ej. `/static/ejercicios/abc.png`). Para mostrarla, anteponer la dirección del servidor: `http://localhost:8000` + `imagen_url`. Estas imágenes son públicas y no requieren token.

## Registro y creación de usuarios

- El registro público (`/auth/registro`, usado por la app) **siempre crea pacientes**.
- Médicos y administradores los crea un admin con `POST /admin/usuarios`, indicando `rol`: `paciente`, `medico` o `admin`.
- Contraseña: mínimo 8 caracteres.
- El email se guarda en minúsculas, así que el login no distingue mayúsculas.

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

**Importante:** los scripts de `init/` solo se ejecutan cuando el volumen de la base se crea desde cero. Si ya tenías la base levantada y quieres cargar los datos iniciales:
```bash
docker compose down -v   # borra la base local, incluidos tus datos de prueba
docker compose up -d
```

### Usuarios de prueba

Contraseña de todos: **`Arcamed2026`** (solo para desarrollo local).

| Rol | Email |
|---|---|
| admin | `admin@arcamed.com`, `soporte@arcamed.com` |
| medico | `camila.rojas@arcamed.com`, `matias.fuentes@arcamed.com`, `valentina.soto@arcamed.com` |
| paciente | `juan.perez@arcamed.com`, `maria.gonzalez@arcamed.com`, `diego.munoz@arcamed.com`, `fernanda.silva@arcamed.com`, `tomas.contreras@arcamed.com` |

> El contenido de las guías clínicas y del catálogo de ejercicios fue redactado con fines académicos y de demostración. No es material clínico validado.
