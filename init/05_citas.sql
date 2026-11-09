-- Citas de prueba. Las fechas se calculan desde el día en que se levanta la base,
-- para que el calendario siempre tenga citas próximas. Horas en hora de Chile.
WITH base AS (
    SELECT date_trunc('day', NOW() AT TIME ZONE 'America/Santiago') AS hoy
)
INSERT INTO citas (paciente_id, medico_id, fecha_hora, duracion_minutos, motivo, estado)
SELECT p.id, m.id, (base.hoy + c.desfase) AT TIME ZONE 'America/Santiago', c.duracion, c.motivo, c.estado
FROM base,
(VALUES
    ('juan.perez@arcamed.com',      'camila.rojas@arcamed.com',   INTERVAL '1 day 09:00',   30, 'Primera consulta',            'programada'),
    ('maria.gonzalez@arcamed.com',  'camila.rojas@arcamed.com',   INTERVAL '1 day 10:00',   30, 'Control',                     'programada'),
    ('diego.munoz@arcamed.com',     'camila.rojas@arcamed.com',   INTERVAL '2 days 11:30',  45, 'Evaluación de movilidad',     'programada'),
    ('fernanda.silva@arcamed.com',  'camila.rojas@arcamed.com',   INTERVAL '3 days 15:00',  30, 'Primera consulta',            'programada'),
    ('tomas.contreras@arcamed.com', 'camila.rojas@arcamed.com',   INTERVAL '5 days 09:30',  30, NULL,                          'programada'),
    ('juan.perez@arcamed.com',      'matias.fuentes@arcamed.com', INTERVAL '2 days 16:00',  30, 'Evaluación de movilidad',     'programada'),
    ('maria.gonzalez@arcamed.com',  'valentina.soto@arcamed.com', INTERVAL '4 days 12:00',  30, 'Revisión de exámenes',        'programada'),
    ('fernanda.silva@arcamed.com',  'matias.fuentes@arcamed.com', INTERVAL '1 day 17:00',   30, 'Control',                     'cancelada'),
    ('diego.munoz@arcamed.com',     'camila.rojas@arcamed.com',   INTERVAL '-3 days 10:00', 30, 'Primera consulta',            'completada')
) AS c(paciente_email, medico_email, desfase, duracion, motivo, estado)
JOIN usuarios p ON p.email = c.paciente_email
JOIN usuarios m ON m.email = c.medico_email;