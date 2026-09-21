# ARCA Med — Backend

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

Guardar el token después del login (ej. en `localStorage`https://github.com/AndhreCruz/arca-med-backend.git):
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

### Qué pasa si el token falta o es inválido

La API responde:
- `401 Unauthorized` → no se mandó token, o es inválido/expiró → hay que loguear de nuevo.
- `403 Forbidden` → el token es válido, pero el rol del usuario no tiene permiso para ese endpoint específico (ej. un paciente llamando a un endpoint solo de médico).

## Endpoints disponibles actualmente

| Método | Ruta | Rol requerido | Descripción |
|---|---|---|---|
| GET | `/health` | — | Confirma que el servidor está corriendo |
| GET | `/health/db` | — | Confirma que el servidor está conectado a la base de datos |
| POST | `/auth/register` | — | Crea una cuenta. Body: `{nombre, email, password, rol}`. Devuelve `{access_token, rol}` |
| POST | `/auth/login` | — | Inicia sesión. Body: `{email, password}`. Devuelve `{access_token, rol}` |
| GET | `/me` | cualquier usuario logueado | Devuelve los datos del usuario dueño del token |
| GET | `/medico/dashboard` | medico | Endpoint de ejemplo, solo accesible por médicos |
| GET | `/admin/usuarios` | admin | Lista todos los usuarios registrados |

> Este listado se irá actualizando a medida que se agreguen más endpoints (síntomas, documentos, etc.). Revisa también `API_CONTRACT.md` para ver el diseño completo planeado, incluyendo lo que aún no está implementado.

## Roles válidos al registrarse

El campo `rol` en `/auth/register` acepta exactamente: `paciente`, `medico`, o `admin`.
