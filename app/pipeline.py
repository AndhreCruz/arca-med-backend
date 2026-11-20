import logging

from database import SessionLocal
from models import Cita, MetricaFisica, Prediagnostico, Sintoma
from anonimizar import anonimizar_texto
from embeddings import buscar_guias_relevantes
from llm import generar_prediagnostico

logger = logging.getLogger("arcamed.pipeline")


def generar_prediagnostico_en_segundo_plano(usuario_id: int, descripcion: str) -> None:
    """
    Flujo antiguo (POST /sintomas, sin cita). Se mantiene mientras la app migra.
    Abre su propia sesion de base de datos: la del endpoint ya esta cerrada.
    """
    db = SessionLocal()
    try:
        texto_seguro = anonimizar_texto(descripcion)
        guias = buscar_guias_relevantes(texto_seguro, db)
        resultado = generar_prediagnostico(f"Síntomas del paciente: {texto_seguro}",
                                           [g.contenido for g in guias])

        db.add(Prediagnostico(
            usuario_id=usuario_id,
            resumen_generado=resultado["resumen"],
            urgencia_sugerida=resultado["urgencia_sugerida"],
            diagnosticos_diferenciales=resultado["diagnosticos_diferenciales"],
        ))
        db.commit()
        logger.info("Prediagnostico generado para usuario %s", usuario_id)
    except Exception:
        db.rollback()
        logger.exception("Error generando prediagnostico para usuario %s", usuario_id)
    finally:
        db.close()


def _armar_caso(cita: Cita, sintoma: Sintoma, texto_seguro: str, metricas: list[MetricaFisica]) -> str:
    """Arma el texto con todo el contexto de la pre-consulta que recibe la IA."""
    lineas = [f"Especialidad de la consulta: {cita.especialidad_nombre}"]

    articulacion = sintoma.articulacion + (f" (lado {sintoma.lado})" if sintoma.lado else "")
    lineas.append(f"Articulación indicada por el paciente: {articulacion}")

    paciente = cita.paciente
    datos_paciente = []
    if paciente.edad is not None:
        datos_paciente.append(f"{paciente.edad} años")
    if paciente.sexo in ("femenino", "masculino", "otro"):
        datos_paciente.append(f"sexo {paciente.sexo}")
    if datos_paciente:
        lineas.append("Paciente: " + ", ".join(datos_paciente))

    lineas.append(f"Síntomas descritos por el paciente: {texto_seguro}")

    if metricas:
        lineas.append("Evaluación articular por cámara (grados):")
        for m in metricas:
            lado = f" {m.lado}" if m.lado else ""
            lineas.append(f"- {m.articulacion}{lado}: ángulo máximo {m.angulo_maximo:.0f}°, "
                          f"ángulo mínimo {m.angulo_minimo:.0f}°")
    else:
        lineas.append("Evaluación articular por cámara: no realizada.")

    return "\n".join(lineas)


def generar_prediagnostico_cita_en_segundo_plano(cita_id: int) -> None:
    """
    Flujo nuevo: corre al enviar la pre-consulta de una cita.
    Usa la especialidad, la articulación, el lado, la edad y el sexo, los síntomas
    y las métricas que existan en ese momento.
    """
    db = SessionLocal()
    try:
        cita = db.query(Cita).filter(Cita.id == cita_id).first()
        sintoma = db.query(Sintoma).filter(Sintoma.cita_id == cita_id).first()
        if cita is None or sintoma is None:
            logger.warning("Cita %s sin datos para generar prediagnostico", cita_id)
            return

        metricas = (
            db.query(MetricaFisica)
            .filter(MetricaFisica.cita_id == cita_id)
            .order_by(MetricaFisica.id)
            .all()
        )

        texto_seguro = anonimizar_texto(sintoma.descripcion)
        caso = _armar_caso(cita, sintoma, texto_seguro, metricas)

        # La búsqueda de guías también usa la especialidad y la articulación, no solo el texto
        consulta_guias = f"{cita.especialidad_nombre}. {sintoma.articulacion}. {texto_seguro}"
        guias = buscar_guias_relevantes(consulta_guias, db)

        resultado = generar_prediagnostico(caso, [g.contenido for g in guias])

        db.add(Prediagnostico(
            usuario_id=cita.paciente_id,
            cita_id=cita.id,
            resumen_generado=resultado["resumen"],
            urgencia_sugerida=resultado["urgencia_sugerida"],
            diagnosticos_diferenciales=resultado["diagnosticos_diferenciales"],
        ))
        db.commit()
        logger.info("Prediagnostico generado para cita %s", cita_id)
    except Exception:
        db.rollback()
        logger.exception("Error generando prediagnostico para cita %s", cita_id)
    finally:
        db.close()