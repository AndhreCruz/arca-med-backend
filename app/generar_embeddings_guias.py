"""
Genera los embeddings de las guías clínicas que aún no tienen uno.

Las guías se cargan con init/03_guias_clinicas.sql con embedding = NULL,
porque un archivo SQL no puede llamar a la API de OpenAI. Este script
completa ese paso.

Uso (desde la carpeta app/, con el venv activo y el .env configurado):
    python generar_embeddings_guias.py

Es seguro correrlo varias veces: solo procesa las guías sin embedding.
"""
from dotenv import load_dotenv

load_dotenv()  # antes de importar embeddings, que lee OPENAI_API_KEY al cargarse

from database import SessionLocal
from models import GuiaClinica
from embeddings import generar_embedding


def main():
    db = SessionLocal()
    try:
        pendientes = db.query(GuiaClinica).filter(GuiaClinica.embedding.is_(None)).all()

        if not pendientes:
            print("Todas las guías ya tienen embedding. Nada que hacer.")
            return

        print(f"Generando embeddings para {len(pendientes)} guías...")
        for guia in pendientes:
            # Mismo criterio que POST /guias-clinicas: el embedding sale del contenido
            guia.embedding = generar_embedding(guia.contenido)
            db.commit()  # se guarda de a una: si algo falla a la mitad, lo hecho no se pierde
            print(f"  ok - {guia.titulo}")

        print("Listo.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
