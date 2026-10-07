from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Literal, Optional
from constantes import ARTICULACIONES_VALIDAS, ARTICULACIONES_SIN_LADO, LADOS_VALIDOS

Rol = Literal["paciente", "medico", "admin"]

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


class DocumentoResponse(BaseModel):
    id: int
    nombre_archivo: str
    ruta_archivo: str

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