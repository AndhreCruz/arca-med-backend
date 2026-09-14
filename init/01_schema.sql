-- Extensión de pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de usuarios (paciente, médico, admin)
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('paciente', 'medico', 'admin')),
    creado_en TIMESTAMP DEFAULT NOW()
);

-- Síntomas ingresados por el paciente (texto libre)
CREATE TABLE sintomas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    descripcion TEXT NOT NULL,
    creado_en TIMESTAMP DEFAULT NOW()
);

-- Documentos subidos (PDF, imágenes)
CREATE TABLE documentos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    nombre_archivo VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(500) NOT NULL,
    tipo_archivo VARCHAR(50),
    subido_en TIMESTAMP DEFAULT NOW()
);

-- Métricas físicas (rango de movimiento articular, capturado por la app)
CREATE TABLE metricas_fisicas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    articulacion VARCHAR(50) NOT NULL,
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
    resumen_generado TEXT NOT NULL,
    urgencia_sugerida VARCHAR(20) CHECK (urgencia_sugerida IN ('baja', 'media', 'alta')),
    diagnosticos_diferenciales JSONB,
    revisado_por_medico BOOLEAN DEFAULT FALSE,
    creado_en TIMESTAMP DEFAULT NOW()
);

-- Ejercicios sugeridos al paciente
CREATE TABLE ejercicios_recomendados (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    nombre_ejercicio VARCHAR(150) NOT NULL,
    descripcion TEXT,
    creado_en TIMESTAMP DEFAULT NOW()
);

-- Feedback de cómo el paciente ejecutó el ejercicio
CREATE TABLE ejecuciones_ejercicio (
    id SERIAL PRIMARY KEY,
    ejercicio_id INTEGER REFERENCES ejercicios_recomendados(id),
    usuario_id INTEGER REFERENCES usuarios(id),
    correcto BOOLEAN,
    comentario TEXT,
    ejecutado_en TIMESTAMP DEFAULT NOW()
);