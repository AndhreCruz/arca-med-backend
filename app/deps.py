from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario
from auth import SECRET_KEY, ALGORITHM

security_scheme = HTTPBearer()

def get_current_user(
    credenciales: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    token = credenciales.credentials
    credenciales_invalidas = HTTPException(status_code=401, detail="Token inválido o expirado")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = payload.get("sub")
        if usuario_id is None:
            raise credenciales_invalidas
    except JWTError:
        raise credenciales_invalidas

    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()
    if usuario is None:
        raise credenciales_invalidas
    return usuario


def require_role(*roles_permitidos: str):
    def verificador(usuario_actual: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario_actual.rol not in roles_permitidos:
            raise HTTPException(status_code=403, detail="No tienes permiso para acceder a esto")
        return usuario_actual
    return verificador