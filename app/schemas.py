from pydantic import BaseModel, EmailStr

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
    angulo_maximo: float
    angulo_minimo: float

class MetricaResponse(BaseModel):
    id: int
    articulacion: str
    angulo_maximo: float
    angulo_minimo: float

    class Config:
        from_attributes = True
        
        
class GuiaClinicaCreate(BaseModel):
    titulo: str
    contenido: str

class GuiaClinicaResponse(BaseModel):
    id: int
    titulo: str

    class Config:
        from_attributes = True