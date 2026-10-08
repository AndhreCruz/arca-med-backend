import logging

from database import SessionLocal
from models import Prediagnostico
from anonimizar import anonimizar_texto
from embeddings import buscar_guias_relevantes
from llm import generar_prediagnostico

logger = logging.getLogger("arcamed.pipeline")


def generar_prediagnostico_en_segundo_plano(usuario_id: int, descripcion: str) -> None:
    """
    Corre despues de que POST /sintomas ya respondio al paciente.
    Abre su propia sesion de base de datos: la del endpoint ya esta cerrada.
    """
    db = SessionLocal()
    try:
        texto_seguro = anonimizar_texto(descripcion)
        guias = buscar_guias_relevantes(texto_seguro, db)
        resultado = generar_prediagnostico(texto_seguro, [g.contenido for g in guias])

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