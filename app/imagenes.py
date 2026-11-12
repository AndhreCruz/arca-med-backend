"""Procesamiento de imágenes subidas por los usuarios."""
from io import BytesIO

from PIL import Image, ImageOps

TAMANO_FOTO_PERFIL = 512  # px, la foto queda cuadrada de 512 x 512


def procesar_foto_perfil(contenido: bytes) -> bytes:
    imagen = Image.open(BytesIO(contenido))
    imagen = ImageOps.exif_transpose(imagen)   # respeta la orientación con que se tomó en el celular
    imagen = imagen.convert("RGB")             # PNG con transparencia u otros formatos -> RGB para JPG
    imagen = ImageOps.fit(imagen, (TAMANO_FOTO_PERFIL, TAMANO_FOTO_PERFIL))  # recorta al centro, cuadrada

    salida = BytesIO()
    imagen.save(salida, format="JPEG", quality=85)
    return salida.getvalue()