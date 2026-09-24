import re

def anonimizar_texto(texto: str) -> str:
    
    texto = re.sub(r"\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]", "[RUT]", texto)
    texto = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]", texto)
    texto = re.sub(r"\+?56?\s?9\s?\d{4}\s?\d{4}", "[TELEFONO]", texto)
    return texto