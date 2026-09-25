# Contrato de API — ARCA Med

## Autenticación (público)

### POST /auth/registro
Body: { "nombre": string, "email": string, "password": string, "rol": "paciente"|"medico"|"admin" }
Devuelve: { "id": int, "token": string }

### POST /auth/inicio-sesion
Body: { "email": string, "password": string }
Devuelve: { "token": string, "rol": string }

---

## Paciente (requiere token, rol: paciente)

### POST /sintomas
Body: { "descripcion": string }
Devuelve: { "id": int, "creado_en": datetime }

### POST /documentos
Body: multipart/form-data (archivo PDF/JPG/PNG, máx 10MB)
Devuelve: { "id": int, "nombre_archivo": string, "ruta_archivo": string }

### POST /metricas
Body: { "articulacion": string, "angulo_maximo": float, "angulo_minimo": float }
Devuelve: { "id": int }

### GET /ejercicios
Devuelve: [ { "id": int, "nombre_ejercicio": string, "descripcion": string } ]

### POST /ejercicios/{id}/ejecucion
Body: { "correcto": bool, "comentario": string }
Devuelve: { "id": int }

---

## Médico (requiere token, rol: medico)

### GET /pacientes/triage
Devuelve: [ { "usuario_id": int, "nombre": string, "urgencia_sugerida": "baja"|"media"|"alta" } ]
Ordenado por urgencia descendente.

### GET /pacientes/{id}/resumen
Devuelve: {
  "resumen_generado": string,
  "diagnosticos_diferenciales": [string],
  "urgencia_sugerida": string,
  "metricas_fisicas": [ { "articulacion": string, "angulo_maximo": float, "angulo_minimo": float } ]
}

### POST /pacientes/{id}/resumen/revisar
Body: { "revisado_por_medico": true }
Devuelve: { "id": int, "revisado_por_medico": bool }

---

## Admin (requiere token, rol: admin)

### GET /usuarios
Devuelve: [ { "id": int, "nombre": string, "email": string, "rol": string } ]

### POST /guias-clinicas
Body: { "titulo": string, "contenido": string }
Devuelve: { "id": int }
(El embedding se genera automático en el backend, no lo manda el cliente)

### GET /auditoria/logs
Devuelve: [ { "usuario_id": int, "accion": string, "fecha": datetime } ]