-- =====================================================================
-- ARCA Med - Usuarios de prueba
-- Contraseña de TODOS los usuarios: Arcamed2026
-- (se guarda solo el hash bcrypt, nunca la contraseña en texto plano)
-- Solo para desarrollo local: no usar estas cuentas en un entorno real.
-- =====================================================================

INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES
-- Administradores
('Administrador ARCA', 'admin@arcamed.com',   '$2b$12$dBtX94rqPFiQolN2KwnvGuAMkpUDAkWoJSczF72aVSSkAk/R02l/2', 'admin'),
('Soporte ARCA',       'soporte@arcamed.com', '$2b$12$dBtX94rqPFiQolN2KwnvGuAMkpUDAkWoJSczF72aVSSkAk/R02l/2', 'admin'),

-- Médicos
('Camila Rojas',    'camila.rojas@arcamed.com',    '$2b$12$dBtX94rqPFiQolN2KwnvGuAMkpUDAkWoJSczF72aVSSkAk/R02l/2', 'medico'),
('Matías Fuentes',  'matias.fuentes@arcamed.com',  '$2b$12$dBtX94rqPFiQolN2KwnvGuAMkpUDAkWoJSczF72aVSSkAk/R02l/2', 'medico'),
('Valentina Soto',  'valentina.soto@arcamed.com',  '$2b$12$dBtX94rqPFiQolN2KwnvGuAMkpUDAkWoJSczF72aVSSkAk/R02l/2', 'medico'),

-- Pacientes
('Juan Pérez',        'juan.perez@arcamed.com',        '$2b$12$dBtX94rqPFiQolN2KwnvGuAMkpUDAkWoJSczF72aVSSkAk/R02l/2', 'paciente'),
('María González',    'maria.gonzalez@arcamed.com',    '$2b$12$dBtX94rqPFiQolN2KwnvGuAMkpUDAkWoJSczF72aVSSkAk/R02l/2', 'paciente'),
('Diego Muñoz',       'diego.munoz@arcamed.com',       '$2b$12$dBtX94rqPFiQolN2KwnvGuAMkpUDAkWoJSczF72aVSSkAk/R02l/2', 'paciente'),
('Fernanda Silva',    'fernanda.silva@arcamed.com',    '$2b$12$dBtX94rqPFiQolN2KwnvGuAMkpUDAkWoJSczF72aVSSkAk/R02l/2', 'paciente'),
('Tomás Contreras',   'tomas.contreras@arcamed.com',   '$2b$12$dBtX94rqPFiQolN2KwnvGuAMkpUDAkWoJSczF72aVSSkAk/R02l/2', 'paciente')
ON CONFLICT (email) DO NOTHING;
