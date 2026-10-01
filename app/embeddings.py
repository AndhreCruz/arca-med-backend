from openai import OpenAI
from models import GuiaClinica
from sqlalchemy.orm import Session
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_embedding(texto: str) -> list[float]:
    respuesta = client.embeddings.create(
        model="text-embedding-3-small",
        input=texto
    )
    return respuesta.data[0].embedding


def buscar_guias_relevantes(texto: str, db: Session, top_k: int = 3) -> list[GuiaClinica]:
    vector_consulta = generar_embedding(texto)
    return (
        db.query(GuiaClinica)
        .order_by(GuiaClinica.embedding.cosine_distance(vector_consulta))
        .limit(top_k)
        .all()
    )