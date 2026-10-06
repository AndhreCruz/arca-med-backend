-- =====================================================================
-- ARCA Med - Catálogo de ejercicios
--
-- Ejercicios generales de movilidad y fortalecimiento, redactados para
-- fines académicos y de demostración. No reemplazan la indicación de un
-- profesional. La app debería mostrar un aviso indicando que, si un
-- ejercicio produce dolor intenso, el paciente debe detenerse.
--
-- Formato de cada descripción:
--   Posición inicial / Ejecución / Dosificación / Precaución
-- La articulación usa los mismos valores que constantes.py (sin lado):
-- rodilla, tobillo, hombro, codo, muneca, cadera, cervical, lumbar.
-- imagen_url queda en NULL: se completa con POST /ejercicios/{id}/imagen.
-- =====================================================================

INSERT INTO ejercicios_recomendados (nombre_ejercicio, articulacion, descripcion) VALUES

-- ===================== RODILLA =====================
('Elevación de pierna recta', 'rodilla',
'Posición inicial: acostado boca arriba, con una rodilla doblada y el pie apoyado en el suelo; la otra pierna estirada.
Ejecución: contrae el muslo de la pierna estirada y elévala hasta la altura de la rodilla contraria. Mantén 3 segundos y baja lentamente.
Dosificación: 3 series de 10 repeticiones.
Precaución: mantén la zona lumbar apoyada en el suelo, sin arquear la espalda.'),

('Sentadilla parcial con apoyo', 'rodilla',
'Posición inicial: de pie, frente a una silla o mesa estable, pies separados al ancho de caderas.
Ejecución: flexiona las rodillas llevando la cadera hacia atrás, como si fueras a sentarte, hasta un ángulo cómodo. Vuelve a subir de forma controlada.
Dosificación: 3 series de 10 repeticiones.
Precaución: las rodillas deben apuntar en la misma dirección que los pies, sin irse hacia adentro. No bajes más allá del punto de molestia.'),

('Extensión de rodilla sentado', 'rodilla',
'Posición inicial: sentado en una silla, espalda apoyada y pies en el suelo.
Ejecución: estira completamente una rodilla hasta dejar la pierna recta, mantén 5 segundos y baja lentamente.
Dosificación: 3 series de 12 repeticiones por pierna.
Precaución: realiza el movimiento sin impulso. Puedes añadir una tobillera liviana cuando sea fácil.'),

('Puente de glúteos', 'rodilla',
'Posición inicial: acostado boca arriba, rodillas dobladas y pies apoyados al ancho de caderas.
Ejecución: eleva la cadera apretando los glúteos hasta formar una línea recta entre hombros y rodillas. Mantén 3 segundos y baja.
Dosificación: 3 series de 12 repeticiones.
Precaución: no arquees en exceso la zona lumbar; el esfuerzo debe sentirse en glúteos y parte posterior del muslo.'),

-- ===================== TOBILLO =====================
('Alfabeto con el tobillo', 'tobillo',
'Posición inicial: sentado, con la pierna estirada y el pie en el aire.
Ejecución: dibuja con la punta del pie las letras del abecedario, moviendo solo el tobillo.
Dosificación: 1 o 2 abecedarios completos, 2 veces al día.
Precaución: movimientos lentos y dentro de un rango sin dolor.'),

('Elevación de talones', 'tobillo',
'Posición inicial: de pie, frente a una pared o silla para apoyarte, pies al ancho de caderas.
Ejecución: sube lentamente a punta de pies, mantén 2 segundos y baja de forma controlada.
Dosificación: 3 series de 15 repeticiones.
Precaución: cuando sea fácil con dos pies, progresa a un solo pie.'),

('Equilibrio en un pie', 'tobillo',
'Posición inicial: de pie junto a una superficie estable para sujetarte si es necesario.
Ejecución: levanta un pie y mantén el equilibrio sobre el otro, con la rodilla levemente flexionada.
Dosificación: 3 repeticiones de 30 segundos por pierna.
Precaución: aumenta la dificultad cerrando los ojos o usando un cojín solo cuando el ejercicio sea estable.'),

('Eversión con banda elástica', 'tobillo',
'Posición inicial: sentado con la pierna estirada y una banda elástica rodeando la parte externa del pie, fijada a un punto del lado contrario.
Ejecución: lleva la planta del pie hacia afuera contra la resistencia de la banda y vuelve lentamente.
Dosificación: 3 series de 12 repeticiones.
Precaución: mueve solo el tobillo, sin girar la pierna completa.'),

-- ===================== HOMBRO =====================
('Péndulo de Codman', 'hombro',
'Posición inicial: inclinado hacia adelante, apoyando la mano sana en una mesa y dejando colgar el brazo afectado relajado.
Ejecución: balancea el cuerpo suavemente para que el brazo dibuje pequeños círculos, sin usar la fuerza del hombro.
Dosificación: 1 minuto en cada sentido, 2 o 3 veces al día.
Precaución: el brazo debe estar completamente relajado; el movimiento lo genera el cuerpo.'),

('Rotación externa con banda elástica', 'hombro',
'Posición inicial: de pie, codo pegado al cuerpo y doblado en 90 grados, sosteniendo una banda elástica fijada a la altura del codo.
Ejecución: gira el antebrazo hacia afuera manteniendo el codo pegado al costado, y vuelve lentamente.
Dosificación: 3 series de 12 repeticiones.
Precaución: puedes poner una toalla enrollada entre el codo y el cuerpo para mantener la posición.'),

('Deslizamiento en pared', 'hombro',
'Posición inicial: de pie frente a una pared, con la mano del brazo afectado apoyada en ella a la altura del pecho.
Ejecución: desliza la mano hacia arriba por la pared lo más alto que puedas sin dolor intenso, mantén 5 segundos y baja.
Dosificación: 2 series de 10 repeticiones.
Precaución: no eleves el hombro hacia la oreja; mantenlo relajado.'),

('Retracción escapular', 'hombro',
'Posición inicial: sentado o de pie, espalda recta y brazos relajados al costado.
Ejecución: junta las escápulas hacia atrás y abajo, como si quisieras guardarlas en los bolsillos traseros. Mantén 5 segundos y relaja.
Dosificación: 3 series de 10 repeticiones.
Precaución: evita encoger los hombros o arquear la espalda.'),

-- ===================== CODO =====================
('Flexo-extensión de codo', 'codo',
'Posición inicial: sentado o de pie, brazo al costado del cuerpo.
Ejecución: dobla el codo llevando la mano hacia el hombro y luego estíralo completamente.
Dosificación: 2 series de 15 repeticiones.
Precaución: movimiento lento y completo, sin forzar el final del recorrido.'),

('Pronosupinación con martillo', 'codo',
'Posición inicial: sentado, antebrazo apoyado en una mesa con la muñeca por fuera del borde, sosteniendo un martillo o una botella por su extremo.
Ejecución: gira lentamente el antebrazo para que la palma mire hacia arriba y luego hacia abajo.
Dosificación: 3 series de 10 repeticiones.
Precaución: si molesta, sujeta el objeto más cerca de la mano para reducir la carga.'),

('Estiramiento de extensores de muñeca', 'codo',
'Posición inicial: de pie o sentado, con el brazo estirado al frente y la palma hacia abajo.
Ejecución: con la otra mano, flexiona suavemente la muñeca hacia abajo hasta sentir estiramiento en la parte superior del antebrazo.
Dosificación: 3 repeticiones de 30 segundos.
Precaución: debe sentirse estiramiento, no dolor punzante en el codo.'),

-- ===================== MUÑECA =====================
('Flexión y extensión de muñeca', 'muneca',
'Posición inicial: sentado, antebrazo apoyado en una mesa con la mano por fuera del borde.
Ejecución: mueve la mano hacia arriba y hacia abajo lentamente, solo desde la muñeca.
Dosificación: 2 series de 15 repeticiones.
Precaución: cuando sea fácil, añade una botella pequeña de agua como peso.'),

('Deslizamiento de tendones', 'muneca',
'Posición inicial: sentado, codo apoyado y mano hacia arriba con los dedos estirados.
Ejecución: pasa por estas posiciones manteniendo 3 segundos cada una: dedos estirados, puño en gancho, puño completo, mano en mesa y puño recto.
Dosificación: 5 secuencias completas, 3 veces al día.
Precaución: movimientos suaves; si aparece hormigueo intenso, detente.'),

('Apretar pelota blanda', 'muneca',
'Posición inicial: sentado, con una pelota blanda o de goma espuma en la mano.
Ejecución: aprieta la pelota con toda la mano, mantén 3 segundos y suelta lentamente.
Dosificación: 3 series de 10 repeticiones.
Precaución: no apretar al punto de provocar dolor en la muñeca o el codo.'),

-- ===================== CADERA =====================
('Abducción de cadera de lado', 'cadera',
'Posición inicial: acostado de lado, piernas estiradas y alineadas con el cuerpo, la pierna de abajo puede estar levemente doblada.
Ejecución: eleva la pierna de arriba manteniéndola estirada y con la punta del pie mirando al frente. Mantén 2 segundos y baja.
Dosificación: 3 series de 12 repeticiones por lado.
Precaución: no gires la cadera hacia atrás; el movimiento es corto y controlado.'),

('Almeja', 'cadera',
'Posición inicial: acostado de lado, caderas y rodillas dobladas, talones juntos.
Ejecución: separa las rodillas elevando la de arriba, manteniendo los talones en contacto, y baja lentamente.
Dosificación: 3 series de 15 repeticiones por lado.
Precaución: la pelvis no debe rotar hacia atrás durante el movimiento.'),

('Estiramiento de flexores de cadera', 'cadera',
'Posición inicial: arrodillado sobre una rodilla, con el otro pie apoyado adelante y una almohada bajo la rodilla.
Ejecución: lleva la pelvis suavemente hacia adelante manteniendo el tronco recto, hasta sentir estiramiento en la parte delantera de la cadera de atrás.
Dosificación: 3 repeticiones de 30 segundos por lado.
Precaución: no arquees la espalda baja para ganar recorrido.'),

('Marcha estática', 'cadera',
'Posición inicial: de pie junto a una pared o silla para apoyarte.
Ejecución: eleva alternadamente una rodilla hacia el pecho, como si marcharas en el lugar, manteniendo el tronco erguido.
Dosificación: 3 series de 20 pasos en total.
Precaución: realiza el movimiento lento y controlado, sin balancear el tronco.'),

-- ===================== CERVICAL =====================
('Retracción cervical', 'cervical',
'Posición inicial: sentado con la espalda recta, mirando al frente.
Ejecución: lleva el mentón hacia atrás, como haciendo una papada, sin inclinar la cabeza hacia abajo. Mantén 5 segundos y relaja.
Dosificación: 3 series de 10 repeticiones.
Precaución: la mirada se mantiene horizontal durante todo el ejercicio.'),

('Rotación cervical activa', 'cervical',
'Posición inicial: sentado con la espalda recta y los hombros relajados.
Ejecución: gira lentamente la cabeza hacia un lado hasta donde sea cómodo, vuelve al centro y repite hacia el otro lado.
Dosificación: 2 series de 10 repeticiones por lado.
Precaución: si aparece mareo, hormigueo en los brazos o dolor intenso, detente.'),

('Estiramiento del trapecio superior', 'cervical',
'Posición inicial: sentado, sujetando el borde de la silla con una mano.
Ejecución: inclina la cabeza hacia el lado contrario llevando la oreja hacia el hombro, hasta sentir estiramiento en el lado del cuello. Puedes ayudarte suavemente con la otra mano.
Dosificación: 3 repeticiones de 30 segundos por lado.
Precaución: estiramiento suave, sin tirones.'),

-- ===================== LUMBAR =====================
('Gato y camello', 'lumbar',
'Posición inicial: en cuatro apoyos, manos bajo los hombros y rodillas bajo las caderas.
Ejecución: redondea la espalda llevando el ombligo hacia arriba y luego arquéala suavemente mirando al frente. Alterna de forma lenta.
Dosificación: 2 series de 10 repeticiones.
Precaución: el movimiento debe ser fluido y dentro de un rango sin dolor.'),

('Rodillas al pecho', 'lumbar',
'Posición inicial: acostado boca arriba con las rodillas dobladas.
Ejecución: lleva una rodilla hacia el pecho sujetándola con las manos, mantén 20 segundos, baja y repite con la otra. Luego ambas juntas.
Dosificación: 3 repeticiones por lado.
Precaución: si el dolor baja por la pierna al hacerlo, detén el ejercicio.'),

('Bird dog (pájaro-perro)', 'lumbar',
'Posición inicial: en cuatro apoyos, espalda neutra.
Ejecución: estira un brazo al frente y la pierna contraria hacia atrás, manteniendo la pelvis estable. Mantén 3 segundos y cambia de lado.
Dosificación: 3 series de 8 repeticiones por lado.
Precaución: evita que la espalda se hunda o la pelvis rote.'),

('Plancha abdominal en rodillas', 'lumbar',
'Posición inicial: boca abajo, apoyado en antebrazos y rodillas.
Ejecución: eleva la cadera hasta formar una línea recta entre hombros y rodillas, contrayendo el abdomen. Mantén la posición.
Dosificación: 3 repeticiones de 20 a 30 segundos.
Precaución: no levantes demasiado la cadera ni dejes caer la zona lumbar.');
