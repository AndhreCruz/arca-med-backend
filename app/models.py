from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy import Numeric
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class Sintoma(Base):
    __tablename__ = "sintomas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    descripcion = Column(Text, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class Documento(Base):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    tipo_archivo = Column(String(50))
    subido_en = Column(DateTime(timezone=True), server_default=func.now())


class MetricaFisica(Base):
    __tablename__ = "metricas_fisicas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    articulacion = Column(String(50), nullable=False)
    angulo_maximo = Column(Numeric(5, 2))
    angulo_minimo = Column(Numeric(5, 2))
    medido_en = Column(DateTime(timezone=True), server_default=func.now())