from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional
from constantes import ARTICULACIONES_VALIDAS, ARTICULACIONES_SIN_LADO, LADOS_VALIDOS

class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: str

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

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