-- =====================================================================
-- ARCA Med - Guías clínicas de referencia (base de conocimiento del RAG)
--
-- Contenido redactado para fines académicos y de demostración, basado en
-- información general y pública de kinesiología y traumatología.
-- NO es material clínico validado ni reemplaza guías oficiales.
--
-- El embedding queda en NULL: se genera después con el script
--   python generar_embeddings_guias.py
-- (el SQL no puede llamar a la API de OpenAI).
--
-- Formato de cada guía: una sola condición, con secciones fijas.
-- La sección "Cómo suele describirlo el paciente" usa lenguaje cotidiano
-- para que la búsqueda semántica encuentre coincidencias con lo que
-- escriben los pacientes.
-- =====================================================================

INSERT INTO guias_clinicas (titulo, contenido) VALUES

-- ===================== TOBILLO Y PIE =====================
('Esguince de tobillo',
'Descripción: lesión de los ligamentos del tobillo, generalmente del ligamento lateral, por un movimiento de torsión. Se clasifica en grado I (distensión), grado II (rotura parcial) y grado III (rotura completa).
Síntomas característicos: dolor en la cara externa del tobillo, hinchazón, moretón que aparece en las horas siguientes y dificultad para apoyar el pie o caminar.
Cómo suele describirlo el paciente: "se me dobló el pie", "me torcí el tobillo jugando a la pelota", "pisé mal al bajar la escalera", "tengo el tobillo hinchado y morado".
Causas y mecanismo frecuentes: inversión forzada del pie al saltar, correr, cambiar de dirección o pisar una superficie irregular.
Signos de alarma: imposibilidad de dar cuatro pasos seguidos, dolor intenso al presionar el hueso (maléolos o base del quinto metatarsiano), deformidad visible o sensación de inestabilidad marcada.
Urgencia orientativa: baja en grado I; media en grado II o si hay mucha hinchazón; alta si hay signos de posible fractura.
Diagnósticos diferenciales: fractura de maléolo, fractura de la base del quinto metatarsiano, lesión de tendones peroneos, lesión de la sindesmosis.'),

('Tendinopatía aquiliana',
'Descripción: alteración dolorosa del tendón de Aquiles por sobrecarga repetida, frecuente en corredores y en personas que aumentan bruscamente su actividad.
Síntomas característicos: dolor y rigidez en la parte posterior del tobillo, sobre el tendón, peor al levantarse en la mañana o al iniciar la actividad. Puede notarse un engrosamiento del tendón.
Cómo suele describirlo el paciente: "me duele atrás del talón", "en la mañana camino tieso", "me duele el tendón cuando empiezo a correr y después se calienta".
Causas y mecanismo frecuentes: aumento rápido de kilometraje, cambio de calzado, correr en subidas, acortamiento de la musculatura de la pantorrilla.
Signos de alarma: chasquido o sensación de "patada" en el talón con dolor súbito e incapacidad para ponerse en punta de pie, que sugiere rotura del tendón.
Urgencia orientativa: baja si es progresivo; alta si hubo chasquido súbito con pérdida de fuerza.
Diagnósticos diferenciales: rotura del tendón de Aquiles, bursitis retrocalcánea, fascitis plantar, fractura por estrés del calcáneo.'),

('Fascitis plantar',
'Descripción: dolor por sobrecarga de la fascia plantar, la banda de tejido que va desde el talón hacia los dedos en la planta del pie.
Síntomas característicos: dolor punzante en la parte interna del talón, muy intenso con los primeros pasos de la mañana o después de estar sentado, que mejora al caminar un rato y empeora al final del día.
Cómo suele describirlo el paciente: "me duele la planta del pie al levantarme", "siento como un clavo en el talón", "los primeros pasos son terribles".
Causas y mecanismo frecuentes: estar mucho tiempo de pie, sobrepeso, calzado sin soporte, aumento de actividad, pie plano o cavo, rigidez de la pantorrilla.
Signos de alarma: hormigueo o adormecimiento en la planta, dolor nocturno en reposo, enrojecimiento y calor local.
Urgencia orientativa: baja.
Diagnósticos diferenciales: fractura por estrés del calcáneo, atrapamiento nervioso del talón, tendinopatía aquiliana, atrofia de la almohadilla grasa del talón.'),

-- ===================== RODILLA =====================
('Síndrome de dolor femoropatelar',
'Descripción: dolor alrededor o detrás de la rótula, asociado a sobrecarga de la articulación entre la rótula y el fémur. Es muy frecuente en personas jóvenes y deportistas.
Síntomas característicos: dolor difuso en la parte anterior de la rodilla que empeora al subir o bajar escaleras, al ponerse en cuclillas, al correr en bajada o al estar sentado mucho tiempo con la rodilla doblada.
Cómo suele describirlo el paciente: "me duele adelante de la rodilla", "no aguanto bajar escaleras", "en el cine me tengo que estirar la pierna", "me cruje la rodilla".
Causas y mecanismo frecuentes: aumento de carga de entrenamiento, debilidad de cuádriceps y de los músculos de la cadera, alteraciones en la alineación de la extremidad.
Signos de alarma: hinchazón importante, bloqueo de la rodilla, inestabilidad o dolor tras un golpe directo.
Urgencia orientativa: baja.
Diagnósticos diferenciales: tendinopatía rotuliana, lesión de cartílago, plica sinovial, lesión meniscal, inestabilidad de rótula.'),

('Lesión del ligamento cruzado anterior',
'Descripción: rotura parcial o total del ligamento cruzado anterior de la rodilla, que estabiliza la articulación frente a desplazamientos y giros.
Síntomas característicos: dolor intenso en el momento de la lesión, hinchazón rápida en las primeras horas y luego sensación de que la rodilla "se va" o falla al girar.
Cómo suele describirlo el paciente: "sentí un crujido cuando giré", "la rodilla se me salió y se hinchó al tiro", "no me puedo confiar de la rodilla al cambiar de dirección".
Causas y mecanismo frecuentes: giro con el pie apoyado, frenazo brusco o mala caída de un salto, típico en fútbol, básquetbol y esquí.
Signos de alarma: hinchazón importante en pocas horas, imposibilidad de apoyar, bloqueo de la rodilla.
Urgencia orientativa: media; alta si la rodilla está bloqueada o hay deformidad.
Diagnósticos diferenciales: lesión meniscal, lesión del ligamento colateral, luxación de rótula, fractura de meseta tibial.'),

('Lesión meniscal',
'Descripción: rotura del menisco, el cartílago que amortigua entre fémur y tibia. Puede ser traumática en jóvenes o degenerativa en mayores de 40 años.
Síntomas característicos: dolor en la línea de la articulación, interna o externa, al girar o ponerse en cuclillas, hinchazón que aparece en horas o días, chasquidos y a veces bloqueo de la rodilla.
Cómo suele describirlo el paciente: "me duele al costado de la rodilla cuando giro", "a veces la rodilla se me traba y no la puedo estirar", "no me puedo agachar".
Causas y mecanismo frecuentes: giro con la rodilla flectada y el pie fijo; en mayores, desgaste progresivo con gestos simples como levantarse de cuclillas.
Signos de alarma: rodilla bloqueada que no se puede extender completamente.
Urgencia orientativa: media; alta si existe bloqueo persistente.
Diagnósticos diferenciales: lesión de ligamento cruzado anterior, artrosis de rodilla, lesión de cartílago, bursitis de la pata de ganso.'),

('Artrosis de rodilla',
'Descripción: desgaste progresivo del cartílago articular de la rodilla, frecuente desde los 50 años y en personas con sobrepeso o lesiones previas.
Síntomas característicos: dolor mecánico que aumenta al caminar, subir escaleras o estar de pie y mejora con reposo; rigidez matinal breve, menor de 30 minutos; crujidos y, con el tiempo, deformidad o pérdida de movilidad.
Cómo suele describirlo el paciente: "me duelen las rodillas al caminar mucho", "en la mañana me cuesta arrancar", "me suenan las rodillas", "cada vez camino menos cuadras".
Causas y mecanismo frecuentes: edad, sobrepeso, lesiones previas de menisco o ligamentos, debilidad muscular, trabajos con carga.
Signos de alarma: rodilla roja, caliente y muy hinchada, fiebre, o dolor nocturno intenso que no cede con reposo.
Urgencia orientativa: baja; alta si hay signos de infección articular.
Diagnósticos diferenciales: lesión meniscal degenerativa, artritis inflamatoria, gota, bursitis.'),

-- ===================== CADERA =====================
('Bursitis trocantérea',
'Descripción: dolor en la cara lateral de la cadera por inflamación de la bursa y sobrecarga de los tendones de los glúteos sobre el trocánter mayor del fémur.
Síntomas característicos: dolor en el costado de la cadera, que puede bajar por el lado del muslo, peor al acostarse sobre ese lado, al subir escaleras o tras estar mucho tiempo de pie.
Cómo suele describirlo el paciente: "me duele el costado de la cadera", "no puedo dormir de ese lado", "me duele al cruzar las piernas".
Causas y mecanismo frecuentes: debilidad de glúteos, aumento de caminatas, diferencias de largo de piernas, sobrepeso; más frecuente en mujeres mayores de 40 años.
Signos de alarma: dolor en la ingle con cojera marcada, fiebre, o dolor tras una caída en persona mayor, que obliga a descartar fractura.
Urgencia orientativa: baja; alta tras una caída con imposibilidad de apoyar.
Diagnósticos diferenciales: artrosis de cadera, dolor lumbar irradiado, tendinopatía de glúteo medio, fractura de cadera.'),

-- ===================== COLUMNA =====================
('Lumbago mecánico agudo',
'Descripción: dolor en la zona baja de la espalda, sin compromiso de nervios, de origen muscular o articular. Es una de las consultas más frecuentes y en general mejora en pocas semanas.
Síntomas característicos: dolor en la parte baja de la espalda, a veces hacia los glúteos, que aumenta con ciertos movimientos y mejora con algunas posiciones; puede haber contractura y rigidez.
Cómo suele describirlo el paciente: "me agaché a levantar algo y quedé tomado", "me duele la espalda baja", "no me puedo enderezar", "tengo la espalda apretada".
Causas y mecanismo frecuentes: levantar peso con mala técnica, giro brusco, posturas mantenidas, sedentarismo.
Signos de alarma: pérdida de fuerza en las piernas, adormecimiento en la zona genital o entre las piernas, pérdida de control de orina o deposiciones, fiebre, baja de peso inexplicada, antecedente de cáncer o dolor tras un trauma importante.
Urgencia orientativa: baja; alta ante cualquier signo de alarma.
Diagnósticos diferenciales: lumbociática por hernia discal, fractura vertebral, dolor de origen renal, síndrome de cauda equina.'),

('Lumbociática por hernia discal',
'Descripción: dolor lumbar que se irradia por la pierna siguiendo el trayecto de un nervio, generalmente por una hernia del disco intervertebral que comprime una raíz nerviosa.
Síntomas característicos: dolor que baja por el glúteo y la parte posterior o lateral de la pierna, a veces hasta el pie; puede acompañarse de hormigueo, adormecimiento o debilidad. Suele empeorar al sentarse, toser o estornudar.
Cómo suele describirlo el paciente: "el dolor me baja por la pierna", "siento corriente hasta el pie", "se me duerme la pierna", "me duele más sentado".
Causas y mecanismo frecuentes: esfuerzos con flexión y giro del tronco, levantamiento de carga, degeneración del disco con la edad.
Signos de alarma: pérdida progresiva de fuerza en la pierna o pie caído, adormecimiento en la zona genital, pérdida de control de esfínteres.
Urgencia orientativa: media; alta ante déficit neurológico progresivo o compromiso de esfínteres.
Diagnósticos diferenciales: lumbago mecánico, síndrome piriforme, estenosis de canal lumbar, síndrome de cauda equina.'),

('Cervicalgia mecánica',
'Descripción: dolor en el cuello de origen muscular o articular, sin compromiso neurológico, muy relacionado con posturas mantenidas y tensión.
Síntomas característicos: dolor y rigidez en el cuello, a veces hacia los hombros o la parte alta de la espalda, con limitación para girar la cabeza; puede asociarse a dolor de cabeza.
Cómo suele describirlo el paciente: "tengo el cuello tieso", "me duele el cuello de estar en el computador", "amanecí con el cuello tomado", "no puedo girar la cabeza".
Causas y mecanismo frecuentes: posturas prolongadas frente a pantallas, mala posición al dormir, estrés, falta de actividad física.
Signos de alarma: dolor o adormecimiento que baja por el brazo con pérdida de fuerza, fiebre, mareos importantes, dolor tras un trauma.
Urgencia orientativa: baja.
Diagnósticos diferenciales: radiculopatía cervical, esguince cervical, cefalea tensional, patología de hombro con dolor referido.'),

('Esguince cervical (latigazo)',
'Descripción: lesión de los tejidos blandos del cuello producida por un movimiento brusco de aceleración y desaceleración, típico de los choques de vehículo por alcance.
Síntomas característicos: dolor y rigidez cervical que suelen aparecer horas después del accidente, dolor de cabeza en la nuca, dolor hacia los hombros y, a veces, mareo.
Cómo suele describirlo el paciente: "me chocaron por atrás y al otro día no podía mover el cuello", "me duele la nuca desde el choque".
Causas y mecanismo frecuentes: accidentes de tránsito, caídas, golpes en deportes de contacto.
Signos de alarma: dolor intenso en la línea media del cuello, adormecimiento o debilidad en brazos, pérdida de conciencia, alteración de la marcha. Ante estos signos se debe descartar fractura.
Urgencia orientativa: media; alta si hay signos neurológicos o trauma de alta energía.
Diagnósticos diferenciales: fractura cervical, radiculopatía cervical, cervicalgia mecánica, conmoción cerebral.'),

-- ===================== HOMBRO =====================
('Tendinopatía del manguito rotador',
'Descripción: dolor por sobrecarga de los tendones del manguito rotador del hombro, especialmente el supraespinoso, con frecuencia asociado a pinzamiento subacromial.
Síntomas característicos: dolor en la parte externa del hombro, que puede bajar hacia el brazo, al levantar el brazo de lado o por sobre la cabeza; dolor nocturno al acostarse sobre ese hombro.
Cómo suele describirlo el paciente: "me duele el hombro al levantar el brazo", "no puedo colgar ropa ni alcanzar cosas arriba", "en la noche me despierta el dolor del hombro".
Causas y mecanismo frecuentes: movimientos repetidos con el brazo en alto, deportes de lanzamiento o natación, trabajos sobre la cabeza, degeneración con la edad.
Signos de alarma: imposibilidad súbita de levantar el brazo tras una caída o esfuerzo, que sugiere rotura del tendón; deformidad tras un trauma.
Urgencia orientativa: baja; media si hay pérdida importante de fuerza.
Diagnósticos diferenciales: rotura del manguito rotador, capsulitis adhesiva, artrosis acromioclavicular, dolor cervical referido.'),

('Capsulitis adhesiva (hombro congelado)',
'Descripción: inflamación y retracción de la cápsula del hombro que produce dolor y una pérdida progresiva de la movilidad en todas las direcciones. Más frecuente entre los 40 y 60 años y en personas con diabetes.
Síntomas característicos: dolor difuso del hombro seguido de rigidez marcada; cuesta levantar el brazo, llevar la mano a la espalda o rotar el brazo hacia afuera, aunque se intente con ayuda.
Cómo suele describirlo el paciente: "no puedo subir el brazo ni con ayuda", "no alcanzo a abrocharme atrás", "el hombro se me fue poniendo cada vez más duro".
Causas y mecanismo frecuentes: a menudo sin causa clara; se asocia a diabetes, alteraciones de tiroides o a periodos de inmovilización del brazo.
Signos de alarma: fiebre, enrojecimiento articular o dolor tras un trauma con deformidad.
Urgencia orientativa: baja.
Diagnósticos diferenciales: tendinopatía del manguito rotador, artrosis glenohumeral, rotura del manguito rotador.'),

-- ===================== CODO Y MUÑECA =====================
('Epicondilitis lateral (codo de tenista)',
'Descripción: tendinopatía de los músculos extensores de la muñeca en su inserción en la cara externa del codo, por sobrecarga repetida.
Síntomas característicos: dolor en la parte externa del codo que aumenta al tomar objetos, apretar, girar una manilla o levantar algo con la palma hacia abajo; puede bajar hacia el antebrazo.
Cómo suele describirlo el paciente: "me duele el codo por fuera cuando agarro la taza", "me duele al usar el mouse", "no puedo exprimir un paño".
Causas y mecanismo frecuentes: trabajos manuales repetitivos, uso intensivo de teclado y mouse, deportes de raqueta, herramientas.
Signos de alarma: hinchazón importante, bloqueo del codo, adormecimiento o debilidad en la mano.
Urgencia orientativa: baja.
Diagnósticos diferenciales: atrapamiento del nervio radial, radiculopatía cervical, artrosis del codo.'),

('Síndrome del túnel carpiano',
'Descripción: compresión del nervio mediano en la muñeca, dentro del túnel carpiano.
Síntomas característicos: hormigueo, adormecimiento y dolor en los dedos pulgar, índice y medio, típicamente de noche o al mantener la muñeca doblada; con el tiempo, torpeza y pérdida de fuerza para tomar objetos finos.
Cómo suele describirlo el paciente: "se me duermen las manos en la noche", "despierto y tengo que sacudir la mano", "se me caen las cosas", "siento corriente en los dedos".
Causas y mecanismo frecuentes: movimientos repetitivos de muñeca, uso de herramientas que vibran, embarazo, diabetes, alteraciones de tiroides.
Signos de alarma: debilidad progresiva o pérdida de masa muscular en la base del pulgar, adormecimiento permanente.
Urgencia orientativa: baja; media si hay debilidad progresiva.
Diagnósticos diferenciales: radiculopatía cervical, tendinitis de De Quervain, artrosis de la base del pulgar, compresión del nervio cubital.');
