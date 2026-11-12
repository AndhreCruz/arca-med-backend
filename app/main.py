import os
import uuid
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from urllib.parse import quote
from sqlalchemy.orm import Session
from sqlalchemy import text, case
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import (
    Usuario, Sintoma, Documento, MetricaFisica, GuiaClinica,
    Prediagnostico, EjercicioRecomendado, EjecucionEjercicio,
    AuditoriaLog, Cita
)
from schemas import (
    RegistroPaciente, UsuarioCreateAdmin,
    UsuarioUpdateAdmin, UsuarioResponse, 
    UsuarioLogin, Rol, Token, SintomaCreate, 
    SintomaResponse, DocumentoResponse,
    SintomaDetalle, DocumentoDetalle,
    MetricaCreate, MetricaResponse,
    GuiaClinicaCreate, GuiaClinicaResponse, GuiaClinicaDetalle,
    PacienteTriage, ResumenPaciente, MetricaResumen,
    RevisarRequest, RevisarResponse,
    EjercicioCreate, EjercicioResponse,
    EjecucionCreate, EjecucionResponse,
    AuditoriaLogResponse, VerificacionAuditoriaResponse,
    PacienteListado, CitaCreate, CitaUpdate, CitaResponse, EstadoCita,
    PerfilUpdate, PerfilResponse
)
from auth import hash_password, verify_password, create_token
from deps import get_current_user, require_role
from embeddings import generar_embedding, buscar_guias_relevantes
from anonimizar import anonimizar_texto
from llm import generar_prediagnostico
from pipeline import generar_prediagnostico_en_segundo_plano
from auditoria import registrar_auditoria, verificar_cadena
from datetime import datetime, timedelta, timezone
from constantes import ARTICULACIONES_VALIDAS

app = FastAPI()

ORIGENES_POR_DEFECTO = "http://localhost:5173,http://127.0.0.1:5173"

origenes_permitidos = [
    origen.strip()
    for origen in os.getenv("CORS_ORIGINS", ORIGENES_POR_DEFECTO).split(",")
    if origen.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Constantes ---
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png"}
EXTENSIONES_PERMITIDAS = {".pdf", ".jpg", ".jpeg", ".png"}
TIPOS_IMAGEN = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
TAMANO_MAXIMO_MB = 10

orden_urgencia = case(
    (Prediagnostico.urgencia_sugerida == "alta", 1),
    (Prediagnostico.urgencia_sugerida == "media", 2),
    (Prediagnostico.urgencia_sugerida == "baja", 3),
    else_=4
)

DURACION_MAXIMA_CITA = 180  # minutos, igual que el CHECK de la tabla


def obtener_medico_o_404(db: Session, medico_id: int) -> Usuario:
    medico = (
        db.query(Usuario)
        .filter(Usuario.id == medico_id, Usuario.rol == "medico", Usuario.activo == True)
        .first()
    )
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return medico


def exigir_zona_horaria(valor: Optional[datetime], campo: str) -> None:
    if valor is not None and valor.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail=f"{campo} debe incluir zona horaria, ej: 2026-11-10T10:00:00-03:00",
        )


def validar_horario_cita(db: Session, medico_id: int, fecha_hora: datetime,
                         duracion_minutos: int, excluir_id: Optional[int] = None) -> None:
    if fecha_hora <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="La cita debe ser en una fecha futura")

    fin = fecha_hora + timedelta(minutes=duracion_minutos)

    # Citas del médico que podrían cruzarse: empiezan antes de que termine la nueva
    # y no tan atrás como para haber terminado antes de que la nueva empiece.
    candidatas = db.query(Cita).filter(
        Cita.medico_id == medico_id,
        Cita.estado == "programada",
        Cita.fecha_hora < fin,
        Cita.fecha_hora > fecha_hora - timedelta(minutes=DURACION_MAXIMA_CITA),
    )
    if excluir_id is not None:
        candidatas = candidatas.filter(Cita.id != excluir_id)

    for cita in candidatas:
        if cita.fecha_hora + timedelta(minutes=cita.duracion_minutos) > fecha_hora:
            raise HTTPException(status_code=409, detail="El médico ya tiene una cita en ese horario")


def crear_usuario(db: Session, nombre: str, email: str, password: str, rol: str, **datos_extra) -> Usuario:
    usuario = Usuario(
        nombre=nombre,
        email=email,
        password_hash=hash_password(password),
        rol=rol,
        **datos_extra,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ese email ya está registrado")
    db.refresh(usuario)
    return usuario


def obtener_paciente_o_404(db: Session, paciente_id: int) -> Usuario:
    paciente = (
        db.query(Usuario)
        .filter(Usuario.id == paciente_id, Usuario.rol == "paciente")
        .first()
    )
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente


@app.post("/auth/registro", response_model=Token)
def registro(datos: RegistroPaciente, db: Session = Depends(get_db)):
    # El registro publico siempre crea pacientes.
    # Medicos y admins los crea un admin con POST /admin/usuarios.
    extra = datos.model_dump(include={"fecha_nacimiento", "sexo", "telefono"}, exclude_none=True)
    usuario = crear_usuario(db, datos.nombre, datos.email, datos.password, rol="paciente", **extra)
    token = create_token(usuario.id, usuario.rol)
    return {"access_token": token, "rol": usuario.rol}


@app.post("/auth/inicio-sesion", response_model=Token)
def login(datos: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario or not verify_password(datos.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada. Contacta al administrador")

    token = create_token(usuario.id, usuario.rol)
    return {"access_token": token, "rol": usuario.rol}


@app.get("/perfil", response_model=PerfilResponse)
def leer_mi_perfil(usuario_actual: Usuario = Depends(get_current_user)):
    return usuario_actual


@app.patch("/perfil", response_model=PerfilResponse)
def editar_mi_perfil(
    datos: PerfilUpdate,
    usuario_actual: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cambios = datos.model_dump(exclude_unset=True)
    if cambios.get("nombre", "") is None:
        cambios.pop("nombre")  # el nombre no se puede borrar

    for campo, valor in cambios.items():
        setattr(usuario_actual, campo, valor)

    db.commit()
    db.refresh(usuario_actual)
    return usuario_actual


@app.get("/admin/usuarios", response_model=list[UsuarioResponse])
def listar_usuarios(
    rol: Optional[Rol] = Query(None),
    usuario_actual: Usuario = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    consulta = db.query(Usuario)
    if rol:
        consulta = consulta.filter(Usuario.rol == rol)
    return consulta.order_by(Usuario.id).all()


@app.post("/admin/usuarios", response_model=UsuarioResponse)
def crear_usuario_admin(
    datos: UsuarioCreateAdmin,
    request: Request,  
    usuario_actual: Usuario = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    nuevo = crear_usuario(db, datos.nombre, datos.email, datos.password, datos.rol)

    registrar_auditoria(db, usuario_actual, "crear_usuario", request,
                        usuario_afectado_id=nuevo.id, detalle=f"rol={nuevo.rol}")
    return nuevo


@app.get("/admin/usuarios/{id}", response_model=UsuarioResponse)
def ver_usuario(
    id: int,
    usuario_actual: Usuario = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@app.patch("/admin/usuarios/{id}", response_model=UsuarioResponse)
def editar_usuario(
    id: int,
    datos: UsuarioUpdateAdmin,
    request: Request,  
    usuario_actual: Usuario = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
    campos_cambiados = list(cambios.keys())  

    if usuario.id == usuario_actual.id and ("rol" in cambios or "activo" in cambios):
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol ni desactivar tu propia cuenta")

    if "password" in cambios:
        usuario.password_hash = hash_password(cambios.pop("password"))

    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ese email ya está registrado")

    db.refresh(usuario)

    registrar_auditoria(db, usuario_actual, "editar_usuario", request,
                        usuario_afectado_id=usuario.id,
                        detalle="campos: " + ", ".join(campos_cambiados))
    return usuario


@app.post("/sintomas", response_model=SintomaResponse)
def crear_sintoma(
    datos: SintomaCreate,
    background_tasks: BackgroundTasks,
    usuario_actual: Usuario = Depends(require_role("paciente")),
    db: Session = Depends(get_db)
):
    nuevo = Sintoma(usuario_id=usuario_actual.id, descripcion=datos.descripcion)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    background_tasks.add_task(
        generar_prediagnostico_en_segundo_plano,
        usuario_actual.id,
        datos.descripcion,
    )
    return nuevo


@app.post("/documentos", response_model=DocumentoResponse)
def subir_documento(
    archivo: UploadFile = File(...),
    usuario_actual: Usuario = Depends(require_role("paciente")),
    db: Session = Depends(get_db)
):
    extension = os.path.splitext(archivo.filename)[1].lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")

    contenido = archivo.file.read()
    if len(contenido) > TAMANO_MAXIMO_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"El archivo supera los {TAMANO_MAXIMO_MB}MB")

    nuevo_doc = Documento(
        usuario_id=usuario_actual.id,
        nombre_archivo=archivo.filename,
        contenido=contenido,
        tipo_archivo=archivo.content_type,
    )
    db.add(nuevo_doc)
    db.commit()
    db.refresh(nuevo_doc)
    return nuevo_doc


@app.post("/metricas", response_model=MetricaResponse)
def crear_metrica(
    datos: MetricaCreate,
    usuario_actual: Usuario = Depends(require_role("paciente")),
    db: Session = Depends(get_db)
):
    nueva = MetricaFisica(
        usuario_id=usuario_actual.id,
        articulacion=datos.articulacion,
        lado=datos.lado,
        angulo_maximo=datos.angulo_maximo,
        angulo_minimo=datos.angulo_minimo,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@app.post("/guias-clinicas", response_model=GuiaClinicaResponse)
def crear_guia_clinica(
    datos: GuiaClinicaCreate,
    request: Request,  
    usuario_actual: Usuario = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    vector = generar_embedding(datos.contenido)

    nueva_guia = GuiaClinica(
        titulo=datos.titulo,
        contenido=datos.contenido,
        embedding=vector,
    )
    db.add(nueva_guia)
    db.commit()
    db.refresh(nueva_guia)

    registrar_auditoria(db, usuario_actual, "crear_guia", request,
                        detalle=f"guia_id={nueva_guia.id}")
    return nueva_guia


@app.get("/guias-clinicas", response_model=list[GuiaClinicaDetalle])
def listar_guias_clinicas(
    usuario_actual: Usuario = Depends(require_role("admin", "medico")),
    db: Session = Depends(get_db)
):
    return db.query(GuiaClinica).order_by(GuiaClinica.titulo).all()


@app.get("/pacientes/triage", response_model=list[PacienteTriage])
def listar_triage(
    request: Request,  
    usuario_actual: Usuario = Depends(require_role("medico")),
    db: Session = Depends(get_db)
):
    resultados = (
        db.query(Prediagnostico, Usuario.nombre)
        .join(Usuario, Usuario.id == Prediagnostico.usuario_id)
        .filter(Prediagnostico.revisado_por_medico == False)
        .order_by(orden_urgencia)
        .all()
    )

    registrar_auditoria(db, usuario_actual, "ver_triage", request,
                        detalle=f"{len(resultados)} pacientes en bandeja")

    return [
        {
            "usuario_id": p.usuario_id,
            "nombre": nombre,
            "urgencia_sugerida": p.urgencia_sugerida
        }
        for p, nombre in resultados
    ]


@app.get("/pacientes/{id}/resumen", response_model=ResumenPaciente)
def ver_resumen_paciente(
    id: int,
    request: Request, 
    usuario_actual: Usuario = Depends(require_role("medico")),
    db: Session = Depends(get_db)
):
    prediagnostico = (
        db.query(Prediagnostico)
        .filter(Prediagnostico.usuario_id == id)
        .order_by(Prediagnostico.creado_en.desc())
        .first()
    )

    if not prediagnostico:
        raise HTTPException(
            status_code=404,
            detail="No hay prediagnostico para este paciente"
        )

    metricas = (
        db.query(MetricaFisica)
        .filter(MetricaFisica.usuario_id == id)
        .all()
    )

    registrar_auditoria(db, usuario_actual, "ver_resumen", request,
                        usuario_afectado_id=id)

    return {
        "resumen_generado": prediagnostico.resumen_generado,
        "diagnosticos_diferenciales": prediagnostico.diagnosticos_diferenciales,
        "urgencia_sugerida": prediagnostico.urgencia_sugerida,
        "metricas_fisicas": metricas,
    }


@app.post("/pacientes/{id}/resumen/revisar", response_model=RevisarResponse)
def revisar_resumen(
    id: int,
    datos: RevisarRequest,
    request: Request,  
    usuario_actual: Usuario = Depends(require_role("medico")),
    db: Session = Depends(get_db)
):
    prediagnostico = (
        db.query(Prediagnostico)
        .filter(Prediagnostico.usuario_id == id)
        .order_by(Prediagnostico.creado_en.desc())
        .first()
    )

    if not prediagnostico:
        raise HTTPException(
            status_code=404,
            detail="No hay prediagnostico para este paciente"
        )

    prediagnostico.revisado_por_medico = datos.revisado_por_medico

    db.commit()
    db.refresh(prediagnostico)

    registrar_auditoria(db, usuario_actual, "revisar_prediagnostico", request,
                        usuario_afectado_id=id,
                        detalle=f"revisado={datos.revisado_por_medico}")
    return prediagnostico


@app.get("/pacientes/{id}/sintomas", response_model=list[SintomaDetalle])
def ver_sintomas_paciente(
    id: int,
    request: Request, 
    usuario_actual: Usuario = Depends(require_role("medico")),
    db: Session = Depends(get_db)
):
    obtener_paciente_o_404(db, id)
    sintomas = (
        db.query(Sintoma)
        .filter(Sintoma.usuario_id == id)
        .order_by(Sintoma.creado_en.desc())
        .all()
    )

    registrar_auditoria(db, usuario_actual, "ver_sintomas", request,
                        usuario_afectado_id=id)
    return sintomas


@app.get("/pacientes/{id}/documentos", response_model=list[DocumentoDetalle])
def ver_documentos_paciente(
    id: int,
    request: Request,  
    usuario_actual: Usuario = Depends(require_role("medico")),
    db: Session = Depends(get_db)
):
    obtener_paciente_o_404(db, id)
    documentos = (
        db.query(Documento)
        .filter(Documento.usuario_id == id)
        .order_by(Documento.subido_en.desc())
        .all()
    )

    registrar_auditoria(db, usuario_actual, "ver_documentos", request,
                        usuario_afectado_id=id)
    return documentos


@app.get("/pacientes/{id}/documentos/{doc_id}/archivo")
def descargar_documento_paciente(
    id: int,
    doc_id: int,
    request: Request,  
    usuario_actual: Usuario = Depends(require_role("medico")),
    db: Session = Depends(get_db)
):
    obtener_paciente_o_404(db, id)
    documento = (
        db.query(Documento)
        .filter(Documento.id == doc_id, Documento.usuario_id == id)
        .first()
    )
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    registrar_auditoria(db, usuario_actual, "descargar_documento", request,
                        usuario_afectado_id=id, detalle=f"documento_id={doc_id}")

    return Response(
        content=documento.contenido,
        media_type=documento.tipo_archivo,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(documento.nombre_archivo)}"
        },
    )


@app.post("/ejercicios", response_model=EjercicioResponse)
def crear_ejercicio(
    datos: EjercicioCreate,
    request: Request, 
    usuario_actual: Usuario = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    nuevo = EjercicioRecomendado(
        nombre_ejercicio=datos.nombre_ejercicio,
        descripcion=datos.descripcion,
        articulacion=datos.articulacion,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    registrar_auditoria(db, usuario_actual, "crear_ejercicio", request,
                        detalle=f"ejercicio_id={nuevo.id}")
    return nuevo


@app.post("/ejercicios/{id}/imagen", response_model=EjercicioResponse)
def subir_imagen_ejercicio(
    id: int,
    request: Request,  
    archivo: UploadFile = File(...),
    usuario_actual: Usuario = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    ejercicio = db.query(EjercicioRecomendado).filter(EjercicioRecomendado.id == id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")

    extension = os.path.splitext(archivo.filename)[1].lower()
    if extension not in EXTENSIONES_IMAGEN:
        raise HTTPException(status_code=400, detail="Solo se permiten imagenes JPG o PNG")

    contenido = archivo.file.read()
    if len(contenido) > TAMANO_MAXIMO_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"La imagen supera los {TAMANO_MAXIMO_MB}MB")

    ejercicio.imagen = contenido
    ejercicio.imagen_tipo = TIPOS_IMAGEN[extension]
    # El ?v= cambia en cada subida para que navegador y app no muestren la imagen antigua de su caché
    ejercicio.imagen_url = f"/ejercicios/{ejercicio.id}/imagen?v={uuid.uuid4().hex[:8]}"
    db.commit()
    db.refresh(ejercicio)

    registrar_auditoria(db, usuario_actual, "subir_imagen_ejercicio", request,
                        detalle=f"ejercicio_id={id}")
    return ejercicio


@app.get("/ejercicios/{id}/imagen")
def ver_imagen_ejercicio(id: int, db: Session = Depends(get_db)):
    ejercicio = db.query(EjercicioRecomendado).filter(EjercicioRecomendado.id == id).first()
    if not ejercicio or ejercicio.imagen is None:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    return Response(
        content=ejercicio.imagen,
        media_type=ejercicio.imagen_tipo,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/ejercicios", response_model=list[EjercicioResponse])
def listar_ejercicios(
    articulacion: Optional[str] = Query(None),
    usuario_actual: Usuario = Depends(require_role("paciente", "medico", "admin")),
    db: Session = Depends(get_db)
):
    consulta = db.query(EjercicioRecomendado)
    if articulacion:
        if articulacion not in ARTICULACIONES_VALIDAS:
            raise HTTPException(status_code=400, detail=f"Articulacion invalida. Opciones: {ARTICULACIONES_VALIDAS}")
        consulta = consulta.filter(EjercicioRecomendado.articulacion == articulacion)
    return consulta.order_by(EjercicioRecomendado.nombre_ejercicio).all()


@app.post("/ejercicios/{id}/ejecucion", response_model=EjecucionResponse)
def registrar_ejecucion(
    id: int,
    datos: EjecucionCreate,
    usuario_actual: Usuario = Depends(require_role("paciente")),
    db: Session = Depends(get_db)
):
    ejercicio = db.query(EjercicioRecomendado).filter(EjercicioRecomendado.id == id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")

    ejecucion = EjecucionEjercicio(
        ejercicio_id=id,
        usuario_id=usuario_actual.id,
        correcto=datos.correcto,
        comentario=datos.comentario,
    )
    db.add(ejecucion)
    db.commit()
    db.refresh(ejecucion)
    return ejecucion


@app.get("/auditoria/logs", response_model=list[AuditoriaLogResponse])
def listar_auditoria(
    usuario_id: int | None = None,
    usuario_afectado_id: int | None = None,
    accion: str | None = None,
    limite: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(require_role("admin")),
):
    consulta = db.query(AuditoriaLog)
    if usuario_id is not None:
        consulta = consulta.filter(AuditoriaLog.usuario_id == usuario_id)
    if usuario_afectado_id is not None:
        consulta = consulta.filter(AuditoriaLog.usuario_afectado_id == usuario_afectado_id)
    if accion:
        consulta = consulta.filter(AuditoriaLog.accion == accion)
    return consulta.order_by(AuditoriaLog.id.desc()).limit(limite).all()


@app.get("/auditoria/verificar", response_model=VerificacionAuditoriaResponse)
def verificar_auditoria(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(require_role("admin")),
):
    return verificar_cadena(db)


@app.get("/pacientes", response_model=list[PacienteListado])
def listar_pacientes(
    request: Request,
    nombre: Optional[str] = Query(None),
    usuario_actual: Usuario = Depends(require_role("medico")),
    db: Session = Depends(get_db)
):
    consulta = db.query(Usuario).filter(Usuario.rol == "paciente", Usuario.activo == True)
    if nombre:
        consulta = consulta.filter(Usuario.nombre.ilike(f"%{nombre}%"))
    pacientes = consulta.order_by(Usuario.nombre).all()

    registrar_auditoria(db, usuario_actual, "ver_pacientes", request,
                        detalle=f"busqueda={nombre}" if nombre else None)
    return pacientes


# ---------- Citas ----------

@app.post("/citas", response_model=CitaResponse)
def crear_cita(
    datos: CitaCreate,
    request: Request,
    usuario_actual: Usuario = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    paciente = obtener_paciente_o_404(db, datos.paciente_id)
    if not paciente.activo:
        raise HTTPException(status_code=400, detail="El paciente está desactivado")
    obtener_medico_o_404(db, datos.medico_id)
    validar_horario_cita(db, datos.medico_id, datos.fecha_hora, datos.duracion_minutos)

    cita = Cita(**datos.model_dump())
    db.add(cita)
    db.commit()
    db.refresh(cita)

    registrar_auditoria(db, usuario_actual, "crear_cita", request,
                        usuario_afectado_id=cita.paciente_id, detalle=f"cita_id={cita.id}")
    return cita


@app.get("/citas", response_model=list[CitaResponse])
def listar_citas(
    request: Request,
    desde: Optional[datetime] = Query(None),
    hasta: Optional[datetime] = Query(None),
    medico_id: Optional[int] = Query(None),
    paciente_id: Optional[int] = Query(None),
    estado: Optional[EstadoCita] = Query(None),
    usuario_actual: Usuario = Depends(require_role("medico", "admin")),
    db: Session = Depends(get_db)
):
    exigir_zona_horaria(desde, "desde")
    exigir_zona_horaria(hasta, "hasta")

    consulta = db.query(Cita)
    if usuario_actual.rol == "medico":
        # El médico solo ve sus propias citas, aunque mande otro medico_id
        consulta = consulta.filter(Cita.medico_id == usuario_actual.id)
    elif medico_id is not None:
        consulta = consulta.filter(Cita.medico_id == medico_id)

    if paciente_id is not None:
        consulta = consulta.filter(Cita.paciente_id == paciente_id)
    if desde:
        consulta = consulta.filter(Cita.fecha_hora >= desde)
    if hasta:
        consulta = consulta.filter(Cita.fecha_hora < hasta)
    if estado:
        consulta = consulta.filter(Cita.estado == estado)

    citas = consulta.order_by(Cita.fecha_hora).all()

    if usuario_actual.rol == "medico":
        registrar_auditoria(db, usuario_actual, "ver_citas", request,
                            usuario_afectado_id=paciente_id)
    return citas


@app.get("/mis-citas", response_model=list[CitaResponse])
def listar_mis_citas(
    solo_proximas: bool = Query(True),
    usuario_actual: Usuario = Depends(require_role("paciente")),
    db: Session = Depends(get_db)
):
    consulta = db.query(Cita).filter(Cita.paciente_id == usuario_actual.id)
    if solo_proximas:
        consulta = consulta.filter(Cita.fecha_hora >= datetime.now(timezone.utc))
    return consulta.order_by(Cita.fecha_hora).all()


@app.patch("/citas/{id}", response_model=CitaResponse)
def editar_cita(
    id: int,
    datos: CitaUpdate,
    request: Request,
    usuario_actual: Usuario = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    cita = db.query(Cita).filter(Cita.id == id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
    if not cambios:
        raise HTTPException(status_code=400, detail="No se envió ningún cambio")

    if cita.estado != "programada":
        raise HTTPException(status_code=400,
                            detail=f"La cita ya está {cita.estado} y no se puede modificar")

    if "fecha_hora" in cambios or "duracion_minutos" in cambios:
        validar_horario_cita(
            db,
            cita.medico_id,
            cambios.get("fecha_hora", cita.fecha_hora),
            cambios.get("duracion_minutos", cita.duracion_minutos),
            excluir_id=cita.id,
        )

    campos_cambiados = list(cambios.keys())
    for campo, valor in cambios.items():
        setattr(cita, campo, valor)

    db.commit()
    db.refresh(cita)

    registrar_auditoria(db, usuario_actual, "editar_cita", request,
                        usuario_afectado_id=cita.paciente_id,
                        detalle=f"cita_id={cita.id}; campos: " + ", ".join(campos_cambiados))
    return cita