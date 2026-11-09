from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict
from typing import Literal, Optional
from datetime import datetime
from constantes import ARTICULACIONES_VALIDAS, ARTICULACIONES_SIN_LADO, LADOS_VALIDOS

Rol = Literal["paciente", "medico", "admin"]

EstadoCita = Literal["programada", "completada", "cancelada"]

MENSAJE_ZONA_HORARIA = "debe incluir zona horaria, ej: 2026-11-10T10:00:00-03:00"

def validar_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("La contraseña es demasiado larga")
    return password


class RegistroPaciente(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v):
        return v.lower()

    @field_validator("password")
    @classmethod
    def revisar_password(cls, v):
        return validar_password(v)


class UsuarioCreateAdmin(RegistroPaciente):
    rol: Rol

class UsuarioUpdateAdmin(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    rol: Optional[Rol] = None
    activo: Optional[bool] = None

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v):
        return v.lower() if v is not None else v

    @field_validator("password")
    @classmethod
    def revisar_password(cls, v):
        return validar_password(v) if v is not None else v


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v):
        return v.lower()


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    activo: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    rol: str


class SintomaCreate(BaseModel):
    descripcion: str


class SintomaResponse(BaseModel):
    id: int
    descripcion: str

    class Config:
        from_attributes = True


class SintomaDetalle(BaseModel):
    id: int
    descripcion: str
    creado_en: datetime

    class Config:
        from_attributes = True


class GuiaClinicaDetalle(BaseModel):
    id: int
    titulo: str
    contenido: str
    creado_en: datetime

    class Config:
        from_attributes = True


class DocumentoDetalle(BaseModel):
    id: int
    nombre_archivo: str
    tipo_archivo: Optional[str] = None
    subido_en: datetime

    class Config:
        from_attributes = True


class DocumentoResponse(BaseModel):
    id: int
    nombre_archivo: str
    tipo_archivo: Optional[str] = None
    subido_en: datetime

    class Config:
        from_attributes = True


class MetricaCreate(BaseModel):
    articulacion: str
    lado: Optional[str] = None
    angulo_maximo: float
    angulo_minimo: float

    @model_validator(mode="after")
    def validar_datos(self):
        if self.articulacion not in ARTICULACIONES_VALIDAS:
            raise ValueError(f"Articulacion invalida. Opciones: {ARTICULACIONES_VALIDAS}")

        if self.articulacion in ARTICULACIONES_SIN_LADO:
            if self.lado is not None:
                raise ValueError(f"'{self.articulacion}' no lleva lado")
        else:
            if self.lado not in LADOS_VALIDOS:
                raise ValueError(f"Debes indicar el lado: {LADOS_VALIDOS}")

        if self.angulo_minimo > self.angulo_maximo:
            raise ValueError("angulo_minimo no puede ser mayor que angulo_maximo")
        return self


class MetricaResponse(BaseModel):
    id: int
    articulacion: str
    lado: Optional[str] = None
    angulo_maximo: float
    angulo_minimo: float

    class Config:
        from_attributes = True


class MetricaResumen(BaseModel):
    articulacion: str
    lado: Optional[str] = None
    angulo_maximo: float
    angulo_minimo: float


class GuiaClinicaCreate(BaseModel):
    titulo: str
    contenido: str


class GuiaClinicaResponse(BaseModel):
    id: int
    titulo: str

    class Config:
        from_attributes = True


class PacienteTriage(BaseModel):
    usuario_id: int
    nombre: str
    urgencia_sugerida: str


class MetricaResumen(BaseModel):
    articulacion: str
    angulo_maximo: float
    angulo_minimo: float


class ResumenPaciente(BaseModel):
    resumen_generado: str
    diagnosticos_diferenciales: list
    urgencia_sugerida: str
    metricas_fisicas: list[MetricaResumen]


class RevisarRequest(BaseModel):
    revisado_por_medico: bool


class RevisarResponse(BaseModel):
    id: int
    revisado_por_medico: bool


class EjercicioCreate(BaseModel):
    nombre_ejercicio: str
    descripcion: Optional[str] = None
    articulacion: str

    @field_validator("articulacion")
    @classmethod
    def validar_articulacion(cls, v):
        if v not in ARTICULACIONES_VALIDAS:
            raise ValueError(f"Articulacion invalida. Opciones: {ARTICULACIONES_VALIDAS}")
        return v


class EjercicioResponse(BaseModel):
    id: int
    nombre_ejercicio: str
    descripcion: Optional[str] = None
    articulacion: str
    imagen_url: Optional[str] = None

    class Config:
        from_attributes = True


class EjecucionCreate(BaseModel):
    correcto: bool
    comentario: Optional[str] = None


class EjecucionResponse(BaseModel):
    id: int
    ejercicio_id: int
    correcto: bool
    comentario: Optional[str] = None

    class Config:
        from_attributes = True


class AuditoriaLogResponse(BaseModel):
    id: int
    usuario_id: int | None
    rol: str
    accion: str
    usuario_afectado_id: int | None
    detalle: str | None
    ip: str | None
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificacionAuditoriaResponse(BaseModel):
    integra: bool
    total_revisados: int
    id_con_error: int | None
    motivo: str | None

    
class PacienteListado(BaseModel):
    id: int
    nombre: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class CitaCreate(BaseModel):
    paciente_id: int
    medico_id: int
    fecha_hora: datetime
    duracion_minutos: int = Field(30, ge=10, le=180)
    motivo: Optional[str] = Field(None, max_length=500)

    @field_validator("fecha_hora")
    @classmethod
    def validar_zona_horaria(cls, valor):
        if valor.tzinfo is None:
            raise ValueError(f"fecha_hora {MENSAJE_ZONA_HORARIA}")
        return valor


class CitaUpdate(BaseModel):
    fecha_hora: Optional[datetime] = None
    duracion_minutos: Optional[int] = Field(None, ge=10, le=180)
    motivo: Optional[str] = Field(None, max_length=500)
    estado: Optional[EstadoCita] = None

    @field_validator("fecha_hora")
    @classmethod
    def validar_zona_horaria(cls, valor):
        if valor is not None and valor.tzinfo is None:
            raise ValueError(f"fecha_hora {MENSAJE_ZONA_HORARIA}")
        return valor


class CitaResponse(BaseModel):
    id: int
    paciente_id: int
    paciente_nombre: str
    medico_id: int
    medico_nombre: str
    fecha_hora: datetime
    duracion_minutos: int
    motivo: Optional[str]
    estado: str

    model_config = ConfigDict(from_attributes=True)