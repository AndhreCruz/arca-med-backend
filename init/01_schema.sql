-- Extensión de pgvector
CREATE EXTENSION IF NOT EXISTS vector;


-- Tabla de usuarios (paciente, médico, admin)
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('paciente', 'medico', 'admin')),
    creado_en TIMESTAMP DEFAULT NOW(),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_nacimiento DATE,
    sexo VARCHAR(20) CHECK (sexo IN ('femenino', 'masculino', 'otro', 'prefiero_no_decir')),
    telefono BYTEA,
    foto BYTEA,
    foto_version VARCHAR(8)
);


-- Síntomas ingresados por el paciente (texto libre)
CREATE TABLE sintomas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    descripcion BYTEA NOT NULL,
    creado_en TIMESTAMP DEFAULT NOW()
);


-- Documentos subidos (PDF, imágenes)
CREATE TABLE documentos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    nombre_archivo BYTEA NOT NULL,
    contenido BYTEA NOT NULL,
    tipo_archivo VARCHAR(50),
    subido_en TIMESTAMP DEFAULT NOW()
);


-- Métricas físicas (rango de movimiento articular, capturado por la app)
CREATE TABLE metricas_fisicas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    articulacion VARCHAR(50) NOT NULL,
    lado VARCHAR(10),
    angulo_maximo NUMERIC(5,2),
    angulo_minimo NUMERIC(5,2),
    medido_en TIMESTAMP DEFAULT NOW()
);


-- Guías clínicas (para el RAG)
CREATE TABLE guias_clinicas (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    contenido TEXT NOT NULL,
    embedding VECTOR(1536),
    creado_en TIMESTAMP DEFAULT NOW()
);


-- Resultado del pipeline RAG
CREATE TABLE prediagnosticos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    resumen_generado BYTEA NOT NULL,
    urgencia_sugerida VARCHAR(20) CHECK (urgencia_sugerida IN ('baja', 'media', 'alta')),
    diagnosticos_diferenciales JSONB,
    revisado_por_medico BOOLEAN DEFAULT FALSE,
    creado_en TIMESTAMP DEFAULT NOW()
);


-- Catálogo de ejercicios
CREATE TABLE ejercicios_recomendados (
    id SERIAL PRIMARY KEY,
    nombre_ejercicio VARCHAR(150) NOT NULL,
    descripcion TEXT,
    articulacion VARCHAR(50),
    imagen_url VARCHAR(500),
    imagen BYTEA,
    imagen_tipo VARCHAR(50),
    creado_en TIMESTAMP DEFAULT NOW()
);


-- Feedback de cómo el paciente ejecutó el ejercicio
CREATE TABLE ejecuciones_ejercicio (
    id SERIAL PRIMARY KEY,
    ejercicio_id INTEGER REFERENCES ejercicios_recomendados(id),
    usuario_id INTEGER REFERENCES usuarios(id),
    correcto BOOLEAN,
    comentario BYTEA,
    ejecutado_en TIMESTAMP DEFAULT NOW()
);


-- Auditoria
CREATE TABLE auditoria_logs (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    rol VARCHAR(20) NOT NULL,
    accion VARCHAR(50) NOT NULL,
    usuario_afectado_id INTEGER REFERENCES usuarios(id),
    detalle TEXT,
    ip VARCHAR(45),
    fecha TIMESTAMPTZ NOT NULL,
    hash_anterior CHAR(64) NOT NULL,
    hash CHAR(64) NOT NULL
);


CREATE INDEX idx_auditoria_usuario ON auditoria_logs(usuario_id);
CREATE INDEX idx_auditoria_afectado ON auditoria_logs(usuario_afectado_id);

CREATE OR REPLACE FUNCTION impedir_modificacion_auditoria() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Los registros de auditoria no se pueden modificar ni borrar';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auditoria_inmutable
BEFORE UPDATE OR DELETE ON auditoria_logs
FOR EACH ROW EXECUTE FUNCTION impedir_modificacion_auditoria();

CREATE TRIGGER auditoria_sin_truncate
BEFORE TRUNCATE ON auditoria_logs
FOR EACH STATEMENT EXECUTE FUNCTION impedir_modificacion_auditoria();


CREATE TABLE citas (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES usuarios(id),
    medico_id INTEGER NOT NULL REFERENCES usuarios(id),
    fecha_hora TIMESTAMPTZ NOT NULL,
    duracion_minutos INTEGER NOT NULL DEFAULT 30 CHECK (duracion_minutos BETWEEN 10 AND 180),
    motivo TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'programada'
        CHECK (estado IN ('programada', 'completada', 'cancelada')),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_citas_medico_fecha ON citas(medico_id, fecha_hora);
CREATE INDEX idx_citas_paciente ON citas(paciente_id);