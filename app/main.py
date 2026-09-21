from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from database import get_db
from models import Usuario
from schemas import UsuarioCreate, UsuarioLogin, Token
from auth import hash_password, verify_password, create_token

app = FastAPI()

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