"""
Cifrado AES-256-GCM para los datos sensibles guardados en la base.

Los modelos usan TextoCifrado y BytesCifrados como tipo de columna:
SQLAlchemy cifra al guardar y descifra al leer, sin que los endpoints
tengan que hacer nada.
"""
import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.types import LargeBinary, TypeDecorator

TAMANO_NONCE = 12  # bytes, el tamaño recomendado para AES-GCM


def _cargar_clave() -> bytes:
    clave_b64 = os.getenv("ENCRYPTION_KEY")
    if not clave_b64:
        raise RuntimeError("Falta ENCRYPTION_KEY en el .env")
    clave = base64.b64decode(clave_b64)
    if len(clave) != 32:
        raise RuntimeError("ENCRYPTION_KEY debe ser de 32 bytes (AES-256), codificada en base64")
    return clave


_aesgcm = AESGCM(_cargar_clave())


def cifrar_bytes(datos: bytes) -> bytes:
    nonce = os.urandom(TAMANO_NONCE)
    return nonce + _aesgcm.encrypt(nonce, datos, None)


def descifrar_bytes(datos: bytes) -> bytes:
    nonce, cifrado = datos[:TAMANO_NONCE], datos[TAMANO_NONCE:]
    return _aesgcm.decrypt(nonce, cifrado, None)


class TextoCifrado(TypeDecorator):
    """Columna de texto que se guarda cifrada (BYTEA en Postgres)."""
    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, valor, dialect):
        if valor is None:
            return None
        return cifrar_bytes(valor.encode("utf-8"))

    def process_result_value(self, valor, dialect):
        if valor is None:
            return None
        return descifrar_bytes(valor).decode("utf-8")


class BytesCifrados(TypeDecorator):
    """Columna de bytes (archivos) que se guarda cifrada."""
    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, valor, dialect):
        if valor is None:
            return None
        return cifrar_bytes(valor)

    def process_result_value(self, valor, dialect):
        if valor is None:
            return None
        return descifrar_bytes(valor)