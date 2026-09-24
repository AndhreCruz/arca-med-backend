import os
import uuid
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from database import get_db
from models import Usuario, Sintoma, Documento, MetricaFisica, GuiaClinica
from schemas import UsuarioCreate, UsuarioLogin, Token, SintomaCreate, SintomaResponse, DocumentoResponse, MetricaCreate, MetricaResponse, GuiaClinicaCreate, GuiaClinicaResponse
from auth import hash_password, verify_password, create_token
from deps import get_current_user, require_role
from embeddings import generar_embedding

app = FastAPI()

EXTENSIONES_PERMITIDAS = {".pdf", ".jpg", ".jpeg", ".png"}
TAMANO_MAXIMO_MB = 10


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "conectado a la base de datos"}


@app.post("/auth/register", response_model=Token)
def register(datos: UsuarioCreate, db: Session = Depends(get_db)):
    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        email=datos.email,
        password_hash=hash_password(datos.password),
        rol=datos.rol,
    )
    db.add(nuevo_usuario)
    try:
        db.commit()
        db.refresh(nuevo_usuario)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ese email ya está registrado")

    token = create_token(nuevo_usuario.id, nuevo_usuario.rol)
    return {"access_token": token, "rol": nuevo_usuario.rol}


@app.post("/auth/login", response_model=Token)
def login(datos: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario or not verify_password(datos.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    token = create_token(usuario.id, usuario.rol)
    return {"access_token": token, "rol": usuario.rol}


@app.get("/me")
def leer_mi_perfil(usuario_actual: Usuario = Depends(get_current_user)):
    return {"id": usuario_actual.id, "nombre": usuario_actual.nombre, "rol": usuario_actual.rol}


@app.get("/medico/dashboard")
def dashboard_medico(usuario_actual: Usuario = Depends(require_role("medico"))):
    return {"mensaje": f"Bienvenido doctor(a) {usuario_actual.nombre}"}


@app.get("/admin/usuarios")
def listar_usuarios(usuario_actual: Usuario = Depends(require_role("admin")), db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).all()
    return [{"id": u.id, "nombre": u.nombre, "email": u.email, "rol": u.rol} for u in usuarios]


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