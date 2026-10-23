import hashlib
import json
from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from models import AuditoriaLog, Usuario

HASH_INICIAL = "0" * 64      # "hash anterior" del primer registro
LLAVE_BLOQUEO = 727001       # número arbitrario que identifica el candado de la auditoría


def _formatear_fecha(fecha: datetime) -> str:
    return fecha.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def calcular_hash(hash_anterior, usuario_id, rol, accion,
                  usuario_afectado_id, detalle, ip, fecha) -> str:
    partes = [
        hash_anterior,
        usuario_id,
        rol,
        accion,
        usuario_afectado_id,
        detalle,
        ip,
        _formatear_fecha(fecha),
    ]
    contenido = json.dumps(partes, ensure_ascii=False)
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()


def registrar_auditoria(db: Session, usuario: Usuario, accion: str,
                        request: Request | None = None,
                        usuario_afectado_id: int | None = None,
                        detalle: str | None = None) -> None:
    db.execute(text("SELECT pg_advisory_xact_lock(:llave)"), {"llave": LLAVE_BLOQUEO})

    ultimo = db.query(AuditoriaLog.hash).order_by(AuditoriaLog.id.desc()).first()
    hash_anterior = ultimo[0] if ultimo else HASH_INICIAL

    fecha = datetime.now(timezone.utc)
    ip = request.client.host if request and request.client else None

    log = AuditoriaLog(
        usuario_id=usuario.id,
        rol=usuario.rol,
        accion=accion,
        usuario_afectado_id=usuario_afectado_id,
        detalle=detalle,
        ip=ip,
        fecha=fecha,
        hash_anterior=hash_anterior,
    )
    log.hash = calcular_hash(hash_anterior, usuario.id, usuario.rol, accion,
                             usuario_afectado_id, detalle, ip, fecha)
    db.add(log)
    db.commit()


def verificar_cadena(db: Session) -> dict:
    hash_esperado = HASH_INICIAL
    total = 0

    for log in db.query(AuditoriaLog).order_by(AuditoriaLog.id).yield_per(500):
        total += 1

        if log.hash_anterior != hash_esperado:
            return {"integra": False, "total_revisados": total, "id_con_error": log.id,
                    "motivo": "La cadena está rota: se alteró o eliminó un registro anterior"}

        recalculado = calcular_hash(log.hash_anterior, log.usuario_id, log.rol, log.accion,
                                    log.usuario_afectado_id, log.detalle, log.ip, log.fecha)
        if recalculado != log.hash:
            return {"integra": False, "total_revisados": total, "id_con_error": log.id,
                    "motivo": "El contenido de este registro fue modificado"}

        hash_esperado = log.hash

    return {"integra": True, "total_revisados": total, "id_con_error": None, "motivo": None}