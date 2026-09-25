# ARCA Med — Backend

## Sobre el proyecto

**ARCA Med** es un sistema de **pre-consulta asistida por inteligencia artificial**, compuesto por una aplicación Android y una plataforma web, diseñado específicamente para el ámbito de **kinesiología y traumatología**.

El sistema permite al paciente, antes de su consulta presencial:

- Registrar sus síntomas y antecedentes relevantes.
- Subir documentos médicos previos.
- Capturar su rango de movimiento articular mediante la cámara del celular.

A partir de esta información, ARCA Med genera un **resumen clínico** y un **prediagnóstico sugerido mediante RAG (Retrieval-Augmented Generation) sobre guías clínicas**, que posteriormente es revisado por el profesional de salud desde un dashboard de triage antes de la atención presencial.

El objetivo es **agilizar y enriquecer la consulta**, proporcionando al profesional información estructurada y antecedentes recopilados previamente.

> Este repositorio corresponde al **backend de ARCA Med**.

## Cómo levantar el proyecto

Requisitos: [Docker Desktop](https://www.docker.com/products/docker-desktop/) y Python 3.11+.

```bash
git clone https://github.com/AndhreCruz/arca-med-backend.git
cd arca-med-backend

# 1. Levantar la base de datos
docker compose up -d

# 2. Levantar el backend
cd app
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

Antes de correr el backend, crea un archivo `.env` dentro de `app/` con:
```
DATABASE_URL=postgresql://arca:arca123@localhost:5432/arcamed
SECRET_KEY=cualquier-texto-largo-random
```

Corre el servidor:
```bash
uvicorn main:app --reload
```

- API corriendo en: `http://localhost:8000`
- Documentación interactiva (probar todo desde el navegador): `http://localhost:8000/docs`

## Cómo integrar la autenticación (Web / App)

La mayoría de los endpoints requieren estar logueado. El flujo general, sin importar la plataforma:

1. Llamar a `POST /auth/register` o `POST /auth/login` → la API devuelve `{ "access_token": "...", "rol": "..." }`.
2. Guardar ese `access_token` localmente (no se pierde al cerrar la app/pestaña si se guarda bien).
3. En **cada** petición a un endpoint protegido, agregar el header:

   ```
   Authorization: Bearer <access_token>
   ```

### Web (React)

Guardar el token después del login (ej. en `localStorage`):
```js
const res = await fetch("http://localhost:8000/auth/login", {
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

const res = await fetch("http://localhost:8000/me", {
  headers: { Authorization: `Bearer ${token}` },
});
```

### App (Android / Kotlin con Retrofit)

Definir el header en la interfaz de Retrofit:
```kotlin
interface ApiService {
    @POST("auth/login")
    suspend fun login(@Body datos: LoginRequest): TokenResponse

    @GET("me")
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
| POST | `/auth/registro` | — | Crea una cuenta. Body: `{nombre, email, password, rol}`. Devuelve `{access_token, rol}` |
| POST | `/auth/inicio-sesion` | — | Inicia sesión. Body: `{email, password}`. Devuelve `{access_token, rol}` |
| GET | `/perfil` | cualquier usuario logueado | Devuelve los datos del usuario dueño del token |
| GET | `/medico/dashboard` | medico | Endpoint de ejemplo, solo accesible por médicos |
| GET | `/admin/usuarios` | admin | Lista todos los usuarios registrados |
| POST | `/sintomas` | paciente | Registra un síntoma. Body: `{descripcion}`. Devuelve `{id, descripcion}` |
| POST | `/documentos` | paciente | Sube un documento (PDF/JPG/PNG, máx 10MB). Body: `multipart/form-data` con el archivo en el campo `archivo`. Devuelve `{id, nombre_archivo, ruta_archivo}` |
| POST | `/metricas` | paciente | Registra una métrica de rango de movimiento. Body: `{articulacion, angulo_maximo, angulo_minimo}`. Devuelve `{id, articulacion, angulo_maximo, angulo_minimo}` |

> Este listado se irá actualizando a medida que se agreguen más endpoints. Revisa también `API_CONTRACT.md` para ver el diseño completo planeado, incluyendo lo que aún no está implementado.

## Roles válidos al registrarse

El campo `rol` en `/auth/register` acepta exactamente: `paciente`, `medico`, o `admin`.
