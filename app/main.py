import os
import uuid
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text, case
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import (
    Usuario, Sintoma, Documento, MetricaFisica, GuiaClinica,
    Prediagnostico, EjercicioRecomendado, EjecucionEjercicio,
)
from schemas import (
    RegistroPaciente, UsuarioCreateAdmin,
    UsuarioUpdateAdmin, UsuarioResponse, 
    UsuarioLogin, Rol, Token, SintomaCreate, 
    SintomaResponse, DocumentoResponse,
    MetricaCreate, MetricaResponse,
    GuiaClinicaCreate, GuiaClinicaResponse,
    PacienteTriage, ResumenPaciente, MetricaResumen,
    RevisarRequest, RevisarResponse,
    EjercicioCreate, EjercicioResponse,
    EjecucionCreate, EjecucionResponse,
)
from auth import hash_password, verify_password, create_token
from deps import get_current_user, require_role
from embeddings import generar_embedding, buscar_guias_relevantes
from anonimizar import anonimizar_texto
from llm import generar_prediagnostico
from constantes import ARTICULACIONES_VALIDAS

app = FastAPI()

# --- CORS: origenes permitidos para la web, configurables en el .env ---
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

# --- Archivos estaticos publicos (solo imagenes de ejercicios) ---
os.makedirs("static/ejercicios", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Constantes ---
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png"}
EXTENSIONES_PERMITIDAS = {".pdf", ".jpg", ".jpeg", ".png"}
TAMANO_MAXIMO_MB = 10

orden_urgencia = case(
    (Prediagnostico.urgencia_sugerida == "alta", 1),
    (Prediagnostico.urgencia_sugerida == "media", 2),
    (Prediagnostico.urgencia_sugerida == "baja", 3),
    else_=4
)

def crear_usuario(db: Session, nombre: str, email: str, password: str, rol: str) -> Usuario:
    usuario = Usuario(
        nombre=nombre,
        email=email,
        password_hash=hash_password(password),
        rol=rol,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ese email ya está registrado")
    db.refresh(usuario)
    return usuario

@app.post("/auth/registro", response_model=Token)
def registro(datos: RegistroPaciente, db: Session = Depends(get_db)):
    # El registro publico siempre crea pacientes.
    # Medicos y admins los crea un admin con POST /admin/usuarios.
    usuario = crear_usuario(db, datos.nombre, datos.email, datos.password, rol="paciente")
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


@app.get("/perfil")
def leer_mi_perfil(usuario_actual: Usuario = Depends(get_current_user)):
    return {"id": usuario_actual.id, "nombre": usuario_actual.nombre, "rol": usuario_actual.rol}


@app.get("/medico/dashboard")
def dashboard_medico(usuario_actual: Usuario = Depends(require_role("medico"))):
    return {"mensaje": f"Bienvenido doctor(a) {usuario_actual.nombre}"}


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
    usuario_actual: Usuario = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    return crear_usuario(db, datos.nombre, datos.email, datos.password, datos.rol)


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
    usuario_actual: Usuario = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)

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
    return usuario


@app.post("/sintomas", response_model=SintomaResponse)
def crear_sintoma(
    datos: SintomaCreate,
    usuario_actual: Usuario = Depends(require_role("paciente")),
    db: Session = Depends(get_db)
):
    nuevo = Sintoma(usuario_id=usuario_actual.id, descripcion=datos.descripcion)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    texto_seguro = anonimizar_texto(datos.descripcion)
    guias = buscar_guias_relevantes(texto_seguro, db)
    textos_guias = [g.contenido for g in guias]

    resultado = generar_prediagnostico(texto_seguro, textos_guias)

    nuevo_prediagnostico = Prediagnostico(
        usuario_id=usuario_actual.id,
        resumen_generado=resultado["resumen"],
        urgencia_sugerida=resultado["urgencia_sugerida"],
        diagnosticos_diferenciales=resultado["diagnosticos_diferenciales"],
    )
    db.add(nuevo_prediagnostico)
    db.commit()

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

    nombre_unico = f"{uuid.uuid4()}{extension}"
    ruta = f"uploads/{nombre_unico}"
    with open(ruta, "wb") as f:
        f.write(contenido)

    nuevo_doc = Documento(
        usuario_id=usuario_actual.id,
        nombre_archivo=archivo.filename,
        ruta_archivo=ruta,
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
    return nueva_guia


@app.get("/pacientes/triage", response_model=list[PacienteTriage])
def listar_triage(
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

    return prediagnostico


@app.post("/ejercicios", response_model=EjercicioResponse)
def crear_ejercicio(
    datos: EjercicioCreate,
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
    return nuevo


@app.post("/ejercicios/{id}/imagen", response_model=EjercicioResponse)
def subir_imagen_ejercicio(
    id: int,
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

    if ejercicio.imagen_url:
        ruta_anterior = ejercicio.imagen_url.lstrip("/")
        if os.path.exists(ruta_anterior):
            os.remove(ruta_anterior)

    nombre_unico = f"{uuid.uuid4()}{extension}"
    with open(f"static/ejercicios/{nombre_unico}", "wb") as f:
        f.write(contenido)

    ejercicio.imagen_url = f"/static/ejercicios/{nombre_unico}"
    db.commit()
    db.refresh(ejercicio)
    return ejercicio


@app.get("/ejercicios", response_model=list[EjercicioResponse])
def listar_ejercicios(
    articulacion: Optional[str] = Query(None),
    usuario_actual: Usuario = Depends(require_role("paciente", "admin")),
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