from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_embedding(texto: str) -> list[float]:
    respuesta = client.embeddings.create(
        model="text-embedding-3-small",
        input=texto
    )
    return respuesta.data[0].embedding